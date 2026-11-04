/* 다봤니 만화책: 알라딘 구매내역·장바구니를 북마클릿으로 가져와 시리즈별로 관리 (애니와 별개) */
const CM = store.get('comics', {v: 1, items: {}, series: {}, carts: []});
CM.items ||= {}; CM.series ||= {}; CM.carts ||= []; CM.unres ||= {}; CM.unresOff ||= {};      // unres: 알라딘에서 끝내 못 읽은 상품, unresOff: 목록에서 뺀 것
const CMS = {fmt: store.get('cmFmt', 'p'), kind: store.get('cmKind', 'all'), view: store.get('cmView', 'all'), sort: store.get('cmSort', 'name'), cart: 0, guide: false};
const ALADIN = ['https://www.aladin.co.kr', 'https://m.aladin.co.kr'];
const BUY_URL = 'https://www.aladin.co.kr/m/mbest.aspx?BestType=OrderSave';
const CART_URL = 'https://www.aladin.co.kr/m/mbasket.aspx?start=moheader';
function cmSave(){ SL_CACHE = null; store.set('comics', CM); if (typeof syncSoon === 'function') syncSoon(); }

/* ---------- 제목에서 시리즈 이름과 권수 읽기 ---------- */
const KN1 = {'하나': 1, '둘': 2, '셋': 3, '넷': 4, '다섯': 5, '여섯': 6, '일곱': 7, '여덟': 8, '아홉': 9};
const KN10 = {'열': 10, '스물': 20, '서른': 30, '마흔': 40, '쉰': 50, '예순': 60, '일흔': 70, '여든': 80, '아흔': 90};
function korNum(w){
  let m = w.match(/^(열|스물|서른|마흔|쉰|예순|일흔|여든|아흔)?(하나|둘|셋|넷|다섯|여섯|일곱|여덟|아홉)?$/);
  if (!m || (!m[1] && !m[2])) return null;
  return (m[1] ? KN10[m[1]] : 0) + (m[2] ? KN1[m[2]] : 0);
}
// 판 표시: 같은 권의 다른 판(그 권으로 침) / 번호 체계가 따로인 판(별도 시리즈)
const SAME_ED = /^(특별판|한정판|특장판|초판\s*한정판?|초회\s*한정판?|일반판|부록판|스페셜\s*에디션|리미티드\s*에디션|한정\s*특장판|특전판|세트|박스세트|합본판?|올컬러판|컬러판|풀컬러판?|초판본|체험판|특별체험판)$/;
const SEP_ED = /^(애장판|완전판|소장판|개정판|신장판|와이드판|무삭제판?)$/;
const PT_CACHE = new Map();
// 구매내역 전수 점검(6,451권)에서 나온 모양들을 반영한 제목 읽기
const ED_WORDS = /판|한정|특전|특장|세트|부록|포함|에디션|edition|박스|합본|증보|퍼즐|소책자|엽서|카드|달력|캘린더|스티커|아크릴|굿즈|커버|화집|노트|체험|ver\.|버전/i;
const QUAL = /\s*\((?:단행본|코믹|코믹스|만화|웹툰|만화판|코믹판)\)\s*$/;     // 「베아게르타(단행본)」, 「…(코믹)」 → 시리즈 이름에서 뗌
function parseTitle(t){
  if (PT_CACHE.has(t)) return PT_CACHE.get(t);
  let c = String(t || '').replace(/^\s*(\[[^\]]*\]\s*)+/, '').trim();   // [eBook] [고화질] [바닐라] 같은 앞 표시
  let ed = '', sep = '', vols = null, upDown = 0;
  // 「에로만화의 별 - 상」 「… (하)」 「… 상권」: 상·중·하 권
  let ud = c.match(/^(.*?\S)\s*(?:-\s*|\(\s*)?(상|중|하)(?:권)?\s*\)?(?:\s+-\s+.*)?$/);
  if (ud && !/\d\s*$/.test(ud[1])) { c = ud[1]; upDown = {'상': 1, '중': 2, '하': 2}[ud[2]]; }
  c = c.replace(/\s+-\s+.*$/, '').trim();                               // 「… 5 - 시프트코믹스」 뒤 부제·총서명
  const plus = c.split(/\s+\+\s+/);                                    // 「사카모토 데이즈 16 + 소설 …」 → 앞 책 기준
  if (plus.length > 1 && plus[0].trim()) { c = plus[0].trim(); ed = '세트'; }
  // 세트의 권수 표시: 「(전6권)」 「(총8권/완결)」 「전4권」 → 1~N권
  let tot = c.match(/\s*\(?\s*(?:전|총)\s*(\d{1,3})\s*권[^)]*\)?\s*$/);
  if (tot) { const n = +tot[1]; c = c.slice(0, tot.index).trim(); if (!/\d\s*[~∼～.·,\-]\s*\d+\s*(?:권|세트|합본)?\s*$/.test(c) && !/\s\d{1,3}$/.test(c)) { vols = []; for (let v = 1; v <= n && v <= 200; v++) vols.push(v); } ed = ed || '세트'; }
  // 닫히지 않은 끝 괄호(알라딘이 긴 제목을 잘라 보낸 경우)
  let um = c.match(/\s*\(([^()]*)$/);
  if (um) { if (ED_WORDS.test(um[1])) ed = ed || um[1].trim().replace(/\s.*$/, ''); c = c.slice(0, um.index).trim(); }
  c = c.replace(/\s*\(?완결\)?\s*$/, '').trim();                        // 「… 10 (완결)」
  // 권 번호 뒤 「 : 부제」 (「… 21 : ASAKURA DIYS」, 「Vol.1 : 집으로」)
  um = c.match(/^(.*\S)\s+((?:vol\.?\s*)?\d{1,3})\s*권?\s*[:：]\s+\S.*$/i);
  if (um) c = `${um[1]} ${um[2]}`;
  for (let guard = 0; guard < 8; guard++) {
    let m = c.match(/\s*\(([^()]*)\)\s*$/);                           // 끝의 괄호: (특장판) (올컬러판) (3 기간 한정 소책자) …
    if (m) {
      const w = m[1].trim();
      const nw = w.match(/^(\d{1,3})\s+(\S.*)$/);                       // 「(3 기간 한정 소책자)」: 괄호 안 앞 숫자가 권 번호
      if (nw && ED_WORDS.test(nw[2])) { ed = ed || nw[2]; c = `${c.slice(0, m.index).trim()} ${nw[1]}`; continue; }
      if (SEP_ED.test(w)) sep = w; else if (SAME_ED.test(w) || ED_WORDS.test(w)) ed = ed || w; else break;
      c = c.slice(0, m.index).trim(); continue;
    }
    // 권 번호 뒤에 붙은 판 설명 여러 낱말: 「2 직소퍼즐 한정판 박스세트」 「1~2 특별 합본판」 「3 한정판」
    m = c.match(/^(.*\S\s+(?:vol\.?\s*)?\d{1,3}(?:\s*[~∼～.·,]\s*\d{1,3})?\s*권?)\s+(\S.*)$/i);
    if (m && ED_WORDS.test(m[2]) && !/\d{2,}/.test(m[2])) { ed = ed || m[2].trim(); c = m[1].trim(); continue; }
    m = c.match(/\s(\S+)$/);                                           // 괄호 없는 끝 낱말: 「단다단 18 특별판」
    if (m && SAME_ED.test(m[1])) { ed = ed || m[1]; c = c.slice(0, m.index).trim(); continue; }
    if (m && SEP_ED.test(m[1]) && /\d\s*권?$/.test(c.slice(0, m.index))) { sep = m[1]; c = c.slice(0, m.index).trim(); continue; }
    break;
  }
  let vol = null, base = c;
  // 여러 권 묶음: 「1~3권」 「4~6」 「1.2 세트」 「1,2」 → 각 권
  const rg = c.match(/^(.*?\S)\s*(\d{1,3})\s*(?:[~∼～]|[.·,\-](?=\s*\d))\s*(\d{1,3})\s*권?$/);      // 「1~10」 「1-10」 「1.2」
  if (rg && +rg[2] < +rg[3] && +rg[3] - +rg[2] < 60) {
    vols = []; for (let v = +rg[2]; v <= +rg[3]; v++) vols.push(v);
    base = rg[1].trim(); vol = +rg[3];
  } else if (!vols) {
    let m = c.match(/^(.*?\S)\s*(?:Season|시즌|vol\.?|volume)\s*(\d{1,3})$/i) || c.match(/^(.*?)\s*(?:제\s*)?(\d{1,3})\s*권$/) || c.match(/^(.*?)[\s.(]\s*(\d{1,3})\s*\)?$/) || c.match(/^(.*\D)(\d{1,3})$/);
    if (m && m[1].trim()) { base = m[1].trim(); vol = +m[2]; }
    else { m = c.match(/^(.*\S)\s(\S+)$/); if (m && korNum(m[2])) { base = m[1]; vol = korNum(m[2]); } }
  } else vol = vols[vols.length - 1];
  if (!vol && upDown) { vol = upDown; }
  base = base.replace(QUAL, '').replace(/\s+vol\.?$/i, '').trim();
  if (sep && !base.includes(sep)) base = `${base} ${sep}`;
  const trial = /체험판/.test(ed);                                     // 체험판은 그 권을 산 것으로 치지 않음
  const r = {base: base || c || String(t || ''), vol: trial ? null : vol, vols: trial ? [] : (vols || (vol ? [vol] : [])), ed, trial};
  PT_CACHE.set(t, r); return r;
}
// 만화책이 아닌 상품(음반·영상)은 묶지 않음
const NOT_BOOK = /^\s*\[(?:음반|DVD|블루레이|Blu-?ray|LP|CD)\]/i;
const cleanTitle = t => parseTitle(t).base;
const volOf = t => parseTitle(t).vol;
const baseOf = t => parseTitle(t).base;
// 분류: 알라딘 장르를 저장해 둔 책은 여기서 계산 (만화 계열 장르가 하나라도 있으면 만화), 없으면 가져올 때 정한 값
function kindOf(it){
  if (Array.isArray(it.cats) && it.cats.length) {        // 알라딘 주제 분류 경로: 만화 쪽 경로가 하나라도 있으면 만화
    const isL = it.cats.some(p => /만화\/라이트노벨 > 라이트 노벨/.test(p)), isC = it.cats.some(p => /만화\/라이트노벨 > (?!라이트 노벨)/.test(p));
    if (isC || isL) return isC ? 'c' : 'l';
    if (!it.cats.some(p => /만화|라이트\s*노벨/.test(p))) return 'x';      // 알라딘 분류에 만화·라이트노벨이 하나도 없는 책(수학책 등)은 만화책 목록에서 뺌
  }
  if (it.g == null) return it.kind === 'l' ? 'l' : 'c';
  const g = it.g, isC = /만화|코믹|웹툰|그래픽\s*노블|BL|툰/.test(g), isL = /라이트\s*노벨|라노벨|라이트노벨/.test(g);
  return isC ? 'c' : isL ? 'l' : 'c';
}
const okDate = d => /^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$/.test(d || '');
const fmtOf = it => it.eb || /^\s*\[(?:전자책|eBook)\]/i.test(it.orig || it.t || '') ? 'e' : 'p';      // 종이책 p · 이북 e
const seriesKey = it => norm(baseOf(it.t)) + '|' + kindOf(it) + '|' + fmtOf(it);      // 만화판·라이트노벨판, 종이책·이북은 따로
// 빠진 권 표시: 이어지는 번호는 묶음 (1, 2, 3, 5 → 「1~3, 5」)
function ranges(a){ const out = []; for (let i = 0; i < a.length; i++) { let j = i; while (j + 1 < a.length && a[j + 1] === a[j] + 1) j++; out.push(j > i ? `${a[i]}~${a[j]}` : `${a[i]}`); i = j; } return out.join(', '); }

/* ---------- 시리즈 묶기 ---------- */
let SL_CACHE = null;
function seriesList(){
  if (SL_CACHE) return SL_CACHE;
  const S_ = new Map();
  // 알라딘 시리즈 번호(sid)가 있는 책은 그 번호로도 묶음: 제목이 달라도(「… Season 2」) 같은 시리즈. 제목 기준 묶음과 합침
  const own = Object.values(CM.items).filter(it => it.own && !NOT_BOOK.test(it.t || '') && kindOf(it) !== 'x'), par = new Map();
  const find = x => { while (par.get(x) !== x) { par.set(x, par.get(par.get(x))); x = par.get(x); } return x; };
  const add = x => { if (!par.has(x)) par.set(x, x); };
  // 한글만 같은 이름(「유루캠△」·「유루캠」, 「플라잉 위치(flying witch)」·「플라잉 위치」, 「뉴 게임(NEW GAME!)」·「뉴 게임! New Game!」)도 이어 붙임.
  // 단, 영문 부분이 서로 다르고 괄호 속 원제도 아니면(「일하는 세포 BLACK」, 「진격의 거인 LOST GIRLS」 같은 외전) 붙이지 않음
  const latinOut = b => b.replace(/\([^)]*\)/g, '').toLowerCase().replace(/[^a-z]/g, ''), latinAll = b => b.toLowerCase().replace(/[^a-z]/g, '');
  const hkey = it => { const b = baseOf(it.t), h = b.replace(/[^가-힣0-9]/g, ''); return h.length >= 3 ? 'h:' + h + '|' + kindOf(it) + '|' + fmtOf(it) : null; };
  const hLat = new Map();      // 한글 열쇠마다 처음 본 이름의 영문 부분
  for (const it of own) { const tk = seriesKey(it); add(tk); const h = hkey(it); if (h) {
      const b = baseOf(it.t), lo = latinOut(b), la = latinAll(b);
      if (!hLat.has(h)) hLat.set(h, []);
      const ok = hLat.get(h).find(([lo2, la2]) => lo === lo2 || la === la2 || (!lo && la && la === la2) || (!lo && !lo2) );
      hLat.get(h).push([lo, la, tk]);
      if (ok) { const a = find(tk), c2 = find(ok[2]); if (a !== c2) par.set(c2, a); }
    } if (it.sid) { const sk = 's:' + it.sid + '|' + kindOf(it) + '|' + fmtOf(it); add(sk); const a = find(tk), b = find(sk); if (a !== b) par.set(b, a); } }
  const cnt = new Map();     // 묶음마다 가장 많이 쓰인 제목 열쇠를 대표로 (읽은 권 등 저장 열쇠가 바뀌지 않게)
  for (const it of own) { const r = find(seriesKey(it)), m = cnt.get(r) || new Map(); m.set(seriesKey(it), (m.get(seriesKey(it)) || 0) + 1); cnt.set(r, m); }
  const rep = new Map([...cnt].map(([r, m]) => [r, [...m].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))[0][0]]));
  for (const it of own) {
    const k = rep.get(find(seriesKey(it))); let s = S_.get(k);
    if (!s) S_.set(k, s = {key: k, name: '', pub: it.pub || '', fmt: fmtOf(it), kind: kindOf(it), items: [], vols: new Set(), eb: false, date: '', buy: ''});
    const pt = parseTitle(it.t); it.vol = pt.vol; it.vols = pt.vols; it.ed = pt.ed;
    s.items.push(it); it.vols.forEach(v => s.vols.add(v)); if (it.eb) s.eb = true;
    if ((it.date || '') > s.date) s.date = it.date || ''; if ((it.buy || '') > s.buy) s.buy = it.buy || '';
    if (!s.name && seriesKey(it) === k) s.name = baseOf(it.t);
  }
  for (const s of S_.values()) {
    // 번호 없는 책 하나 + 2권부터 번호가 있는 시리즈: 단편으로 나왔다가 후속권이 나온 경우라 그 책을 1권으로 봄
    const nonum = s.items.filter(it => !it.vols.length);
    if (nonum.length && s.vols.size && !s.vols.has(1)) {
      const first = nonum.sort((a, b) => String(a.date).localeCompare(String(b.date)))[0];
      first.vol = 1; first.vols = [1]; s.vols.add(1);
    }
    s.items.sort((a, b) => (a.vol || 0) - (b.vol || 0) || String(a.date).localeCompare(String(b.date)));
    // 예전 열쇠(종류·형태 없음)로 저장한 읽은 권·다른 곳에서 산 권·경고 확인 옮김
    const old1 = s.key.replace(/\|[pe]$/, ''), old0 = old1.replace(/\|[cl]$/, '');
    if (!CM.series[s.key] && (CM.series[old1] || CM.series[old0])) CM.series[s.key] = {...(CM.series[old1] || CM.series[old0])};      // 예전 열쇠(종류 없음)로 저장한 읽은 권·다른 곳에서 산 권 옮김
    const ext = new Set((CM.series[s.key] || {}).ext || []); s.ext = [...ext].sort((a, b) => a - b);      // 다른 곳에서 산 권
    s.max = Math.max(0, ...s.vols, ...ext); s.gaps = [];
    for (let v = 1; v < s.max; v++) if (!s.vols.has(v) && !ext.has(v)) s.gaps.push(v);
    const last = s.items[s.items.length - 1]; s.cover = last.cover; s.pub = last.pub || s.pub;
    const st = CM.series[s.key] || {}; s.read = st.read || 0; s.ack = st.ack === s.gaps.join(',');
  }
  return (SL_CACHE = [...S_.values()]);
}

/* ---------- 화면 ---------- */
const BM_CODE = `javascript:(()=>{const s=document.createElement('script');s.src='${location.origin}/bm.js?v='+Date.now();document.body.appendChild(s)})()`;
function guideHTML(tab){
  const url = tab === 'ccart' ? CART_URL : BUY_URL;
  return `<div class="stbox cmguide"><button class="cmgh" data-cm="guide" aria-expanded="${CMS.guide}"><b>${t(tab === 'ccart' ? '알라딘 장바구니 백업하기' : '알라딘 구매내역 가져오기')}</b><span class="car">${CMS.guide ? '▴' : '▾'}</span></button>
    <div ${CMS.guide ? '' : 'hidden'}><ol class="cmsteps">
      <li>${t('아래 「다봤니 북마크」를 북마크로 저장합니다. 사파리에서는 아무 페이지나 북마크한 뒤, 북마크 편집에서 주소를 복사한 코드로 바꿉니다.')}</li>
      <li>${t('알라딘에 로그인한 상태로 이 페이지를 엽니다.')} <a href="${url}" target="_blank" rel="noopener">${esc(url.replace('https://', ''))}</a></li>
      <li>${t('그 페이지에서 저장한 북마크를 누르고, 다 읽으면 「다봤니로 보내기」를 누릅니다.')}</li></ol>
      <div class="setbtns"><a class="bmlink" href="${esc(BM_CODE)}" data-cm="bmnop">${t('다봤니 북마크')}</a><button data-cm="bmcopy">${t('코드 복사')}</button></div></div></div>`;
}
function kindPill(k){ return k === 'l' ? `<span class="pill">${t('라이트노벨')}</span>` : k === 'c' ? `<span class="pill">${t('만화')}</span>` : ''; }
function seriesCard(s){
  const warn = s.gaps.length ? `<div class="cmwarn ${s.ack ? 'acked' : ''}">${s.ack ? '' : '⚠ '}${esc(F('missingVols', ranges(s.gaps)))}${s.ack ? '' : `<button data-cm="ack" data-k="${esc(s.key)}">${t('확인')}</button>`}</div>` : '';
  return `<div class="card cmcard">
    <button class="kv" data-cm="open" data-k="${esc(s.key)}" aria-label="${esc(s.name)}"><span class="nokv">${t('표지 없음')}</span>${s.cover ? `<img src="${esc(s.cover)}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.remove()">` : ''}${s.eb ? '<span class="ebtag">e-book</span>' : ''}</button>
    <div class="meta"><div class="t1" data-cm="open" data-k="${esc(s.key)}">${esc(s.name)}</div><div class="t2">${esc(s.pub)}</div>
      <div class="pills">${kindPill(s.kind)}<span class="pill">${esc(F('ownedTo', s.max || s.items.length))}</span></div>${warn}</div>
    <div class="prog"><button class="step" data-cm="read-" data-k="${esc(s.key)}" aria-label="${t('읽은 권 빼기')}">−</button>
      <span class="now">${s.read}<small> / ${esc(F('volN', s.max || s.items.length))}</small></span>
      <button class="step" data-cm="read+" data-k="${esc(s.key)}" aria-label="${t('읽은 권 더하기')}">+</button></div></div>`;
}
// 이름표가 붙은 한 줄짜리 고르기 (종류·보기·정렬을 줄마다 나눠 구분되게)
function chipRow(label, name, cur, opts){
  return `<div class="frow"><span class="flab">${t(label)}</span><div class="fscroll">${opts.map(([v, l, n]) => `<button class="chip ${cur === v ? 'on' : ''}" data-cm="${name}" data-v="${v}">${t(l)}${n != null ? `<span class="pill">${fmtN(n)}</span>` : ''}</button>`).join('')}</div></div>`;
}
function seg(name, cur, opts){ return `<div class="seg cmseg">${opts.map(([v, l]) => `<button data-cm="${name}" data-v="${v}" class="${cur === v ? 'on' : ''}">${t(l)}</button>`).join('')}</div>`; }
function renderBuy(q){
  const ALL = seriesList(), fc = {p: ALL.filter(s => s.fmt === 'p').length, e: ALL.filter(s => s.fmt === 'e').length};
  let L = ALL.filter(s => s.fmt === CMS.fmt);
  const counts = {all: L.length, c: L.filter(s => s.kind !== 'l').length, l: L.filter(s => s.kind === 'l').length};
  if (CMS.kind !== 'all') L = L.filter(s => (CMS.kind === 'l') === (s.kind === 'l'));
  if (q) { const nq = norm(q); L = L.filter(s => norm(s.name + s.pub).includes(nq)); }
  const gapN = L.filter(s => s.gaps.length).length;
  L.sort(CMS.sort === 'date' ? (a, b) => b.date.localeCompare(a.date) || tcmpS(a, b) : tcmpS);
  let h = guideHTML('cbuy');
  if (!Object.keys(CM.items).length) return h + `<div class="stbox"><p class="stempty">${t('아직 가져온 구매내역이 없습니다.')}</p></div>`;
  h += `<div class="seg cmfmt">${[['p', '종이책'], ['e', '이북']].map(([v, l]) => `<button data-cm="fmt" data-v="${v}" class="${CMS.fmt === v ? 'on' : ''}">${t(l)}<span class="pill">${fmtN(fc[v])}</span></button>`).join('')}</div>
  <div class="cmctl">
    <div class="frow"><span class="flab">${t('종류')}</span><div class="fscroll">${[['all', '전체'], ['c', '만화'], ['l', '라이트노벨']].map(([v, l]) => `<button class="chip ${CMS.kind === v ? 'on' : ''}" data-cm="kind" data-v="${v}">${t(l)}<span class="pill">${fmtN(counts[v])}</span></button>`).join('')}</div></div>
    ${chipRow('보기', 'view', CMS.view, [['all', '전체'], ['pub', '출판사별'], ['gap', '빠진 권 있음', gapN]])}
    ${chipRow('정렬', 'sort', CMS.sort, [['name', '이름순'], ['date', '발매일순']])}</div>`;
  if (CMS.view === 'gap') {
    const G = L.filter(s => s.gaps.length); CMQ = [];
    return h + `<h2 class="gh">${t('빠진 권 있음')}<span class="pill">${fmtN(G.length)}</span></h2>` + (G.length ? `<div class="rows cmgaps">${G.map(s => `<button class="cmrowi" data-cm="open" data-k="${esc(s.key)}">
      <span class="cover">${s.cover ? `<img src="${esc(s.cover)}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.remove()">` : ''}${s.eb ? '<span class="ebtag">e-book</span>' : ''}</span>
      <span class="grow"><b>${esc(s.name)}</b><span class="s">${esc([s.pub, F('ownedTo', s.max)].filter(Boolean).join(' · '))}</span><span class="cmwarn ${s.ack ? 'acked' : ''}">${s.ack ? '' : '⚠ '}${esc(F('missingVols', ranges(s.gaps)))}</span></span></button>`).join('')}</div>` : `<div class="stbox"><p class="stempty">${t('빠진 권이 있는 시리즈가 없습니다.')}</p></div>`);
  }
  // 그릴 순서(머리 줄·카드)만 만들어 두고, 실제 그리기는 스크롤에 맞춰 조금씩 (전부 보여 줌)
  CMQ = [];
  if (CMS.view === 'pub') {
    const G = new Map(); for (const s of L) { const p = s.pub || t('출판사 미상'); if (!G.has(p)) G.set(p, []); G.get(p).push(s); }
    for (const [p, arr] of [...G].sort((a, b) => b[1].length - a[1].length || a[0].localeCompare(b[0], 'ko'))) { CMQ.push({h: `<h2 class="gh">${esc(p)}<span class="pill">${fmtN(arr.length)}</span></h2>`}); arr.forEach(s => CMQ.push({s})); }
  } else { CMQ.push({h: `<h2 class="gh">${t('시리즈')}<span class="pill">${fmtN(L.length)}</span></h2>`}); L.forEach(s => CMQ.push({s})); }
  return h + '<div id="cmFeed"></div><div id="cmMore" class="cmmore"></div>';
}
let CMQ = [], CMQi = 0, CMQobs = null;
function cmAppend(n){
  const feed = $('#cmFeed'); if (!feed) return;
  let grid = feed.lastElementChild && feed.lastElementChild.classList.contains('grid') ? feed.lastElementChild : null, html = '';
  const flush = () => { if (html) { grid.insertAdjacentHTML('beforeend', html); html = ''; } };
  for (let k = 0; k < n && CMQi < CMQ.length; CMQi++) {
    const q = CMQ[CMQi];
    if (q.h) { if (grid) flush(); feed.insertAdjacentHTML('beforeend', q.h + '<div class="grid"></div>'); grid = feed.lastElementChild; }
    else { if (!grid) { feed.insertAdjacentHTML('beforeend', '<div class="grid"></div>'); grid = feed.lastElementChild; } html += seriesCard(q.s); k++; }
  }
  flush();
  if (CMQi >= CMQ.length && CMQobs) { CMQobs.disconnect(); CMQobs = null; }
}
function tcmpS(a, b){
  const g = s => /^[가-힣]/.test(s) ? 0 : /^[\u3040-\u30ff\u3400-\u9fff]/.test(s) ? 2 : 1;
  return (g(a.name) - g(b.name)) || a.name.localeCompare(b.name, 'ko');
}
function renderCart(){
  let h = guideHTML('ccart');
  if (!CM.carts.length) return h + `<div class="stbox"><p class="stempty">${t('아직 백업한 장바구니가 없습니다.')}</p></div>`;
  const i = Math.min(CMS.cart, CM.carts.length - 1), c = CM.carts[i];
  h += `<div class="cmrow">${CM.carts.length > 1 ? `<div class="fscroll cmsnap">${CM.carts.map((x, j) => `<button class="chip ${j === i ? 'on' : ''}" data-cm="snap" data-v="${j}">${esc(new Date(x.at).toLocaleString('ko-KR', {month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit'}))}</button>`).join('')}</div>` : `<span class="setnote">${esc(new Date(c.at).toLocaleString('ko-KR'))} ${t('백업')}</span>`}<button class="cmdel" data-cm="snapdel" data-v="${i}">${t('이 백업 지우기')}</button></div>`;
  for (const sec of c.sections) {
    if (!sec.items.length) continue;
    h += `<h2 class="gh">${esc(sec.name || t('기타'))}<span class="pill">${fmtN(sec.items.length)}</span></h2><div class="rows cmcart">${sec.items.map(it => `<a class="cmrowi" href="https://www.aladin.co.kr/m/mproduct.aspx?ItemId=${esc(it.id)}" target="_blank" rel="noopener">
      <span class="cover">${it.cover ? `<img src="${esc(it.cover)}" alt="" loading="lazy" referrerpolicy="no-referrer">` : ''}${it.eb ? '<span class="ebtag">e-book</span>' : ''}</span>
      <span class="grow"><b>${esc(it.t)}</b><span class="s">${esc([it.pub, it.price ? F('won', it.price) : ''].filter(Boolean).join(' · '))}</span></span>${kindPill(it.kind)}</a>`).join('')}</div>`;
  }
  return h;
}
function cmRender(tab){
  const box = $('#comics');
  box.innerHTML = tab === 'ccart' ? renderCart() : renderBuy(S.q);
  if (CMQobs) { CMQobs.disconnect(); CMQobs = null; }
  if (tab !== 'ccart' && $('#cmFeed')) {
    CMQi = 0; cmAppend(48);
    CMQobs = new IntersectionObserver(es => { if (es.some(e => e.isIntersecting)) cmAppend(48); }, {rootMargin: '1200px 0px'});
    CMQobs.observe($('#cmMore'));
  }
  box.querySelectorAll('.fscroll').forEach(el => { const f = () => { el.classList.toggle('fl', el.scrollLeft > 2); el.classList.toggle('fr', el.scrollLeft + el.clientWidth < el.scrollWidth - 2); }; el.onscroll = f; f(); });
}
function cmOpen(key){
  const s = seriesList().find(x => x.key === key); if (!s) return;
  const box = document.createElement('div'); box.id = 'editor';
  box.innerHTML = `<div class="ebox cmsheet" role="dialog" aria-modal="true"><h3>${esc(s.name)}</h3><p class="setnote">${esc([s.pub, s.kind === 'l' ? t('라이트노벨') : t('만화')].join(' · '))}</p>
    ${s.gaps.length ? `<p class="cmwarn ${s.ack ? 'acked' : ''}">${esc(F('missingVols', ranges(s.gaps)))}</p>
      <div class="cmext"><span class="setnote">${t('다른 곳에서 산 권을 누르세요')}</span><div class="pills">${s.gaps.map(v => `<button class="chip" data-cmx="add" data-v="${v}">${esc(F('volN', v))}</button>`).join('')}${s.gaps.length > 1 ? `<button class="chip on" data-cmx="all">${esc(F('allMissing', ranges(s.gaps)))}</button>` : ''}</div></div>` : ''}
    ${s.ext.length ? `<div class="cmext"><span class="setnote">${t('다른 곳에서 삼')}</span><div class="pills">${s.ext.map(v => `<button class="chip ext" data-cmx="del" data-v="${v}">${esc(F('volN', v))} ✕</button>`).join('')}</div></div>` : ''}
    <div class="rows">${s.items.map(it => `<a class="cmrowi" href="https://www.aladin.co.kr/m/mproduct.aspx?ItemId=${esc(it.id)}" target="_blank" rel="noopener">
      <span class="cover">${it.cover ? `<img src="${esc(it.cover)}" alt="" loading="lazy" referrerpolicy="no-referrer">` : ''}${it.eb ? '<span class="ebtag">e-book</span>' : ''}</span>
      <span class="grow"><b>${esc(it.vols && it.vols.length > 1 ? F('volN', `${it.vols[0]}~${it.vols[it.vols.length - 1]}`) : it.vol ? F('volN', it.vol) : t('권수 미상'))}${it.ed ? ` <span class="pill edtag">${esc(it.ed)}</span>` : ''}${it.vol && s.read >= it.vol ? ` <i class="ck">✓</i>` : ''}</b><span class="s">${esc(it.t)}</span><span class="s">${esc([okDate(it.date) && F('pubOn', it.date), okDate(it.buy) && F('boughtOn', it.buy)].filter(Boolean).join(' · '))}</span></span></a>`).join('')}</div>
    <div class="ebtns"><button class="ecancel">${t('닫기')}</button></div></div>`;
  document.body.appendChild(box);
  box.querySelector('.ecancel').onclick = () => box.remove();
  box.onclick = e => {
    if (e.target === box) return box.remove();
    const b = e.target.closest('[data-cmx]'); if (!b) return;
    const st = (CM.series[key] ||= {}), ext = new Set(st.ext || []), v = +b.dataset.v;
    if (b.dataset.cmx === 'add') ext.add(v); if (b.dataset.cmx === 'del') ext.delete(v); if (b.dataset.cmx === 'all') s.gaps.forEach(x => ext.add(x));
    st.ext = [...ext].sort((a, b2) => a - b2); st.u = Date.now(); cmSave();
    box.remove(); cmOpen(key); cmRender(S.tab);
  };
}
document.addEventListener('click', e => {
  const el = e.target.closest('[data-cm]'); if (!el || !$('#comics') || !$('#comics').contains(el)) return;
  const a = el.dataset.cm, k = el.dataset.k;
  if (a === 'bmnop') { e.preventDefault(); return; }
  e.stopPropagation();
  if (a === 'open') return cmOpen(k);
  if (a === 'guide') { CMS.guide = !CMS.guide; return cmRender(S.tab); }
  if (a === 'bmcopy') { navigator.clipboard?.writeText(BM_CODE).then(() => { el.textContent = t('복사했습니다'); }, () => {}); return; }
  if (a === 'kind' || a === 'view' || a === 'sort' || a === 'fmt') { CMS[a] = el.dataset.v; store.set('cm' + a[0].toUpperCase() + a.slice(1), CMS[a]); return cmRender(S.tab); }
  if (a === 'snap') { CMS.cart = +el.dataset.v; return cmRender(S.tab); }
  if (a === 'snapdel') { if (!confirm(t('이 장바구니 백업을 지울까요?'))) return; CM.carts.splice(+el.dataset.v, 1); CMS.cart = 0; cmSave(); return cmRender(S.tab); }
  const st = (CM.series[k] ||= {});
  const s = seriesList().find(x => x.key === k); if (!s) return;
  if (a === 'read+' || a === 'read-') { st.read = Math.max(0, Math.min((s.max || 999), (st.read || 0) + (a === 'read+' ? 1 : -1))); s.read = st.read; }
  if (a === 'ack') { st.ack = s.gaps.join(','); s.ack = true; }
  st.u = Date.now(); store.set('comics', CM); if (typeof syncSoon === 'function') syncSoon();      // 묶음은 그대로라 다시 계산하지 않음
  const card = el.closest('.cmcard'); if (card) card.outerHTML = seriesCard(s);
}, true);

/* ---------- 북마클릿에서 받기 ---------- */
window.addEventListener('message', e => {
  const d = e.data;
  if (!ALADIN.includes(e.origin) || !d || d.type !== 'dabwanni-aladin' || !Array.isArray(d.items)) return;
  const now = Date.now(); let added = 0;
  const pick = x => ({id: String(x.id), t: String(x.t || '').slice(0, 300), cover: /^https:\/\//.test(x.cover || '') ? x.cover : '', pub: String(x.pub || '').slice(0, 80),
    date: String(x.date || '').slice(0, 10), kind: x.kind === 'l' ? 'l' : 'c', eb: x.eb ? 1 : 0, price: +x.price || 0,
    ...(x.g != null ? {g: String(x.g).slice(0, 300)} : {}), ...(x.f != null ? {f: String(x.f).slice(0, 80)} : {}),
    ...(x.sid ? {sid: String(x.sid).slice(0, 20)} : {}), ...(Array.isArray(x.cats) ? {cats: x.cats.slice(0, 6).map(p => String(p).slice(0, 120))} : {})});
  if (d.kind === 'purchase') {
    for (const x of d.items) { if (!x.id) continue; const it = pick(x), old = CM.items[it.id]; if (!old) added++;
      CM.items[it.id] = {...old, ...it, own: 1, buy: String(x.buy || old?.buy || '').slice(0, 10), vol: volOf(it.t), u: now}; delete CM.unres[it.id]; }
    for (const f of (Array.isArray(d.fails) ? d.fails : [])) {
      const id = String(f.id || ''); if (!id || hasItem(CM.items, id) || CM.unresOff[id]) continue;
      CM.unres[id] = {id, t: String(f.t || '').slice(0, 300), buy: String(f.buy || '').slice(0, 10), cover: /^https:\/\//.test(f.cover || '') ? f.cover : '', snip: String(f.snip || '').slice(0, 160), at: now};
    }
  } else if (d.kind === 'cart') {
    const secs = (Array.isArray(d.sections) ? d.sections : []).map(s => ({name: String(s.name || '').slice(0, 40), items: (s.items || []).filter(x => x.id).map(pick)}));
    CM.carts.unshift({at: now, sections: secs}); added = secs.reduce((n, s) => n + s.items.length, 0);
  }
  cmSave();
  try { e.source && e.source.postMessage({type: 'dabwanni-aladin-ack', added}, e.origin); } catch {}
  store.set('cmTab', d.kind === 'cart' ? 'ccart' : 'cbuy');
  setMode('comic', d.kind === 'cart' ? 'ccart' : 'cbuy');
});

/* ---------- 동기화에 넣기: 작품·시리즈는 바뀐 시각이 늦은 쪽, 장바구니 백업은 합쳐 최근 12개 ---------- */
// 세트를 권마다 나눠 넣은 경우(「…#3」)도 넣은 것으로 침
const hasItem = (items, id) => !!items[id] || Object.keys(items).some(k => k.startsWith(id + '#'));
function cmMerge(L, R_){
  const out = {v: 1, items: {...(R_?.items || {})}, series: {...(R_?.series || {})}, carts: [], unres: {}, unresOff: {}};
  for (const [k, v] of Object.entries(L.items || {})) if (!out.items[k] || (v.u || 0) >= (out.items[k].u || 0)) out.items[k] = v;
  for (const [k, v] of Object.entries(L.series || {})) if (!out.series[k] || (v.u || 0) >= (out.series[k].u || 0)) out.series[k] = v;
  const seen = new Set(); for (const c of [...(L.carts || []), ...(R_?.carts || [])].sort((a, b) => b.at - a.at)) if (!seen.has(c.at)) { seen.add(c.at); out.carts.push(c); }
  out.unres = {...(R_?.unres || {}), ...(L.unres || {})}; out.unresOff = {...(R_?.unresOff || {}), ...(L.unresOff || {})};
  for (const k of Object.keys(out.unres)) if (hasItem(out.items, k) || out.unresOff[k]) delete out.unres[k];
  return out;
}

/* ---------- 설정: 가져오기 실패 (알라딘에서 끝내 못 읽은 상품을 직접 시리즈·권에 넣기) ---------- */
function renderUnres(){
  const box = $('#cmUnres'); if (!box) return;
  const L = Object.values(CM.unres || {}).sort((a, b) => String(b.buy).localeCompare(String(a.buy)));
  $('#cmUnresN').textContent = fmtN(L.length); $('#cmUnresN').hidden = !L.length;
  box.innerHTML = L.length ? `<div class="rows cmunres">${L.map(f => `<div class="cmrowi">
      <span class="cover">${f.cover ? `<img src="${esc(f.cover)}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.remove()">` : ''}</span>
      <span class="grow"><b>${esc(f.t)}</b><span class="s">${esc(f.snip)}</span>
        <span class="cmubtn"><button data-cmu="add" data-id="${esc(f.id)}">${t('시리즈에 넣기')}</button><button data-cmu="off" data-id="${esc(f.id)}">${t('목록에서 빼기')}</button></span></span></div>`).join('')}</div>`
    : `<p class="setnote">${t('못 읽은 상품이 없습니다.')}</p>`;
}
document.addEventListener('click', e => {
  const b = e.target.closest('[data-cmu]'); if (!b) return;
  const f = CM.unres[b.dataset.id]; if (!f) return;
  if (b.dataset.cmu === 'off') { CM.unresOff[f.id] = 1; delete CM.unres[f.id]; cmSave(); return renderUnres(); }
  const ffmt = /^\s*\[(?:전자책|eBook)\]/i.test(f.t) ? 'e' : 'p';      // 이북 상품이면 이북 시리즈 중에서
  const S_ = seriesList().filter(s => s.fmt === ffmt), raw = String(f.t).replace(/^\s*(\[[^\]]*\]\s*)+/, ''), base = baseOf(raw);
  // 비슷한 정도: 두 글자 묶음 겹침(다이스 계수) + 한쪽이 다른 쪽을 품으면 가산
  const bg = s => { const n = norm(s), r = new Set(); for (let k = 0; k < n.length - 1; k++) r.add(n.slice(k, k + 2)); return r; };
  const sim = (a, b) => { const A = bg(a), B = bg(b); if (!A.size || !B.size) return 0; let x = 0; A.forEach(v => { if (B.has(v)) x++; }); const n1 = norm(a), n2 = norm(b); return 2 * x / (A.size + B.size) + (n1 && n2 && (n1.includes(n2) || n2.includes(n1)) ? 0.5 : 0); };
  const scored = S_.map(s => ({s, v: sim(base, s.name)})).filter(o => o.v > 0.25).sort((a, b) => b.v - a.v).slice(0, 5);
  const row = s => `<button class="cmpick" data-key="${esc(s.key)}"><b>${esc(s.name)}</b><span class="s">${esc([s.pub, s.kind === 'l' ? t('라이트노벨') : t('만화'), F('ownedTo', s.max || s.items.length)].filter(Boolean).join(' · '))}</span></button>`;
  const box = document.createElement('div'); box.id = 'editor';
  box.innerHTML = `<div class="ebox" role="dialog" aria-modal="true"><h3>${t('시리즈에 넣기')}</h3><p class="setnote">${esc(f.t)}</p>
    ${scored.length ? `<h4 class="cmh4">${t('비슷한 시리즈')}</h4><div class="cmpicks">${scored.map(o => row(o.s)).join('')}</div>` : ''}
    <h4 class="cmh4">${t('시리즈 찾기')}</h4><input id="cmuQ" class="cmq" type="search" value="" placeholder="${esc(t('시리즈 이름'))}" autocomplete="off">
    <div class="cmpicks" id="cmuR"></div>
    <div class="cmsel" id="cmuSel"></div>
    <label class="erow"><span>${t('권')}</span><input id="cmuV" type="text" inputmode="text" value="${esc((pv => pv.vols.length > 1 ? `${pv.vols[0]}~${pv.vols[pv.vols.length - 1]}` : pv.vol || '')(parseTitle(raw)))}" placeholder="3, 1~10, 1,3,5"></label>
    <div class="seg emode" id="cmuK"><button data-k="c" class="on">${t('만화')}</button><button data-k="l">${t('라이트노벨')}</button></div>
    <div class="ebtns"><button class="ecancel">${t('닫기')}</button><button class="esave" disabled>${t('저장')}</button></div></div>`;
  document.body.appendChild(box);
  let pickS = null, newName = '', kind = 'c';
  const setKind = k => { kind = k; box.querySelectorAll('#cmuK [data-k]').forEach(y => y.classList.toggle('on', y.dataset.k === k)); };
  const showSel = () => {
    box.querySelector('#cmuSel').innerHTML = pickS ? `${t('선택')}: <b>${esc(pickS.name)}</b>` : newName ? `${t('새 시리즈')}: <b>${esc(newName)}</b>` : '';
    box.querySelector('.esave').disabled = !(pickS || newName);
    box.querySelectorAll('.cmpick').forEach(x => x.classList.toggle('on', !!pickS && x.dataset.key === pickS.key));
  };
  const search = () => {
    const q = box.querySelector('#cmuQ').value.trim(), nq = norm(q);
    const R0 = !nq ? [] : S_.map(s => ({s, v: norm(s.name).includes(nq) ? 2 + nq.length / Math.max(1, norm(s.name).length) : sim(q, s.name)})).filter(o => o.v > 0.3).sort((a, b) => b.v - a.v).slice(0, 20);
    box.querySelector('#cmuR').innerHTML = R0.map(o => row(o.s)).join('') + (q ? `<button class="cmpick cmnew" data-new="1"><b>${esc(t('새 시리즈로'))}: ${esc(q)}</b></button>` : '');
  };
  box.querySelector('#cmuQ').oninput = search;
  box.querySelectorAll('#cmuK [data-k]').forEach(x => x.onclick = () => setKind(x.dataset.k));
  box.querySelector('.ecancel').onclick = () => box.remove();
  box.onclick = ev => {
    if (ev.target === box) return box.remove();
    const p = ev.target.closest('.cmpick'); if (!p) return;
    if (p.dataset.new) { newName = box.querySelector('#cmuQ').value.trim(); pickS = null; }
    else { pickS = S_.find(s => s.key === p.dataset.key); newName = ''; if (pickS) setKind(pickS.kind === 'l' ? 'l' : 'c'); }
    showSel();
  };
  box.querySelector('.esave').onclick = () => {
    const name = pickS ? pickS.name : newName; if (!name) return;
    // 권: 「3」, 「1~10」·「1-10」, 「1,3,5」 → 권마다 한 권씩 넣음 (세트 하나에서 여러 권)
    const vs = []; String(box.querySelector('#cmuV').value).split(/[,，\s]+/).forEach(p => { const m = p.match(/^(\d{1,3})(?:\s*[~∼～\-]\s*(\d{1,3}))?$/); if (!m) return; const a = +m[1], z = m[2] ? +m[2] : a; for (let n = Math.min(a, z); n <= Math.max(a, z) && n - Math.min(a, z) < 200; n++) vs.push(n); });
    const s = pickS, sid = s ? (s.items.find(i => i.sid) || {}).sid : undefined, now = Date.now();
    const mk = v => ({t: v ? `${name} ${v}` : name, orig: f.t, own: 1, kind: s ? s.kind : kind, buy: f.buy, cover: f.cover, pub: s ? s.pub : '', man: 1, ...(sid ? {sid} : {}), u: now});
    if (vs.length <= 1) CM.items[f.id] = {id: f.id, ...mk(vs[0])};
    else vs.forEach(v => { const id = `${f.id}#${v}`; CM.items[id] = {id, ...mk(v)}; });
    delete CM.unres[f.id]; cmSave(); box.remove(); renderUnres();
  };
});
