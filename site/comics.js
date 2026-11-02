/* 다봤니 만화책: 알라딘 구매내역·장바구니를 북마클릿으로 가져와 시리즈별로 관리 (애니와 별개) */
const CM = store.get('comics', {v: 1, items: {}, series: {}, carts: []});
CM.items ||= {}; CM.series ||= {}; CM.carts ||= [];
const CMS = {kind: store.get('cmKind', 'all'), view: store.get('cmView', 'all'), sort: store.get('cmSort', 'name'), cart: 0, guide: false};
const ALADIN = ['https://www.aladin.co.kr', 'https://m.aladin.co.kr'];
const BUY_URL = 'https://www.aladin.co.kr/m/mbest.aspx?BestType=OrderSave';
const CART_URL = 'https://www.aladin.co.kr/m/mbasket.aspx?start=moheader';
function cmSave(){ store.set('comics', CM); if (typeof syncSoon === 'function') syncSoon(); }

/* ---------- 제목에서 시리즈 이름과 권수 읽기 ---------- */
const KN1 = {'하나': 1, '둘': 2, '셋': 3, '넷': 4, '다섯': 5, '여섯': 6, '일곱': 7, '여덟': 8, '아홉': 9};
const KN10 = {'열': 10, '스물': 20, '서른': 30, '마흔': 40, '쉰': 50, '예순': 60, '일흔': 70, '여든': 80, '아흔': 90};
function korNum(w){
  let m = w.match(/^(열|스물|서른|마흔|쉰|예순|일흔|여든|아흔)?(하나|둘|셋|넷|다섯|여섯|일곱|여덟|아홉)?$/);
  if (!m || (!m[1] && !m[2])) return null;
  return (m[1] ? KN10[m[1]] : 0) + (m[2] ? KN1[m[2]] : 0);
}
function cleanTitle(t){
  return String(t || '').replace(/^\s*(\[[^\]]*\]\s*)+/, '')      // [eBook] [고화질] 같은 앞 표시
    .replace(/\s+-\s+.*$/, '')                                   // 「… 5 - 시프트코믹스」 뒤 부제·총서명
    .replace(/\s*\((?:[^()]*?(?:판|한정|특전|세트|부록|포함|에디션|edition)[^()]*)\)\s*$/i, '')   // (특장판) (한정판) …
    .trim();
}
function volOf(t){
  const c = cleanTitle(t);
  let m = c.match(/(?:제\s*)?(\d{1,3})\s*권$/) || c.match(/[\s.(]\s*(\d{1,3})\s*\)?$/) || c.match(/(\d{1,3})$/);
  if (m) return +m[1];
  m = c.match(/\s(\S+)$/); if (m) { const k = korNum(m[1]); if (k) return k; }
  return null;
}
function baseOf(t){
  let c = cleanTitle(t);
  c = c.replace(/\s*(?:제\s*)?\d{1,3}\s*권$/, '').replace(/[\s.(]\s*\d{1,3}\s*\)?$/, '').replace(/(\D)\d{1,3}$/, '$1');
  const m = c.match(/^(.*\S)\s(\S+)$/); if (m && korNum(m[2])) c = m[1];
  return c.trim() || cleanTitle(t);
}
const seriesKey = it => norm(baseOf(it.t));
// 빠진 권 표시: 이어지는 번호는 묶음 (1, 2, 3, 5 → 「1~3, 5」)
function ranges(a){ const out = []; for (let i = 0; i < a.length; i++) { let j = i; while (j + 1 < a.length && a[j + 1] === a[j] + 1) j++; out.push(j > i ? `${a[i]}~${a[j]}` : `${a[i]}`); i = j; } return out.join(', '); }

/* ---------- 시리즈 묶기 ---------- */
function seriesList(){
  const S_ = new Map();
  for (const it of Object.values(CM.items)) {
    if (!it.own) continue;
    const k = seriesKey(it); let s = S_.get(k);
    if (!s) S_.set(k, s = {key: k, name: baseOf(it.t), pub: it.pub || '', kind: it.kind, items: [], vols: new Set(), eb: false, date: '', buy: ''});
    s.items.push(it); if (it.vol) s.vols.add(it.vol); if (it.eb) s.eb = true;
    if ((it.date || '') > s.date) s.date = it.date || ''; if ((it.buy || '') > s.buy) s.buy = it.buy || '';
    if (it.kind === 'l') s.kind = 'l';
  }
  for (const s of S_.values()) {
    s.items.sort((a, b) => (a.vol || 0) - (b.vol || 0) || String(a.date).localeCompare(String(b.date)));
    s.max = Math.max(0, ...s.vols); s.gaps = [];
    for (let v = 1; v < s.max; v++) if (!s.vols.has(v)) s.gaps.push(v);
    const last = s.items[s.items.length - 1]; s.cover = last.cover; s.pub = last.pub || s.pub;
    const st = CM.series[s.key] || {}; s.read = st.read || 0; s.ack = st.ack === s.gaps.join(',');
  }
  return [...S_.values()];
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
function seg(name, cur, opts){ return `<div class="seg cmseg">${opts.map(([v, l]) => `<button data-cm="${name}" data-v="${v}" class="${cur === v ? 'on' : ''}">${t(l)}</button>`).join('')}</div>`; }
function renderBuy(q){
  let L = seriesList();
  const counts = {all: L.length, c: L.filter(s => s.kind !== 'l').length, l: L.filter(s => s.kind === 'l').length};
  if (CMS.kind !== 'all') L = L.filter(s => (CMS.kind === 'l') === (s.kind === 'l'));
  if (q) { const nq = norm(q); L = L.filter(s => norm(s.name + s.pub).includes(nq)); }
  L.sort(CMS.sort === 'date' ? (a, b) => b.date.localeCompare(a.date) || tcmpS(a, b) : tcmpS);
  let h = guideHTML('cbuy');
  if (!Object.keys(CM.items).length) return h + `<div class="stbox"><p class="stempty">${t('아직 가져온 구매내역이 없습니다.')}</p></div>`;
  h += `<div class="cmctl">
    <div class="frow"><span class="flab">${t('종류')}</span><div class="fscroll">${[['all', '전체'], ['c', '만화'], ['l', '라이트노벨']].map(([v, l]) => `<button class="chip ${CMS.kind === v ? 'on' : ''}" data-cm="kind" data-v="${v}">${t(l)}<span class="pill">${fmtN(counts[v])}</span></button>`).join('')}</div></div>
    <div class="cmrow">${seg('view', CMS.view, [['all', '전체'], ['pub', '출판사별']])}${seg('sort', CMS.sort, [['name', '이름순'], ['date', '발매일순']])}</div></div>`;
  const grid = arr => `<div class="grid">${arr.map(seriesCard).join('')}</div>`;
  if (CMS.view === 'pub') {
    const G = new Map(); for (const s of L) { const p = s.pub || t('출판사 미상'); if (!G.has(p)) G.set(p, []); G.get(p).push(s); }
    for (const [p, arr] of [...G].sort((a, b) => b[1].length - a[1].length || a[0].localeCompare(b[0], 'ko'))) h += `<h2 class="gh">${esc(p)}<span class="pill">${fmtN(arr.length)}</span></h2>` + grid(arr);
  } else h += `<h2 class="gh">${t('시리즈')}<span class="pill">${fmtN(L.length)}</span></h2>` + grid(L);
  return h;
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
  box.querySelectorAll('.fscroll').forEach(el => { const f = () => { el.classList.toggle('fl', el.scrollLeft > 2); el.classList.toggle('fr', el.scrollLeft + el.clientWidth < el.scrollWidth - 2); }; el.onscroll = f; f(); });
}
function cmOpen(key){
  const s = seriesList().find(x => x.key === key); if (!s) return;
  const box = document.createElement('div'); box.id = 'editor';
  box.innerHTML = `<div class="ebox cmsheet" role="dialog" aria-modal="true"><h3>${esc(s.name)}</h3><p class="setnote">${esc([s.pub, s.kind === 'l' ? t('라이트노벨') : t('만화')].join(' · '))}</p>
    ${s.gaps.length ? `<p class="cmwarn ${s.ack ? 'acked' : ''}">${esc(F('missingVols', ranges(s.gaps)))}</p>` : ''}
    <div class="rows">${s.items.map(it => `<a class="cmrowi" href="https://www.aladin.co.kr/m/mproduct.aspx?ItemId=${esc(it.id)}" target="_blank" rel="noopener">
      <span class="cover">${it.cover ? `<img src="${esc(it.cover)}" alt="" loading="lazy" referrerpolicy="no-referrer">` : ''}${it.eb ? '<span class="ebtag">e-book</span>' : ''}</span>
      <span class="grow"><b>${esc(it.vol ? F('volN', it.vol) : t('권수 미상'))}${it.vol && s.read >= it.vol ? ` <i class="ck">✓</i>` : ''}</b><span class="s">${esc(it.t)}</span><span class="s">${esc([it.date && F('pubOn', it.date), it.buy && F('boughtOn', it.buy)].filter(Boolean).join(' · '))}</span></span></a>`).join('')}</div>
    <div class="ebtns"><button class="ecancel">${t('닫기')}</button></div></div>`;
  document.body.appendChild(box);
  box.querySelector('.ecancel').onclick = () => box.remove(); box.onclick = e => { if (e.target === box) box.remove(); };
}
document.addEventListener('click', e => {
  const el = e.target.closest('[data-cm]'); if (!el || !$('#comics') || !$('#comics').contains(el)) return;
  const a = el.dataset.cm, k = el.dataset.k;
  if (a === 'bmnop') { e.preventDefault(); return; }
  e.stopPropagation();
  if (a === 'open') return cmOpen(k);
  if (a === 'guide') { CMS.guide = !CMS.guide; return cmRender(S.tab); }
  if (a === 'bmcopy') { navigator.clipboard?.writeText(BM_CODE).then(() => { el.textContent = t('복사했습니다'); }, () => {}); return; }
  if (a === 'kind' || a === 'view' || a === 'sort') { CMS[a] = el.dataset.v; store.set('cm' + a[0].toUpperCase() + a.slice(1), CMS[a]); return cmRender(S.tab); }
  if (a === 'snap') { CMS.cart = +el.dataset.v; return cmRender(S.tab); }
  if (a === 'snapdel') { if (!confirm(t('이 장바구니 백업을 지울까요?'))) return; CM.carts.splice(+el.dataset.v, 1); CMS.cart = 0; cmSave(); return cmRender(S.tab); }
  const st = (CM.series[k] ||= {});
  if (a === 'read+' || a === 'read-') { const s = seriesList().find(x => x.key === k); st.read = Math.max(0, Math.min((s?.max || 999), (st.read || 0) + (a === 'read+' ? 1 : -1))); st.u = Date.now(); cmSave(); return cmRender(S.tab); }
  if (a === 'ack') { const s = seriesList().find(x => x.key === k); st.ack = s.gaps.join(','); st.u = Date.now(); cmSave(); return cmRender(S.tab); }
}, true);

/* ---------- 북마클릿에서 받기 ---------- */
window.addEventListener('message', e => {
  const d = e.data;
  if (!ALADIN.includes(e.origin) || !d || d.type !== 'dabwanni-aladin' || !Array.isArray(d.items)) return;
  const now = Date.now(); let added = 0;
  const pick = x => ({id: String(x.id), t: String(x.t || '').slice(0, 300), cover: /^https:\/\//.test(x.cover || '') ? x.cover : '', pub: String(x.pub || '').slice(0, 80),
    date: String(x.date || '').slice(0, 10), kind: x.kind === 'l' ? 'l' : 'c', eb: x.eb ? 1 : 0, price: +x.price || 0});
  if (d.kind === 'purchase') {
    for (const x of d.items) { if (!x.id) continue; const it = pick(x), old = CM.items[it.id]; if (!old) added++;
      CM.items[it.id] = {...old, ...it, own: 1, buy: String(x.buy || old?.buy || '').slice(0, 10), vol: volOf(it.t), u: now}; }
  } else if (d.kind === 'cart') {
    const secs = (Array.isArray(d.sections) ? d.sections : []).map(s => ({name: String(s.name || '').slice(0, 40), items: (s.items || []).filter(x => x.id).map(pick)}));
    CM.carts.unshift({at: now, sections: secs}); CM.carts = CM.carts.slice(0, 12); added = secs.reduce((n, s) => n + s.items.length, 0);
  }
  cmSave();
  try { e.source && e.source.postMessage({type: 'dabwanni-aladin-ack', added}, e.origin); } catch {}
  store.set('cmTab', d.kind === 'cart' ? 'ccart' : 'cbuy');
  setMode('comic', d.kind === 'cart' ? 'ccart' : 'cbuy');
});

/* ---------- 동기화에 넣기: 작품·시리즈는 바뀐 시각이 늦은 쪽, 장바구니 백업은 합쳐 최근 12개 ---------- */
function cmMerge(L, R_){
  const out = {v: 1, items: {...(R_?.items || {})}, series: {...(R_?.series || {})}, carts: []};
  for (const [k, v] of Object.entries(L.items || {})) if (!out.items[k] || (v.u || 0) >= (out.items[k].u || 0)) out.items[k] = v;
  for (const [k, v] of Object.entries(L.series || {})) if (!out.series[k] || (v.u || 0) >= (out.series[k].u || 0)) out.series[k] = v;
  const seen = new Set(); for (const c of [...(L.carts || []), ...(R_?.carts || [])].sort((a, b) => b.at - a.at)) if (!seen.has(c.at)) { seen.add(c.at); out.carts.push(c); }
  out.carts = out.carts.slice(0, 12); return out;
}
