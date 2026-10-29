"""수집기 공통 도구.
- Http: 속도 제한·재시도. 응답 코드에 따라 NotFound / Blocked / SourceDown 예외를 구분해 던짐
- Run: 출처별 실행 기록. 시험 요청(canary), 실패율 감시, 시간 예산, 로그 파일, 요약 파일
- save: 이미 받아 둔 좋은 데이터를 빈 결과로 덮어쓰지 않음
- needs: 새 작품·방영 중 작품·오래된 데이터만 다시 받도록 판단"""
import json, os, sys, time, hashlib, unicodedata, re, traceback, datetime, urllib.request, urllib.error, urllib.parse

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(ROOT, '..', 'site')
RAW = os.path.join(ROOT, 'raw')
LOGS = os.path.join(ROOT, 'logs')
UA = 'dabwanni/1.0 (personal anime database; https://dabwanni.pages.dev)'      # 「collector」가 든 머리말은 애니메테마즈(Cloudflare)가 520으로 막음

class SourceError(Exception):
    """출처 자체의 문제(주소 변경, 차단, 서버 다운, 형식 변경). 개별 작품 문제와 구분."""
class NotFound(Exception): pass
class Blocked(SourceError): pass
class SourceDown(SourceError): pass
class SchemaError(SourceError): pass
class Abort(Exception): pass
QUICK = [False]   # 시험 요청 중에는 재시도를 줄여 빨리 판정
SKIP = object()   # work()가 이 값을 돌려주면 '최신이라 건너뜀'으로 집계

def now(): return datetime.datetime.now(datetime.timezone.utc)

def load_catalog():
    d = json.load(open(os.path.join(SITE, 'data', 'catalog.json'), encoding='utf-8'))
    F = d['fields']; ST = d.get('studios', [])
    out = []
    for r in d['rows']:
        w = dict(zip(F, r))
        w['_stu_names'] = [ST[i][0] if isinstance(ST[i], list) else ST[i] for i in w.get('stu') or []]
        w['_stu_names'] += [ST[i][1] for i in w.get('stu') or [] if isinstance(ST[i], list) and len(ST[i]) > 1 and ST[i][1]]   # 한국어 제작사 이름도 (라프텔 「와오월드」 같은 표기와 맞추려고)
        out.append(w)
    return out

def raw_path(src, k):
    p = os.path.join(RAW, src); os.makedirs(p, exist_ok=True)
    return os.path.join(p, re.sub(r'[^\w.-]', '_', str(k)) + '.json')
def have(src, k): return os.path.exists(raw_path(src, k))
def load(src, k):
    p = raw_path(src, k)
    if not os.path.exists(p): return None
    try: d = json.load(open(p, encoding='utf-8'))
    except Exception: return None
    if isinstance(d, dict): d.pop('_at', None)
    return d
def _empty(o): return o is None or o == {} or o == [] or (isinstance(o, dict) and not any(v for k, v in o.items() if not str(k).startswith('_')))
def save(src, k, obj):
    """빈 결과로 기존의 좋은 데이터를 덮어쓰지 않음. 받은 시각(_at)을 함께 기록."""
    p = raw_path(src, k)
    if _empty(obj) and os.path.exists(p):
        old = load(src, k)
        if not _empty(old):
            os.utime(p); return False
    if isinstance(obj, dict): obj = {**obj, '_at': now().isoformat()}
    elif obj is None: obj = {'_at': now().isoformat()}
    tmp = p + '.tmp'
    json.dump(obj, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False)
    os.replace(tmp, p); return True
def fetched_at(src, k):
    p = raw_path(src, k)
    if not os.path.exists(p): return None
    try:
        d = json.load(open(p, encoding='utf-8'))
        if isinstance(d, dict) and d.get('_at'): return datetime.datetime.fromisoformat(d['_at'])
    except Exception: pass
    return datetime.datetime.fromtimestamp(os.path.getmtime(p), datetime.timezone.utc)

def needs(src, w, fresh_days=None, airing_days=7):
    """다시 받을지 판단: 없음 → 받음. 방영 중·예정이거나 올해·작년 작품 → airing_days 지나면 다시.
    fresh_days를 주면 모든 작품을 그 주기로 다시(예: OTT)."""
    t = fetched_at(src, w['k'])
    if t is None: return True
    age = (now() - t).days
    if fresh_days is not None and age >= fresh_days: return True
    recent = w.get('st') in ('O', 'U') or (w.get('y') or 0) >= now().year - 1
    return recent and age >= airing_days

class Http:
    """최소 간격과 재시도. 404는 NotFound, 401/403은 Blocked, 그 밖의 반복 실패는 SourceDown."""
    def __init__(self, interval=1.0, run=None): self.interval, self.last, self.run = interval, 0, run
    def req(self, url, data=None, headers=None, tries=5):
        if QUICK[0]: tries = 2
        last_err = None
        for i in range(tries):
            wait = self.interval - (time.time() - self.last)
            if wait > 0: time.sleep(wait)
            self.last = time.time()
            h = {'User-Agent': UA, **(headers or {})}
            body = json.dumps(data).encode() if isinstance(data, dict) else data
            if isinstance(data, dict): h['Content-Type'] = 'application/json'
            try:
                with urllib.request.urlopen(urllib.request.Request(url, body, h), timeout=60) as r:
                    return r.read()
            except urllib.error.HTTPError as e:
                snippet = e.read()[:300].decode('utf-8', 'replace') if e.fp else ''
                if self.run: self.run.http_error(url, e.code, snippet)
                if e.code == 404: raise NotFound(url)
                if e.code in (401, 403): raise Blocked(f'{e.code} {url} {snippet[:120]}')
                last_err = f'{e.code} {snippet[:120]}'
                if e.code == 429 or e.code >= 500:
                    ra = e.headers.get('Retry-After')
                    # 429(요청 제한)는 길게 쉼: 쇼보이는 짧게 다시 두드리면 제한이 더 길어짐
                    base = 60 * (i + 1) if e.code == 429 else 10 * (i + 1)
                    time.sleep(min(int(ra) + 1 if ra and ra.isdigit() else base, 300)); continue
                raise SourceDown(f'{e.code} {url} {snippet[:120]}')
            except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
                last_err = repr(e)
                if self.run: self.run.http_error(url, None, last_err)
                time.sleep(min(5 * (i + 1), 30))
        raise SourceDown(f'{url} 반복 실패: {last_err}')
    def json(self, url, data=None, headers=None, tries=5):
        b = self.req(url, data, headers, tries)
        try: return json.loads(b)
        except Exception: raise SchemaError(f'JSON이 아닌 응답: {url} {b[:120]!r}')

class Run:
    """출처 하나의 실행 기록. logs/<출처>.log (사람용), logs/<출처>.jsonl (오류 상세), logs/summary/<출처>.json (요약)"""
    def __init__(self, src, budget_min=None, max_fail=0.2, max_empty=0.6, min_n=40):
        self.src, self.t0 = src, time.time()
        self.deadline = self.t0 + budget_min * 60 if budget_min else None
        self.max_fail, self.max_empty, self.min_n = max_fail, max_empty, min_n
        self.c = {'ok': 0, 'empty': 0, 'fail': 0, 'skip': 0}
        self.status, self.reason, self.examples = 'running', '', []
        os.makedirs(os.path.join(LOGS, 'summary'), exist_ok=True)
        self.log = open(os.path.join(LOGS, f'{src}.log'), 'a', encoding='utf-8')
        self.err = open(os.path.join(LOGS, f'{src}.jsonl'), 'a', encoding='utf-8')
        self.say(f'시작')
    def say(self, msg):
        line = f"{now().strftime('%Y-%m-%d %H:%M:%S')} [{self.src}] {msg}"
        print(line, flush=True); self.log.write(line + '\n'); self.log.flush()
    def http_error(self, url, code, snippet):
        self.err.write(json.dumps({'t': now().isoformat(), 'type': 'http', 'url': url, 'code': code, 'body': snippet[:300]}, ensure_ascii=False) + '\n'); self.err.flush()
    def canary(self, fn, what):
        """결과를 이미 아는 요청 하나로 출처가 살아 있는지 확인. 실패하면 Abort."""
        try:
            QUICK[0] = True
            try: ok = fn()
            finally: QUICK[0] = False
            if not ok: raise SchemaError(f'시험 요청의 응답에 기대한 항목이 없음 ({what})')
            self.say(f'시험 요청 통과: {what}')
        except Exception as e:
            self.fail_source(f'시험 요청 실패 ({what}): {e}'); raise Abort()
    def time_left(self): return self.deadline is None or time.time() < self.deadline
    def item(self, k, fn):
        """작품 하나 처리. fn()이 결과를 돌려주면 저장 여부에 따라 ok/empty 집계."""
        try:
            res = fn()
            if res is SKIP:
                self.c['skip'] += 1; return
            self.c['empty' if _empty(res) else 'ok'] += 1
        except NotFound:
            self.c['empty'] += 1
        except SourceError as e:
            self._record_fail(k, e); self.fail_source(f'출처 오류: {e}'); raise Abort()
        except Exception as e:
            self._record_fail(k, e)
        n = self.c['ok'] + self.c['empty'] + self.c['fail']
        if n >= self.min_n:
            if self.c['fail'] / n > self.max_fail:
                self.fail_source(f"실패율 {self.c['fail']}/{n}이 기준({int(self.max_fail * 100)}%)을 넘음"); raise Abort()
            if self.max_empty is not None and self.c['empty'] / n > self.max_empty and self.c['ok'] == 0:
                self.fail_source(f"빈 응답만 {self.c['empty']}건: 주소나 형식이 바뀌었을 가능성"); raise Abort()
        if n and n % 200 == 0: self.say(f"진행 {self.c}")
        if not self.time_left():
            self.status, self.reason = 'partial', '시간 예산 소진, 다음 실행에서 이어 받음'; raise Abort()
    def _record_fail(self, k, e):
        self.c['fail'] += 1
        rec = {'t': now().isoformat(), 'type': 'item', 'k': k, 'error': f'{type(e).__name__}: {e}', 'trace': traceback.format_exc()[-1500:]}
        self.err.write(json.dumps(rec, ensure_ascii=False) + '\n'); self.err.flush()
        if len(self.examples) < 5: self.examples.append(f'{k}: {type(e).__name__}: {str(e)[:160]}')
    def skip(self): self.c['skip'] += 1
    def fail_source(self, reason): self.status, self.reason = 'failed', reason; self.say('실패: ' + reason)
    def finish(self):
        if self.status == 'running':
            self.status = 'ok'
            if self.c['fail']: self.reason = f"개별 작품 {self.c['fail']}건 실패 (출처는 정상, 다음 실행에서 다시 시도)"
        s = {'source': self.src, 'status': self.status, 'reason': self.reason, 'counts': self.c, 'examples': self.examples,
             'minutes': round((time.time() - self.t0) / 60, 1), 'finished': now().isoformat()}
        json.dump(s, open(os.path.join(LOGS, 'summary', f'{self.src}.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        self.say(f"끝: {self.status} {self.c} {self.reason}")
        self.log.close(); self.err.close()
        return s

def run_source(src, items, work, canary=None, budget_min=None, **kw):
    """items의 각 작품에 work(w)를 실행. 중간에 Abort되어도 요약은 남기고, 실패면 종료 코드 2."""
    run = Run(src, budget_min, **kw)
    try:
        if canary: run.canary(*canary)
        for w in items:
            run.item(w['k'] if isinstance(w, dict) else w, lambda w=w: work(w, run))
    except Abort: pass
    except KeyboardInterrupt: run.status, run.reason = 'partial', '중단됨'
    s = run.finish()
    if s['status'] == 'failed': sys.exit(2)
    return s

def budget_arg(ap): ap.add_argument('--budget-min', type=float, default=None, help='이 시간(분)이 지나면 멈추고 다음 실행에서 이어 받음')

def pname(s):
    s = unicodedata.normalize('NFKC', s or '')
    s = re.sub(r'[\s・･=＝]', '', s)
    s = re.sub(r'[（(].*?[)）]', '', s)
    return s
def pid(name): return hashlib.sha1(pname(name).encode()).hexdigest()[:12]
