'use strict';
const TYPE = {T:'TV', O:'웹', V:'OVA', S:'스페셜', M:'극장판', X:'미분류'};
const TYPE_ORDER = ['T','O','V','S','M','X'];
const QL = {1:'1분기', 2:'2분기', 3:'3분기', 4:'4분기'};
const QM = {1:'1~3월', 2:'4~6월', 3:'7~9월', 4:'10~12월'};
const LEN = {short:'숏 (5분 이하)', half:'하프 (6~17분)', normal:'일반 (18~35분)', long:'장편 (36분 이상)'};
const ROLE = {MAIN:'주연', SUPPORTING:'조연', BACKGROUND:'엑스트라'};
const SONG = {OP:'오프닝', ED:'엔딩', IN:'삽입곡'};
const CREDIT_ORDER = ['歌','作詞','作曲','編曲'];
const CREDIT_KO = {'歌':'노래','作詞':'작사','作曲':'작곡','編曲':'편곡'};
const RT = {SEQUEL:'다음 시즌', PREQUEL:'이전 시즌', SIDE_STORY:'외전', PARENT:'본편', SPIN_OFF:'스핀오프', ALTERNATIVE:'다른 버전', SUMMARY:'총집편', ADAPTATION:'원작', CHARACTER:'캐릭터 공유', COMPILATION:'총집편', CONTAINS:'포함', SOURCE:'원작', OTHER:'기타'};
const LINK_KO = {'Official Site':'공식 사이트', 'Twitter':'공식 X', 'X':'공식 X', 'YouTube':'유튜브', 'Instagram':'인스타그램', 'TikTok':'틱톡', 'Facebook':'페이스북'};
const STUDIO_AS = {main:'애니메이션 제작', coop:'협력 (회차)', committee:'제작위원회·참여사'};
const PAGE = 120, NB = 2048;

const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmtN = n => Number(n).toLocaleString('ko-KR');
const today = () => new Date().toISOString().slice(0, 10);
const store = {
  get(k, d){ try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch { return d; } },
  set(k, v){ try { localStorage.setItem(k, JSON.stringify(v)); } catch {} }
};

let W = [], BYK = new Map(), STUDIOS = [], TAGS = [], IDX = {people:null, studios:null}, usedAuto = false;
const marks = store.get('marks', {});   // {k: {w,i,ep,rate,memo,re,start,end}}
const S = { tab:'season', theme:store.get('theme', 'system'), lang:store.get('lang', 'ko'), q:'', y:2026, qq:4, types:new Set(), lens:new Set(), shown:PAGE };

/* ---------- 데이터 ---------- */
function fnv(s){ let h = 0x811c9dc5; for (const b of new TextEncoder().encode(s)) { h ^= b; h = Math.imul(h, 0x01000193) >>> 0; } return h % NB; }
const bucketCache = new Map();
async function getJSON(u){ try { const r = await fetch(u); return r.ok ? await r.json() : null; } catch { return null; } }
async function item(kind, id){
  const key = kind + '/' + fnv(id);
  if (!bucketCache.has(key)) bucketCache.set(key, getJSON(`data/${key}.json`));
  return ((await bucketCache.get(key)) || {})[id] || null;
}
function lenKind(w){ const m = w.d ? w.d / 60 : null; if (m == null) return null; return m <= 5 ? 'short' : m <= 17 ? 'half' : m <= 35 ? 'normal' : 'long'; }
function title(w, lang = S.lang){ const o = {ko:w.ko, ja:w.ja, en:w.en, r:w.r}; return o[lang] || o.ko || o.ja || o.en || o.r; }
function subtitle(w){ const t = title(w); return (S.lang === 'ja' ? [w.ko, w.en, w.r] : [w.ja, w.en, w.r]).find(x => x && x !== t) || ''; }
// 키 비주얼: MAL은 기본(약 225px)과 큰 것(l, 약 425px)을 화면 밀도에 맞춰 고르게 함
function img(w, big){
  if (!w.p) return '';
  if (w.p[0] === 'M') { const p = w.p.slice(1); return 'https://cdn.myanimelist.net/images/anime/' + (big ? p.replace(/\.(jpg|webp)$/, 'l.$1') : p); }
  if (w.p[0] === 'A') return w.p.slice(1);
  return /^https:\/\//.test(w.p) ? w.p : '';
}
function srcset(w){
  if (w.p && w.p[0] === 'M') { const b = 'https://cdn.myanimelist.net/images/anime/' + w.p.slice(1); return `${b} 225w, ${b.replace(/\.(jpg|webp)$/, 'l.$1')} 425w`; }
  return '';
}
// 방영 상태: 원천 목록의 '방영 예정'은 늦게 갱신되므로, 시작 분기가 지났으면 표시하지 않음
function curQ(){ const d = new Date(); return d.getFullYear() * 10 + Math.floor(d.getMonth() / 3) + 1; }
function statusLabel(w){
  if (w.st === 'O') return '방영 중';
  if (w.st === 'H') return '휴방 중';
  if (w.st === 'U') { const s = w.y ? w.y * 10 + (w.q || 1) : null; return (!s || s > curQ()) ? '방영 예정' : ''; }
  return '';
}
function norm(s){ return (s || '').toLowerCase().normalize('NFKC').replace(/[\s\-_:;!?！？・･.,'"“”‘’()（）\[\]「」『』~〜]/g, ''); }
const total = w => w.e || 0;

// 화면 모드: 기기 설정 따름 / 라이트 / 다크. 로고도 같은 모드 그림으로 바꿈
function applyTheme(){
  const t = S.theme || 'system';
  if (t === 'system') document.documentElement.removeAttribute('data-theme'); else document.documentElement.dataset.theme = t;
  const media = t === 'dark' ? 'all' : t === 'light' ? 'not all' : '(prefers-color-scheme: dark)';
  document.querySelectorAll('.logo source').forEach(s => s.media = media);
}
function setLogo(){
  const l = S.lang === 'ja' ? 'ja' : (S.lang === 'en' || S.lang === 'r') ? 'en' : 'ko';
  document.querySelectorAll('.logo picture').forEach(p => p.classList.toggle('on', p.dataset.l === l));
  document.documentElement.lang = l;
}
async function boot(){
  applyTheme(); setLogo();
  const d = await getJSON('data/catalog.json');
  STUDIOS = d.studios; TAGS = d.tags || [];
  const nonjp = await getJSON('data/nonjp.json') || {};
  const F = d.fields;
  W = d.rows.filter(r => !nonjp[r[0]]).map(r => { const o = {}; F.forEach((f, i) => o[f] = r[i]); o.lk = lenKind(o); o.n = norm([o.r, o.ja, o.ko, o.en].join('|')); return o; });
  W.forEach(w => BYK.set(w.k, w));
  // 중복으로 합쳐져 사라진 작품에 남은 체크 기록은 남은 작품으로 옮김
  let moved = 0;
  for (const [old, k] of Object.entries(d.aliases || {})) {
    if (marks[old] && !BYK.has(old) && BYK.has(k)) {
      const a = marks[old], b = marks[k] || (marks[k] = {});
      for (const f of ['w', 'i', 'rate', 'memo', 'start', 'end']) if (a[f] && !b[f]) b[f] = a[f];
      b.ep = Math.max(b.ep || 0, a.ep || 0) || undefined; if (!b.ep) delete b.ep;
      b.re = Math.max(b.re || 0, a.re || 0) || undefined; if (!b.re) delete b.re;
      delete marks[old]; moved++;
    }
  }
  if (moved) save();
  $('#totalPill').textContent = fmtN(W.length) + '편';
  bind(); route(); render();
}

/* ---------- 이벤트 ---------- */
function bind(){
  document.querySelectorAll('.tabs button').forEach(b => b.onclick = () => {
    S.tab = b.dataset.tab; S.shown = PAGE;
    document.querySelectorAll('.tabs button').forEach(x => x.classList.toggle('on', x === b));
    render(); window.scrollTo(0, 0);
  });
  let t; $('#q').oninput = e => {
    $('#qClear').hidden = !e.target.value;
    clearTimeout(t); t = setTimeout(async () => { S.q = e.target.value.trim(); S.shown = PAGE; if (S.q) await loadIdx(); render(); }, 200);
  };
  $('#qClear').onclick = () => { clearTimeout(t); $('#q').value = ''; $('#qClear').hidden = true; S.q = ''; S.shown = PAGE; render(); $('#q').focus(); };
  $('#setLang').onclick = e => { const b = e.target.closest('[data-lang]'); if (!b) return; S.lang = b.dataset.lang; store.set('lang', S.lang); setLogo(); render(); };
  $('#setTheme').onclick = e => { const b = e.target.closest('[data-theme-set]'); if (!b) return; S.theme = b.dataset.themeSet; store.set('theme', S.theme); applyTheme(); render(); };
  matchMedia('(prefers-color-scheme: dark)').addEventListener?.('change', applyTheme);
  $('#qPick').onclick = () => openPicker();
  $('#prevQ').onclick = () => { if (--S.qq < 1) { S.qq = 4; S.y--; } S.shown = PAGE; render(); };
  $('#nextQ').onclick = () => { if (++S.qq > 4) { S.qq = 1; S.y++; } S.shown = PAGE; render(); };
  document.addEventListener('click', onClick);
  document.addEventListener('pointerdown', holdStart);
  ['pointerup', 'pointercancel', 'lostpointercapture'].forEach(t => document.addEventListener(t, holdStop));
  document.addEventListener('contextmenu', e => { if (e.target.closest('.step')) e.preventDefault(); });
  // 확대·축소 막기: 사파리는 viewport 설정을 무시하므로 손가락 모으기 동작 자체를 막음
  ['gesturestart', 'gesturechange', 'gestureend'].forEach(t => document.addEventListener(t, e => e.preventDefault(), {passive: false}));
  document.addEventListener('touchmove', e => { if (e.touches.length > 1) e.preventDefault(); }, {passive: false});
  document.addEventListener('change', onChange);
  window.addEventListener('hashchange', route);
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && !$('#sheet').hidden) closeSheet(); });
  $('#exportBtn').onclick = () => {
    const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([JSON.stringify({v:2, marks}, null, 1)], {type:'application/json'}));
    a.download = 'dabwanni-marks.json'; a.click();
  };
  $('#importFile').onchange = async e => {
    const f = e.target.files[0]; if (!f) return;
    try { const d = JSON.parse(await f.text()); Object.assign(marks, d.marks || {}); save(); render(); alert('체크 기록을 불러왔습니다.'); }
    catch { alert('파일 형식이 맞지 않습니다. 이 사이트에서 내보낸 파일을 선택하세요.'); }
  };
}
async function loadIdx(){
  if (!IDX.people) IDX.people = await getJSON('data/people/index.json') || {};
  if (!IDX.studios) IDX.studios = await getJSON('data/studios/index.json') || {};
}
function save(){ for (const k in marks) { const m = marks[k]; if (!m.w && !m.i && !m.ep && !m.rate && !m.memo && !m.re && !m.start && !m.end) delete marks[k]; } store.set('marks', marks); }
const M = k => marks[k] || (marks[k] = {});

function onClick(e){
  const el = e.target.closest('[data-act]');
  if (el) {
    const {act, k} = el.dataset;
    if (act === 'w' || act === 'i') {
      const m = M(k); m[act] ? delete m[act] : (m[act] = 1);
      if (act === 'w' && m.w) { const t = total(BYK.get(k)); if (t) m.ep = t; if (!m.start) m.start = today(); if (!m.end) m.end = today(); }
      save(); refresh(k); return;
    }
    if ((act === 'ep+' || act === 'ep-') && e.detail === 0) { setEp(k, (M(k).ep || 0) + (act === 'ep+' ? 1 : -1)); return; }   // 키보드로 누른 경우만 (손가락·마우스는 아래 길게 누르기 처리)
    if (act === 'epset') { const n = +el.dataset.no, cur = M(k).ep || 0; setEp(k, cur >= n ? n - 1 : n); return; }
    if (act === 'rate') { const m = M(k), n = +el.dataset.n; m.rate = m.rate === n ? 0 : n; save(); refresh(k); return; }
    if (act === 're+' || act === 're-') { const m = M(k); m.re = Math.max(0, (m.re || 0) + (act === 're+' ? 1 : -1)); save(); refresh(k); return; }
    if (act === 'open') { location.hash = '#/w/' + encodeURIComponent(k); return; }
    if (act === 'person') { location.hash = '#/p/' + encodeURIComponent(el.dataset.p); return; }
    if (act === 'studio') { location.hash = '#/s/' + encodeURIComponent(el.dataset.s); return; }
    if (act === 'type' || act === 'len') { const set = act === 'type' ? S.types : S.lens, v = el.dataset.v; set.has(v) ? set.delete(v) : set.add(v); S.shown = PAGE; render(); return; }
    if (act === 'more') { S.shown += PAGE * 2; render(); return; }
  }
  if (e.target.closest('[data-close]')) closeSheet();
}
// + − 길게 누르기: 처음 0.4초 뒤부터 반복, 반복할수록 간격이 짧아짐 (최소 0.04초)
let hold = null;
function holdStart(e){
  const b = e.target.closest('[data-act="ep+"],[data-act="ep-"]'); if (!b) return;
  e.preventDefault();
  const k = b.dataset.k, d = b.dataset.act === 'ep+' ? 1 : -1;
  holdStop();
  const step = () => setEp(k, (M(k).ep || 0) + d);
  step();
  let delay = 400, n = 0;
  const tick = () => { step(); n++; delay = Math.max(40, 220 * Math.pow(0.85, n)); hold.t = setTimeout(tick, delay); };
  hold = {b, t: setTimeout(tick, delay)};
  b.setPointerCapture?.(e.pointerId);
}
function holdStop(){ if (hold) { clearTimeout(hold.t); hold = null; } }
/* ---------- 통계 ---------- */
const AVG_MIN = {T: 24, O: 15, V: 30, S: 24, M: 100, X: 24};   // 1화 길이를 모르는 작품의 어림값(분)
function fmtDHM(min){
  min = Math.round(min); const d = Math.floor(min / 1440), h = Math.floor(min % 1440 / 60), m = min % 60;
  return `${d ? `${fmtN(d)}<small>일</small> ` : ''}${d || h ? `${h}<small>시간</small> ` : ''}${m}<small>분</small>`;
}
function fmtHM(min){ min = Math.round(min); return `${fmtN(Math.floor(min / 60))}<small>시간</small> ${min % 60}<small>분</small>`; }
const hbarRow = (label, parts, max, total) => `<span class="lab">${label}</span><span class="bar">${parts.map(([cls, n]) => n ? `<i class="${cls}" style="width:${(n / max * 100).toFixed(2)}%"></i>` : '').join('')}</span><span class="num">${fmtN(total)}</span>`;
function venn(a, ab, b, bc, c){
  // 왼쪽 보는 중 · 가운데 관심 · 오른쪽 봤음. 보는 중과 봤음은 겹칠 수 없어 사슬 모양
  const num = (x, y, n) => `<text x="${x}" y="${y}" text-anchor="middle" font-size="20" font-weight="800" fill="var(--ink)">${fmtN(n)}</text>`;
  const lab = (x, y, s, col) => `<text x="${x}" y="${y}" text-anchor="middle" font-size="13" font-weight="700" fill="${col}">${s}</text>`;
  return `<svg class="venn" viewBox="0 0 340 190" role="img" aria-label="보는 중 ${a + ab}, 관심 ${ab + b + bc}, 봤음 ${bc + c}">
    <circle cx="80" cy="100" r="72" fill="var(--watching)" fill-opacity=".22" stroke="var(--watching)" stroke-width="2"/>
    <circle cx="170" cy="100" r="72" fill="var(--want)" fill-opacity=".22" stroke="var(--want)" stroke-width="2"/>
    <circle cx="260" cy="100" r="72" fill="var(--onair)" fill-opacity=".22" stroke="var(--onair)" stroke-width="2"/>
    ${lab(62, 20, '보는 중', 'var(--watching)')}${lab(170, 20, '관심', 'var(--want)')}${lab(278, 20, '봤음', 'var(--onair)')}
    ${num(55, 107, a)}${num(125, 107, ab)}${num(170, 160, b)}${num(215, 107, bc)}${num(285, 107, c)}
  </svg>`;
}
let statsBy = 'q';
function renderStats(){
  const L = [];
  for (const [k, m] of Object.entries(marks)) { const w = BYK.get(k); if (w && (m.w || m.i || m.ep)) L.push([w, m]); }
  const watched = L.filter(([, m]) => m.w), watching = L.filter(([, m]) => m.ep && !m.w), want = L.filter(([, m]) => m.i);
  if (!L.length) { $('#stats').innerHTML = `<div class="stbox"><p class="stempty">아직 기록이 없습니다. 작품 카드에서 봤음·관심을 누르거나 본 회차를 늘리면 여기에 통계가 쌓입니다.</p></div>`; return; }
  const a = L.filter(([, m]) => m.ep && !m.w && !m.i).length, ab = L.filter(([, m]) => m.ep && !m.w && m.i).length;
  const b = L.filter(([, m]) => m.i && !m.w && !m.ep).length, bc = L.filter(([, m]) => m.i && m.w).length, c = L.filter(([, m]) => m.w && !m.i).length;

  // 본 화수·시간 (다시 본 횟수 포함, 1화 길이를 모르면 형식별 어림값)
  let eps = 0, min = 0, guessed = 0, reEps = 0;
  for (const [w, m] of L) {
    const seen = m.w ? (total(w) || m.ep || 1) : (m.ep || 0);
    if (!seen) continue;
    const re = m.w ? (m.re || 0) * (total(w) || seen) : 0;
    const per = w.d ? w.d / 60 : AVG_MIN[w.ty] || 24;
    if (!w.d) guessed++;
    eps += seen + re; reEps += re; min += (seen + re) * per;
  }

  // 분기별·연도별 히스토그램 (방영 시기 기준)
  const key = w => !w.y ? '연도 미상' : statsBy === 'y' ? `${w.y}년` : `${w.y} ${w.q ? w.q + '분기' : '미상'}`;
  const ord = w => (w.y || 0) * 10 + (statsBy === 'y' ? 0 : (w.q || 0));
  const grp = new Map();
  for (const [w, m] of L) {
    const g = grp.get(key(w)) || grp.set(key(w), {o: ord(w), w: 0, g: 0, i: 0}).get(key(w));
    if (m.w) g.w++; else if (m.ep) g.g++; else if (m.i) g.i++;
  }
  const G = [...grp].sort((x, y) => y[1].o - x[1].o), gmax = Math.max(...G.map(([, g]) => g.w + g.g + g.i));

  // 형식·장르·제작사 (봤음 기준)
  const count = (arr, f) => { const c = new Map(); arr.forEach(x => f(x).forEach(k => k && c.set(k, (c.get(k) || 0) + 1))); return [...c].sort((p, q) => q[1] - p[1]); };
  const byType = count(watched, ([w]) => [TYPE[w.ty]]);
  const byTag = count(watched, ([w]) => (w.tags || []).map(i => TAGS[i])).slice(0, 10);
  const byStudio = count(watched, ([w]) => (w.stu || []).map(i => STUDIOS[i] && STUDIOS[i][1])).slice(0, 10);
  const byDecade = count(watched, ([w]) => [w.y ? `${Math.floor(w.y / 10) * 10}년대` : '연도 미상']).sort((p, q) => q[0].localeCompare(p[0]));
  const rates = [1, 2, 3, 4, 5].map(n => L.filter(([, m]) => m.rate === n).length), rated = rates.reduce((s, x) => s + x, 0);
  const avgRate = rated ? (rates.reduce((s, x, i) => s + x * (i + 1), 0) / rated) : 0;

  // 최근 12개월 다 본 작품 수 (다 본 날 기준)
  const now = new Date(), months = [];
  for (let i = 11; i >= 0; i--) { const d = new Date(now.getFullYear(), now.getMonth() - i, 1); months.push([`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`, d.getMonth() + 1, 0]); }
  watched.forEach(([, m]) => { const mm = (m.end || '').slice(0, 7); const x = months.find(z => z[0] === mm); if (x) x[2]++; });
  const mmax = Math.max(1, ...months.map(x => x[2]));

  // 보는 중 진행률
  const prog = watching.map(([w, m]) => total(w) ? m.ep / total(w) : null).filter(x => x != null);
  const avgProg = prog.length ? prog.reduce((s, x) => s + x, 0) / prog.length : null;

  const one = (title, rows, max, cls) => rows.length ? `<div class="stbox"><h2>${title}</h2><div class="hbars">${rows.map(([k, n]) => hbarRow(esc(k), [[cls, n]], max, n)).join('')}</div></div>` : '';
  let h = `<div class="stbox"><h2>내 기록</h2><div class="kpis">
      <div class="kpi"><div class="lb"><span class="dot w"></span>봤음</div><div class="v">${fmtN(watched.length)}</div></div>
      <div class="kpi"><div class="lb"><span class="dot g"></span>보는 중</div><div class="v">${fmtN(watching.length)}</div></div>
      <div class="kpi"><div class="lb"><span class="dot i"></span>관심</div><div class="v">${fmtN(want.length)}</div></div></div>
      ${venn(a, ab, b, bc, c)}
      <p class="stnote">보는 중과 봤음은 동시에 될 수 없어서, 관심을 사이에 두고 두 원이 떨어져 있습니다.</p></div>`;
  h += `<div class="stbox"><h2>본 양</h2><div class="big3">
      <div class="row3"><span class="k">본 화수</span><span class="v">${fmtN(eps)}<small>화</small></span></div>
      <div class="row3"><span class="k">일·시간·분</span><span class="v">${fmtDHM(min)}</span></div>
      <div class="row3"><span class="k">시간·분</span><span class="v">${fmtHM(min)}</span></div>
      <div class="row3"><span class="k">분</span><span class="v">${fmtN(Math.round(min))}<small>분</small></span></div></div>
      <p class="stnote">${reEps ? `다시 본 ${fmtN(reEps)}화를 포함합니다. ` : ''}${guessed ? `1화 길이를 모르는 ${fmtN(guessed)}편은 형식별 평균(TV 24분, 극장판 100분 등)으로 어림했습니다.` : ''}</p></div>`;
  h += `<div class="stbox"><h2>방영 시기별</h2>
      <div class="stseg" id="stBy"><button data-by="q" class="${statsBy === 'q' ? 'on' : ''}">분기별</button><button data-by="y" class="${statsBy === 'y' ? 'on' : ''}">연도별</button></div>
      <div class="legend3"><span><i class="dot w"></i>봤음</span><span><i class="dot g"></i>보는 중</span><span><i class="dot i"></i>관심만</span></div>
      <div class="hbars tight">${G.map(([k, g]) => hbarRow(esc(k), [['w', g.w], ['g', g.g], ['i', g.i]], gmax, g.w + g.g + g.i)).join('')}</div></div>`;
  h += `<div class="stbox"><h2>최근 12개월 다 본 작품</h2><div class="vbars">${months.map(([, mo, n]) => `<div class="c"><em>${n || ''}</em><b style="height:${(n / mmax * 100).toFixed(1)}%;${n ? '' : 'min-height:2px;opacity:.25'}"></b><span>${mo}월</span></div>`).join('')}</div>
      <p class="stnote">다 본 날을 기준으로 셉니다.</p></div>`;
  if (rated) h += `<div class="stbox"><h2>별점<span class="pill">평균 ${avgRate.toFixed(1)}</span></h2><div class="hbars">${rates.map((n, i) => hbarRow('★'.repeat(i + 1), [['g', n]], Math.max(...rates), n)).reverse().join('')}</div></div>`;
  if (avgProg != null) h += `<div class="stbox"><h2>보는 중 진행률<span class="pill">평균 ${Math.round(avgProg * 100)}%</span></h2><div class="hbars">${watching.filter(([w]) => total(w)).sort((p, q) => q[1].ep / total(q[0]) - p[1].ep / total(p[0])).slice(0, 8).map(([w, m]) => hbarRow(esc(title(w).length > 12 ? title(w).slice(0, 12) + '…' : title(w)), [['g', m.ep]], total(w), m.ep).replace(`<span class="num">${fmtN(m.ep)}</span>`, `<span class="num">${m.ep}/${total(w)}</span>`)).join('')}</div></div>`;
  h += one('형식별 (봤음)', byType, Math.max(1, ...byType.map(x => x[1])), 'w');
  h += one('방영 연대별 (봤음)', byDecade, Math.max(1, ...byDecade.map(x => x[1])), 'w');
  h += one('많이 본 장르·태그', byTag, Math.max(1, ...byTag.map(x => x[1])), 'w');
  h += one('많이 본 제작사', byStudio, Math.max(1, ...byStudio.map(x => x[1])), 'w');
  $('#stats').innerHTML = h;
  $('#stBy').onclick = e => { const b = e.target.closest('[data-by]'); if (!b) return; statsBy = b.dataset.by; renderStats(); };
}

/* ---------- 연도·분기 고르기 ---------- */
let pk = null;                      // {y: 고른 연도}
function seasonCounts(){
  const c = new Map();              // 연도 → [전체, 1분기, 2분기, 3분기, 4분기]
  for (const w of W) { if (!w.y) continue; const a = c.get(w.y) || [0, 0, 0, 0, 0]; a[0]++; if (w.q) a[w.q]++; c.set(w.y, a); }
  return c;
}
function openPicker(){
  pk = {y: S.y, c: seasonCounts()};
  $('#picker').hidden = false; document.body.style.overflow = 'hidden';
  drawPicker(true);
}
function closePicker(){ $('#picker').hidden = true; if ($('#sheet').hidden) document.body.style.overflow = ''; pk = null; }
function drawPicker(scroll){
  const c = pk.c, a = c.get(pk.y) || [0, 0, 0, 0, 0];
  $('#pkQ').innerHTML = [1, 2, 3, 4].map(q => `<button class="qb ${pk.y === S.y && q === S.qq ? 'on' : ''}" data-pq="${q}" ${a[q] ? '' : 'disabled'}><b>${QL[q]}</b><small>${QM[q]}</small><span class="pill">${fmtN(a[q])}</span></button>`).join('');
  const years = [...c.keys()].sort((x, y) => y - x), dec = new Map();
  years.forEach(y => { const d = Math.floor(y / 10) * 10; if (!dec.has(d)) dec.set(d, []); dec.get(d).push(y); });
  $('#pkY').innerHTML = [...dec].map(([d, ys]) => `<div class="pkdec">${d}년대<span class="pill">${fmtN(ys.reduce((s, y) => s + c.get(y)[0], 0))}</span></div><div class="pkgrid">${
    ys.map(y => `<button class="yb ${y === pk.y ? 'on' : ''}" data-py="${y}">${y}<span class="pill">${fmtN(c.get(y)[0])}</span></button>`).join('')}</div>`).join('');
  if (scroll) { const b = $('#pkY').querySelector('.yb.on'); if (b) $('#pkY').scrollTop = b.offsetTop - $('#pkY').clientHeight / 2; }
}
document.addEventListener('click', e => {
  if ($('#picker').hidden) return;
  if (e.target.closest('[data-pclose]')) { closePicker(); return; }
  const yb = e.target.closest('[data-py]');
  if (yb) { pk.y = +yb.dataset.py; drawPicker(false); return; }
  const qb = e.target.closest('[data-pq]');
  if (qb && !qb.disabled) { S.y = pk.y; S.qq = +qb.dataset.pq; S.shown = PAGE; closePicker(); render(); window.scrollTo(0, 0); }
});
document.addEventListener('keydown', e => { if (e.key === 'Escape' && !$('#picker').hidden) closePicker(); });

function onChange(e){
  const el = e.target.closest('[data-field]'); if (!el) return;
  const m = M(el.dataset.k); m[el.dataset.field] = el.value || undefined; if (!el.value) delete m[el.dataset.field]; save();
}
function setEp(k, n){
  const w = BYK.get(k), m = M(k), t = total(w);
  n = Math.max(0, t ? Math.min(n, t) : n);
  m.ep = n || undefined; if (!n) delete m.ep;
  if (n > 0 && !m.start) m.start = today();
  if (t && n >= t) { m.w = 1; if (!m.end) m.end = today(); }
  save(); refresh(k);
}
function refresh(k){
  const m = marks[k] || {}, w = BYK.get(k);
  document.querySelectorAll(`[data-k="${CSS.escape(k)}"]`).forEach(el => {
    const a = el.dataset.act;
    if (a === 'w' || a === 'i') el.classList.toggle('on', !!m[a]);
    if (a === 'epset') { const on = (m.ep || 0) >= +el.dataset.no; el.classList.toggle('on', on); el.setAttribute('aria-pressed', on); }
    if (a === 'rate') el.classList.toggle('on', (m.rate || 0) >= +el.dataset.n);
    if (el.dataset.out === 'ep') el.innerHTML = progText(w);
    if (el.dataset.out === 're') el.textContent = (m.re || 0) + '회';
    if (el.dataset.field === 'start' || el.dataset.field === 'end') el.value = m[el.dataset.field] || '';
    if (el.classList.contains('badges')) el.innerHTML = badges(w);
  });
}

/* ---------- 목록 ---------- */
function baseList(){
  let L;
  if (S.q) { const q = norm(S.q); L = W.filter(w => w.n.includes(q)); }
  else if (S.tab === 'season') L = W.filter(w => w.y === S.y && w.q === S.qq);
  else L = W;
  if (S.tab === 'watching') L = L.filter(w => marks[w.k]?.ep && !marks[w.k]?.w);
  if (S.tab === 'watched') L = L.filter(w => marks[w.k]?.w);
  if (S.tab === 'want') L = L.filter(w => marks[w.k]?.i);
  return L;
}
const EMPTY = {
  watching: '아직 보는 중인 작품이 없습니다. 작품 카드의 + 버튼으로 본 회차를 늘리면 여기에 모입니다.',
  watched: '아직 봤음으로 체크한 작품이 없습니다. 작품 카드의 봤음 버튼을 누르면 여기에 모입니다.',
  want: '아직 관심으로 체크한 작품이 없습니다. 작품 카드의 관심 버튼을 누르면 여기에 모입니다.',
  all: '검색 결과가 없습니다. 다른 언어의 제목으로도 찾아보세요.', stats: '검색 결과가 없습니다. 다른 언어의 제목으로도 찾아보세요.', settings: '검색 결과가 없습니다. 다른 언어의 제목으로도 찾아보세요.', season: '검색 결과가 없습니다. 다른 언어의 제목으로도 찾아보세요.'
};
function render(){
  const settingsMode = S.tab === 'settings' && !S.q, statsMode = S.tab === 'stats' && !S.q;
  $('#settings').hidden = !settingsMode;
  $('#stats').hidden = !statsMode;
  ['#filters', '#list', '#more'].forEach(s => $(s).hidden = settingsMode || statsMode);
  if (statsMode) { $('#seasonBar').hidden = true; renderStats(); return; }
  if (settingsMode) {
    $('#seasonBar').hidden = true;
    document.querySelectorAll('#setLang [data-lang]').forEach(b => b.classList.toggle('on', b.dataset.lang === S.lang));
    document.querySelectorAll('#setTheme [data-theme-set]').forEach(b => b.classList.toggle('on', b.dataset.themeSet === (S.theme || 'system')));
    return;
  }
  const seasonMode = S.tab === 'season' && !S.q;
  $('#seasonBar').hidden = !seasonMode;
  $('#qYear').textContent = S.y + '년';
  $('#qLabel').textContent = `${QL[S.qq]} (${QM[S.qq]})`;
  const base = baseList(), tc = {}, lc = {};
  base.forEach(w => { tc[w.ty] = (tc[w.ty] || 0) + 1; if (w.lk) lc[w.lk] = (lc[w.lk] || 0) + 1; });
  $('#filters').innerHTML =
    TYPE_ORDER.filter(t => tc[t]).map(t => `<button class="chip ${S.types.has(t) ? 'on' : ''}" data-act="type" data-v="${t}">${TYPE[t]}<span class="pill">${fmtN(tc[t])}</span></button>`).join('') +
    Object.keys(LEN).filter(l => lc[l]).map(l => `<button class="chip ${S.lens.has(l) ? 'on' : ''}" data-act="len" data-v="${l}">${LEN[l]}<span class="pill">${fmtN(lc[l])}</span></button>`).join('');
  let L = base.filter(w => (!S.types.size || S.types.has(w.ty)) && (!S.lens.size || S.lens.has(w.lk)));
  let html = S.q ? idxResults(S.q, 'people', '인물', 'person', 'p') + idxResults(S.q, 'studios', '제작사', 'studio', 's') : '';
  const hasIdx = html !== '';
  if (seasonMode) {
    TYPE_ORDER.forEach(t => { const arr = L.filter(w => w.ty === t).sort((a, b) => title(a).localeCompare(title(b), 'ko')); if (arr.length) html += group(TYPE[t], arr, arr.length); });
    if (!L.length) html += `<p class="empty">이 분기에 해당하는 작품이 없습니다. 위의 화살표로 다른 분기를 보세요.</p>`;
    $('#more').innerHTML = '';
  } else {
    L = L.slice().sort((a, b) => (b.y || 0) - (a.y || 0) || (b.q || 0) - (a.q || 0) || title(a).localeCompare(title(b), 'ko'));
    const gk = w => w.y ? (w.q ? `${w.y}년 ${QL[w.q]}` : `${w.y}년`) : '연도 미상';
    const full = {}; L.forEach(w => full[gk(w)] = (full[gk(w)] || 0) + 1);
    const by = new Map(); L.slice(0, S.shown).forEach(w => { if (!by.has(gk(w))) by.set(gk(w), []); by.get(gk(w)).push(w); });
    by.forEach((arr, key) => html += group(key, arr, full[key]));
    if (!L.length && !hasIdx) html += `<p class="empty">${EMPTY[S.tab]}</p>`;
    $('#more').innerHTML = L.length > S.shown ? `<button data-act="more">더 보기 <span class="pill">${fmtN(L.length - S.shown)}</span></button>` : '';
  }
  $('#list').innerHTML = html;
}
function group(name, arr, count){ return `<section class="group"><div class="ghead"><h2>${esc(name)}</h2><span class="pill">${fmtN(count)}</span></div><div class="grid">${arr.map(card).join('')}</div></section>`; }
function badges(w){ const m = marks[w.k] || {}; return (m.w ? '<span class="badge w">봤음</span>' : '') + (m.i ? '<span class="badge i">관심</span>' : '') + (m.ep && !m.w ? '<span class="badge">보는 중</span>' : ''); }
function fmtDur(sec){ return sec < 60 ? `${sec}초` : sec < 3600 ? `${Math.round(sec / 60)}분` : `${Math.floor(sec / 3600)}시간 ${Math.round(sec % 3600 / 60)}분`; }
function infoPills(w){
  const p = [`<span class="pill">${TYPE[w.ty]}</span>`];
  if (w.e) p.push(`<span class="pill">${w.e}화</span>`);
  if (w.d) p.push(`<span class="pill">${fmtDur(w.d)}</span>`);
  const sl = statusLabel(w); if (sl) p.push(`<span class="pill">${sl}</span>`);
  return p.join('');
}
function progText(w){ const m = marks[w.k] || {}, t = total(w); return `${m.ep || 0}${t ? ` <small>/ ${t}화</small>` : '<small>화</small>'}`; }
function progCtl(w){ return `<div class="prog"><button class="step" data-act="ep-" data-k="${esc(w.k)}" aria-label="본 회차 줄이기">−</button><span class="now" data-k="${esc(w.k)}" data-out="ep">${progText(w)}</span><button class="step" data-act="ep+" data-k="${esc(w.k)}" aria-label="본 회차 늘리기">+</button></div>`; }
function card(w){
  const m = marks[w.k] || {}, src = img(w), k = esc(w.k);
  return `<div class="card">
    <button class="kv" data-act="open" data-k="${k}" aria-label="${esc(title(w))} 자세히"><span class="nokv">키 비주얼 없음</span>${src ? `<img loading="lazy" src="${esc(src)}" ${srcset(w) ? `srcset="${esc(srcset(w))}" sizes="(max-width:420px) 46vw, 180px"` : ''} alt="" referrerpolicy="no-referrer" onerror="this.remove()">` : ''}<span class="badges" data-k="${k}">${badges(w)}</span></button>
    <div class="meta"><div class="t1 ${S.lang === 'ja' ? 'ja' : ''}" data-act="open" data-k="${k}">${esc(title(w))}</div><div class="t2">${esc(subtitle(w))}</div><div class="pills">${infoPills(w)}</div></div>
    ${progCtl(w)}
    <div class="acts"><button class="tg w ${m.w ? 'on' : ''}" data-act="w" data-k="${k}">봤음</button><button class="tg i ${m.i ? 'on' : ''}" data-act="i" data-k="${k}">관심</button></div>
  </div>`;
}
function idxResults(q, kind, label, act, attr){
  const I = IDX[kind]; if (!I) return '';
  const n = norm(q), hits = [];
  for (const [id, names] of Object.entries(I)) { if (names.some(x => norm(x).includes(n))) { hits.push([id, names]); if (hits.length >= 30) break; } }
  if (!hits.length) return '';
  return `<section class="group"><div class="ghead"><h2>${label}</h2><span class="pill">${hits.length >= 30 ? '30+' : hits.length}</span></div><div class="rows">${hits.map(([id, names]) =>
    `<div class="row"><div class="grow"><button class="link" data-act="${act}" data-${attr}="${esc(id)}">${esc(names[0])}</button><div class="s">${esc(names.slice(1).join(' / '))}</div></div></div>`).join('')}</div></section>`;
}

/* ---------- 이름 표시 (한국어 + 원어) ---------- */
function nm(n, opts = {}){
  if (!n) return '';
  if (typeof n === 'string') return esc(n);
  if (n.auto) usedAuto = true;
  const main = S.lang === 'ja' && n.ja ? n.ja : (n.ko || n.ja || n.en);
  const sub = S.lang === 'ja' ? n.ko : (n.ja && n.ja !== n.ko ? n.ja : '');
  const cls = n.auto && main === n.ko ? 'auto' : '';
  return `<span class="${cls}">${esc(main)}</span>${sub && !opts.short ? ` <span class="s ${S.lang === 'ja' && n.auto ? 'auto' : ''}">${esc(sub)}</span>` : ''}`;
}
const pLink = p => `<button class="link" data-act="person" data-p="${esc(p.pid)}">${nm(p, {short:true})}</button>`;
const sLink = s => `<button class="link" data-act="studio" data-s="${esc(s.sid)}">${nm(s, {short:true})}</button>`;
const sec = (t, body, count) => `<div class="sec"><h3>${t}${count ? `<span class="pill">${fmtN(count)}</span>` : ''}</h3>${body}</div>`;
const nodata = t => `<p class="nodata">${t}</p>`;
const dl = rows => `<dl class="info">${rows.filter(r => r[1]).map(([a, b]) => `<dt>${a}</dt><dd>${b}</dd>`).join('')}</dl>`;

/* ---------- 상세 시트 ---------- */
function route(){
  const m = location.hash.match(/^#\/(w|p|s)\/(.+)$/);
  if (!m) { closeSheet(true); return; }
  const id = decodeURIComponent(m[2]);
  ({w:openWork, p:openPerson, s:openStudio})[m[1]](id);
}
function closeSheet(fromRoute){
  $('#sheet').hidden = true; document.body.style.overflow = '';
  if (!fromRoute && location.hash) history.pushState('', '', location.pathname + location.search);
  render();
}
function showSheet(html){
  $('#sheetBody').innerHTML = `<button class="close" data-close aria-label="닫기">✕</button>` + html + (usedAuto ? `<p class="legend"><span class="auto">점선 밑줄</span>은 공식 한국어 표기를 찾지 못해 자동으로 옮긴 이름이라 읽는 법이 틀릴 수 있습니다.</p>` : '');
  $('#sheet').hidden = false; document.body.style.overflow = 'hidden';
  $('#sheetBody').focus({preventScroll:true});
}
async function openWork(k){
  const w = BYK.get(k); if (!w) return;
  usedAuto = false; showSheet(workHTML(w, null)); $('#sheetBody').scrollTop = 0;
  const d = await item('detail', k);
  if (d && location.hash === '#/w/' + encodeURIComponent(k)) { const st = $('#sheetBody').scrollTop; usedAuto = false; showSheet(workHTML(w, d)); $('#sheetBody').scrollTop = st; }
}

function workHTML(w, d){
  const m = marks[w.k] || {}, src = img(w, true), k = esc(w.k), t = d?.titles || {};
  const titles = [['한국어', t.ko || w.ko], ['日本語', t.ja || w.ja], ['English', t.en || w.en], ['Romaji', w.r]].filter(x => x[1]);
  let h = `<div class="shead">${src ? `<img src="${esc(src)}" alt="" referrerpolicy="no-referrer" onerror="this.replaceWith(Object.assign(document.createElement('div'),{className:'ph'}))">` : '<div class="ph"></div>'}
    <div><h2 class="${S.lang === 'ja' ? 'ja' : ''}">${esc(title(w))}</h2><dl class="tl">${titles.map(([l, v]) => `<dt>${l}</dt><dd class="${l === '日本語' ? 'ja' : ''}">${esc(v)}</dd>`).join('')}</dl></div></div>
    <div class="sacts"><button class="tg w ${m.w ? 'on' : ''}" data-act="w" data-k="${k}">봤음</button><button class="tg i ${m.i ? 'on' : ''}" data-act="i" data-k="${k}">관심</button></div>
    <div class="sprog">${progCtl(w)}</div>`;

  // 내 기록
  h += sec('내 기록', `<dl class="mylog">
    <dt>별점</dt><dd><div class="stars">${[1,2,3,4,5].map(n => `<button class="${(m.rate || 0) >= n ? 'on' : ''}" data-act="rate" data-n="${n}" data-k="${k}" aria-label="별 ${n}개">★</button>`).join('')}</div></dd>
    <dt>시작한 날</dt><dd><input type="date" data-field="start" data-k="${k}" value="${esc(m.start || '')}"></dd>
    <dt>다 본 날</dt><dd><input type="date" data-field="end" data-k="${k}" value="${esc(m.end || '')}"></dd>
    <dt>다시 본 횟수</dt><dd><span class="mini"><button data-act="re-" data-k="${k}" aria-label="줄이기">−</button><span data-k="${k}" data-out="re">${m.re || 0}회</span><button data-act="re+" data-k="${k}" aria-label="늘리기">+</button></span></dd>
    <dt>메모</dt><dd><textarea data-field="memo" data-k="${k}" rows="3">${esc(m.memo || '')}</textarea></dd></dl>`);

  // 기본 정보
  const author = (d?.staff || []).find(s => s.role === '원작');
  const stuMain = d?.studios?.main?.length ? d.studios.main.map(sLink).join(', ') : (w.stu || []).map(i => { const s = STUDIOS[i]; return `<button class="link" data-act="studio" data-s="${esc(s[3])}">${nm({ko:s[1], auto:s[2]}, {short:true})}</button>`; }).join(', ');
  const tags = [...new Set([...(d?.genres || []), ...(d?.tags?.length ? d.tags : (w.tags || []).map(i => TAGS[i]))])].slice(0, 14);
  h += sec('기본 정보', dl([
    ['방영 시기', w.y ? `${w.y}년${w.q ? ` ${QL[w.q]} (${QM[w.q]})` : ''}` : '미상'],
    ['형식', TYPE[w.ty] + (w.net ? ' (넷플릭스 독점)' : '')],
    ['화수', w.e ? w.e + '화' : '미상'],
    ['1화 길이', w.d ? fmtDur(w.d) + (w.lk ? ` (${LEN[w.lk].split(' ')[0]})` : '') : '미상'],
    ['원작', d?.source ? esc(d.source) + (author ? ' · ' + author.people.map(pLink).join(', ') : '') : ''],
    ['제작', stuMain || '미상'],
    ['평점', d?.averageScore ? `${d.averageScore}점 <span class="s">(AniList 100점 만점)</span>` : ''],
    ['인기', d?.popularity ? `${fmtN(d.popularity)}명이 목록에 담음` : ''],
    ['연령 등급', d?.adult ? '성인' : ''],
    ['장르·태그', tags.length ? `<div class="pills">${tags.map(x => `<span class="pill">${esc(x)}</span>`).join('')}</div>` : ''],
  ]));

  // 링크
  const links = [...(d?.links || []).map(l => [LINK_KO[l.site] || l.site, l.url]), ...(d?.pv ? [['PV 영상', d.pv]] : []), ...(!d?.links && w.site ? [['공식 사이트', w.site]] : [])];
  if (links.length) h += sec('공식 링크', `<div class="rows">${links.map(([n, u]) => `<div class="row"><a class="link" href="${esc(u)}" target="_blank" rel="noopener">${esc(n)}</a></div>`).join('')}</div>`);

  // 제작사
  const st = d?.studios;
  if (st && (st.coop.length || st.committee.length || st.main.length))
    h += sec('제작사', dl([['애니메이션 제작', st.main.map(sLink).join(', ')], ['협력 스튜디오', st.coop.map(s => `${sLink(s)} <span class="s">${esc(s.eps.join(', '))}화</span>`).join('<br>')], ['제작위원회·참여사', st.committee.map(sLink).join(', ')]]));

  // 스태프
  const staff = (d?.staff || []).filter(s => s.role !== '원작');
  h += sec('스태프', staff.length ? dl(staff.map(s => [esc(s.role), s.people.map(pLink).join(', ')])) : nodata('스태프 정보가 아직 수집되지 않았습니다.'), staff.length);

  // 방송
  const bro = d?.broadcast || [];
  h += sec('일본 방송', bro.length ? `<div class="rows">${bro.map(b => `<div class="row"><div class="grow"><b>${nm(b.station)}</b><div class="s">${esc([b.start, b.weekday, b.time].filter(Boolean).join(' '))}</div></div></div>`).join('')}</div>`
    + (d.rebroadcast?.length ? `<p class="s" style="margin:10px 0 0"><b>재방송</b> ${d.rebroadcast.map(b => `${nm(b.station, {short:true})} ${esc(b.start)}`).join(', ')}</p>` : '')
    + (d.notes?.length ? `<p class="s" style="margin:6px 0 0"><b>휴방·연기</b><br>${d.notes.map(esc).join('<br>')}</p>` : '') : nodata('방송국·시간 정보가 아직 수집되지 않았습니다.'));
  if (d?.korea) h += sec('한국 방영', `<p class="kr">${esc(d.korea)}</p>`);

  // OTT
  const VODN = {danime:{ko:'d애니메 스토어', ja:'dアニメストア'}, unext:'U-NEXT', abema:'ABEMA', netflix:'넷플릭스', prime:'프라임 비디오', nicovideo:{ko:'니코니코', ja:'ニコニコ'}, disneyplus:'디즈니+', youtube:'유튜브', crunchyroll:'크런치롤'};
  const ott = d?.ott || (w.vod ? {JP: w.vod.JP.map(n => ({name: VODN[n] || n})), US: w.vod.US.map(n => ({name: VODN[n] || n}))} : null);
  const on = p => { const t = typeof p.name === 'string' ? esc(p.name) : nm(p.name, {short:true}); return p.url ? `<a class="link" href="${esc(p.url)}" target="_blank" rel="noopener">${t}</a>` : t; };
  h += sec('지금 볼 수 있는 곳', ott ? dl([['한국', (ott.KR || []).map(on).join(', ') || '정보 없음'], ['일본', (ott.JP || []).map(on).join(', ') || '정보 없음'], ['미국', (ott.US || []).map(on).join(', ') || '정보 없음']]) + (d?.ott_updated ? `<p class="s" style="margin:8px 0 0">${esc(d.ott_updated)} 기준</p>` : '') : nodata('OTT 정보가 아직 수집되지 않았습니다.'));

  // 회차
  // 시즌을 이어서 세는 작품(예: 3기가 49~60화)은 화면에는 이어 센 번호(no), 시청 기록에는 이 작품 안 순서(i)를 씀
  const off = d?.ep_offset || 0, idx = e => e.i ?? (parseInt(e.no, 10) - off);
  const have = new Map((d?.episodes || []).map(e => [String(idx(e)), {...e, i: idx(e)}]));
  for (let i = 1; i <= Math.min(total(w), 3000); i++) if (!have.has(String(i))) have.set(String(i), {no: String(off + i), i, title: {}});
  const eps = [...have.values()].sort((a, b) => (Number.isFinite(a.i) ? a.i : 1e9) - (Number.isFinite(b.i) ? b.i : 1e9));
  if (eps.length) h += sec('회차', `<div>${eps.map(e => epRow(w, e)).join('')}</div>`, eps.length);

  // 캐릭터
  const ch = d?.characters || [];
  h += sec('캐릭터·성우', ch.length ? `<div class="rows">${ch.map(c => `<div class="row">${c.img ? `<img class="thumb" loading="lazy" src="${esc(c.img)}" alt="" referrerpolicy="no-referrer">` : ''}<div class="grow"><b>${nm(c.name)}</b> ${ROLE[c.role] ? `<span class="pill">${ROLE[c.role]}</span>` : ''}<div class="s">${(c.cast || []).map(v => pLink(v) + (v.lang && v.lang !== 'ja' ? ` (${v.lang === 'ko' ? '한국어 더빙' : '영어 더빙'})` : '')).join('<br>')}</div></div></div>`).join('')}</div>` : nodata('캐릭터와 성우 정보가 아직 수집되지 않았습니다.'), ch.length);

  // 주제가
  const sg = d?.songs || [];
  h += sec('주제가·삽입곡', sg.length ? `<div class="rows">${sg.map(s => `<div class="row"><span class="pill">${SONG[s.kind] || esc(s.kind)}${s.seq ? ' ' + s.seq : ''}</span><div class="grow"><b class="ja">${esc(s.title)}</b>${s.eps ? `<div class="s">${esc(s.eps)}화</div>` : ''}<div class="s">${CREDIT_ORDER.map(r => { const cs = (s.credits || []).filter(c => c.role === r); return cs.length ? `${CREDIT_KO[r]} ${cs.map(pLink).join(', ')}` : ''; }).filter(Boolean).join('<br>')}</div></div></div>`).join('')}</div>` : nodata('주제가 정보가 아직 수집되지 않았습니다.'), sg.length);

  if (d?.albums?.length) h += sec('음반', `<div class="rows">${d.albums.map(a => `<div class="row"><span class="pill">${esc(a.kind)}</span><div class="grow"><b class="ja">${esc(a.title)}</b><div class="s">${esc([a.date, (a.artists || []).join(', ')].filter(Boolean).join(' '))}</div>${a.links?.length ? `<div class="s">${a.links.map(l => `<a class="link" href="${esc(l.url)}" target="_blank" rel="noopener">${esc({spotify:'스포티파이', apple:'애플 뮤직', youtube:'유튜브 뮤직', amazon:'아마존 뮤직', line:'라인 뮤직', melon:'멜론'}[l.site] || l.site)}</a>`).join(' ')}</div>` : ''}</div></div>`).join('')}</div>`, d.albums.length);
  if (d?.box_office) h += sec('흥행 수입', `<p class="kr">${esc(d.box_office)}</p>`);
  if (d?.pilgrimage?.count) { const p = d.pilgrimage; h += sec('성지순례', `<p class="kr">${p.city ? nm(p.city, {short:true}) + ' 등 ' : ''}장소 ${fmtN(p.count)}곳 · <a class="link" href="${esc(p.map)}" target="_blank" rel="noopener">지도로 보기</a></p><div class="pts" style="margin-top:10px">${p.points.map(x => `<div class="pt">${x.image ? `<img loading="lazy" src="${esc(x.image)}" alt="" referrerpolicy="no-referrer">` : ''}${nm(x.name)}${x.ep ? ` <span class="s">${x.ep}화</span>` : ''}</div>`).join('')}</div>`, p.count); }

  // 관련 작품
  const rel = (d?.relations?.length ? d.relations : (w.rel || []).map(k => ({k}))).map(r => ({...r, w: BYK.get(r.k)})).filter(r => r.w).sort((a, b) => (a.w.y || 9999) - (b.w.y || 9999) || (a.w.q || 0) - (b.w.q || 0));
  h += sec('관련 작품', rel.length ? `<div class="rows">${rel.map(r => `<div class="row"><div class="grow"><button class="link" data-act="open" data-k="${esc(r.k)}">${esc(title(r.w))}</button><div class="s">${r.w.y || '연도 미상'}${r.w.q ? ' ' + QL[r.w.q] : ''} ${TYPE[r.w.ty]}${r.w.e ? ' ' + r.w.e + '화' : ''}</div></div>${r.type ? `<span class="pill">${RT[r.type] || esc(r.type)}</span>` : ''}</div>`).join('')}</div>` : nodata('연결된 작품이 없습니다.'), rel.length);

  const ext = [w.al && ['AniList', 'https://anilist.co/anime/' + w.al], w.mal && ['MyAnimeList', 'https://myanimelist.net/anime/' + w.mal], w.adb && ['AniDB', 'https://anidb.net/anime/' + w.adb], w.tmdb && ['TMDB', 'https://www.themoviedb.org/tv/' + w.tmdb], w.sy && ['쇼보이 캘린더', 'https://cal.syoboi.jp/tid/' + w.sy], w.an && ['Annict', 'https://annict.com/works/' + w.an], w.bgm && ['Bangumi', 'https://bgm.tv/subject/' + w.bgm]].filter(Boolean);
  h += sec('외부 링크', `<div class="rows">${ext.map(([n, u]) => `<div class="row"><a class="link" href="${u}" target="_blank" rel="noopener">${n}</a></div>`).join('')}</div>`);
  return h;
}
function epRow(w, e){
  const m = marks[w.k] || {}, n = Number.isFinite(e.i) && e.i > 0 ? e.i : parseInt(e.no, 10), seen = n && (m.ep || 0) >= n, t = e.title || {};
  const order = S.lang === 'ja' ? ['ja', 'ko', 'en'] : S.lang === 'en' ? ['en', 'ko', 'ja'] : ['ko', 'ja', 'en'];
  const tt = order.map(l => t[l]).filter(Boolean);
  const lines = [];
  if (tt.length > 1) lines.push(tt.slice(1).map(esc).join(' / '));
  const meta = [e.air, e.min && e.min + '분'].filter(Boolean).join(' ');
  if (meta || e.special) lines.push(esc(meta) + (e.special ? ' <span class="pill">2배 분량</span>' : ''));
  (e.staff || []).forEach(s => lines.push(`<b>${esc(s.role)}</b> ${s.people.map(pLink).join(', ')}`));
  if (e.studios?.length) lines.push(`<b>협력</b> ${e.studios.map(sLink).join(', ')}`);
  (e.songs || []).filter(s => s.special).forEach(s => lines.push(`<b>${s.kind === 'ED' ? '특수 엔딩' : s.kind === 'OP' ? '특수 오프닝' : '삽입곡'}</b> ${esc(s.title)}`));
  if (e.endcard) lines.push(`<b>엔드카드</b> ${pLink(e.endcard)}`);
  return `<div class="ep">${n ? `<button class="chk ${seen ? 'on' : ''}" data-act="epset" data-no="${n}" data-k="${esc(w.k)}" aria-pressed="${!!seen}" aria-label="${esc(e.no)}화까지 봤음">✓</button>` : ''}<div class="grow"><span class="no">${esc(e.no)}화</span>${esc(tt[0] || '')}${lines.length ? `<div class="s">${lines.join('<br>')}</div>` : ''}</div></div>`;
}

async function openPerson(id){
  usedAuto = false; showSheet(sec('불러오는 중', ''));
  const p = await item('people', id);
  usedAuto = false;
  if (!p) { showSheet(sec('인물 정보 없음', nodata('이 인물의 출연·참여 정보가 아직 수집되지 않았습니다.'))); return; }
  const n = p.name, pf = p.profile || {};
  let h = `<div class="shead" style="grid-template-columns:${pf.image ? '84px ' : ''}1fr">${pf.image ? `<img class="pf" src="${esc(pf.image)}" alt="" referrerpolicy="no-referrer">` : ''}<div><h2>${nm({...n, ja: null})}</h2><div class="s" style="color:var(--sub)">${esc([n.ja, n.en].filter(Boolean).join(' / '))}</div></div></div>`;
  const info = [['생년월일', pf.birth], ['출신지', pf.hometown], ['소속사', pf.agency], ['활동 분야', (pf.jobs || []).join(', ')], ['활동 연도', (pf.years || []).join(' ~ ')]].filter(x => x[1]).map(([a, b]) => [a, esc(b)]);
  if (info.length) h += sec('프로필', dl(info));
  const W_ = x => ({...x, w: BYK.get(x.k)}), byYear = (a, b) => (b.w.y || 0) - (a.w.y || 0) || (b.w.q || 0) - (a.w.q || 0);
  const roles = (p.roles || []).map(W_).filter(r => r.w).sort(byYear);
  if (roles.length) h += sec('출연 배역', `<div class="rows">${roles.map(r => `<div class="row"><div class="grow"><button class="link" data-act="open" data-k="${esc(r.k)}">${esc(title(r.w))}</button><div class="s">${nm(r.char, {short:true})}${ROLE[r.role] ? ' · ' + ROLE[r.role] : ''}${r.lang && r.lang !== 'ja' ? ` · ${r.lang === 'ko' ? '한국어 더빙' : '영어 더빙'}` : ''}</div></div><span class="pill">${r.w.y || '?'}</span></div>`).join('')}</div>`, roles.length);
  const staff = new Map();
  (p.staff || []).forEach(s => { if (!BYK.get(s.k)) return; const g = staff.get(s.k) || staff.set(s.k, {k: s.k, w: BYK.get(s.k), roles: new Map()}).get(s.k); const r = g.roles.get(s.role) || new Set(); (s.eps || []).forEach(x => r.add(x)); g.roles.set(s.role, r); });
  const st = [...staff.values()].sort(byYear);
  if (st.length) h += sec('스태프 참여', `<div class="rows">${st.map(g => `<div class="row"><div class="grow"><button class="link" data-act="open" data-k="${esc(g.k)}">${esc(title(g.w))}</button><div class="s">${[...g.roles].map(([r, e]) => esc(r) + (e.size ? ` (${[...e].sort((a, b) => a - b).join(', ')}화)` : '')).join(' · ')}</div></div><span class="pill">${g.w.y || '?'}</span></div>`).join('')}</div>`, st.length);
  const songs = (p.songs || []).map(W_).filter(s => s.w).sort(byYear);
  if (songs.length) h += sec('참여 곡', `<div class="rows">${songs.map(s => `<div class="row"><div class="grow"><b class="ja">${esc(s.title)}</b><div class="s"><button class="link" data-act="open" data-k="${esc(s.k)}">${esc(title(s.w))}</button> ${SONG[s.kind] || esc(s.kind)} · ${(s.roles || []).map(r => CREDIT_KO[r] || r).join(', ')}</div></div></div>`).join('')}</div>`, songs.length);
  if (!roles.length && !st.length && !songs.length) h += sec('', nodata('출연·참여 정보가 없습니다.'));
  showSheet(h); $('#sheetBody').scrollTop = 0;
}

async function openStudio(id){
  usedAuto = false; showSheet(sec('불러오는 중', ''));
  const s = await item('studios', id);
  usedAuto = false;
  if (!s) { showSheet(sec('제작사 정보 없음', nodata('이 제작사의 정보가 아직 수집되지 않았습니다.'))); return; }
  const n = s.name;
  let h = `<div class="shead" style="grid-template-columns:1fr"><div><h2>${nm({...n, ja: null})}</h2><div class="s" style="color:var(--sub)">${esc([n.ja, n.en].filter(Boolean).join(' / '))}</div></div></div>`;
  if (s.founded) h += sec('정보', dl([['설립', esc(s.founded) + '년']]));
  for (const as of ['main', 'coop', 'committee']) {
    const L = s.works.filter(x => x.as === as).map(x => ({...x, w: BYK.get(x.k)})).filter(x => x.w).sort((a, b) => (b.w.y || 0) - (a.w.y || 0));
    if (L.length) h += sec(STUDIO_AS[as], `<div class="rows">${L.map(x => `<div class="row"><div class="grow"><button class="link" data-act="open" data-k="${esc(x.k)}">${esc(title(x.w))}</button>${x.eps?.length ? `<div class="s">${esc(x.eps.join(', '))}화</div>` : ''}</div><span class="pill">${x.w.y || '?'}</span></div>`).join('')}</div>`, L.length);
  }
  showSheet(h); $('#sheetBody').scrollTop = 0;
}

boot();
