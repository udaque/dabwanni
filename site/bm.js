/* 다봤니 북마클릿: 알라딘 구매내역·장바구니 화면에서, 로그인된 본인 세션으로 목록을 읽어 다봤니로 보냅니다.
   상품마다 알라딘 상품 페이지의 구조화 정보(장르·출판사·발매일·전자책 여부)를 읽어 만화·라이트노벨만 고릅니다. */
(function () {
  if (window.__dwBM) { window.__dwBM.show(); return; }
  var DW = 'https://dabwanni.pages.dev';
  var BUY = 'https://www.aladin.co.kr/m/mbest.aspx?BestType=OrderSave', CART = 'https://www.aladin.co.kr/m/mbasket.aspx?start=moheader';
  var isAladin = /(^|\.)aladin\.co\.kr$/.test(location.hostname);
  var mode = /mbasket|wbasket/i.test(location.pathname) ? 'cart' : /OrderSave/i.test(location.search) || /order|mypage|account/i.test(location.pathname) ? 'purchase' : '';

  // ---------- 작은 화면 ----------
  var box = document.createElement('div');
  box.style.cssText = 'position:fixed;left:10px;right:10px;bottom:10px;z-index:2147483647;background:#19202C;color:#E7ECF3;border-radius:14px;padding:14px 16px;font:15px/1.5 -apple-system,system-ui,sans-serif;box-shadow:0 10px 30px rgba(0,0,0,.4)';
  var title = document.createElement('b'); title.textContent = '다봤니 · 알라딘 ' + (mode === 'cart' ? '장바구니 백업' : '구매내역 가져오기');
  var msg = document.createElement('div'); msg.style.cssText = 'margin:6px 0 10px;color:#97A3B6;font-size:14px';
  var row = document.createElement('div'); row.style.cssText = 'display:flex;gap:8px;flex-wrap:wrap';
  box.appendChild(title); box.appendChild(msg); box.appendChild(row); document.body.appendChild(box);
  function btn(label, primary, fn) { var b = document.createElement('button'); b.textContent = label; b.style.cssText = 'height:40px;padding:0 14px;border-radius:10px;font-weight:700;font-size:15px;white-space:nowrap;border:' + (primary ? '0;background:#FF4D55;color:#fff' : '1px solid #2B3443;background:#10151E;color:#E7ECF3'); b.onclick = fn; row.appendChild(b); return b; }
  function finish() { row.innerHTML = ''; btn('닫기', false, function () { box.remove(); window.__dwBM = null; }); }
  window.__dwBM = { show: function () { box.style.display = 'block'; } };
  var closeBtn = btn('닫기', false, function () { box.remove(); window.__dwBM = null; });

  if (!isAladin || !mode) {
    msg.innerHTML = '알라딘 <a style="color:#3BC2BE" href="' + BUY + '">구매내역</a> 또는 <a style="color:#3BC2BE" href="' + CART + '">장바구니</a> 화면에서 눌러 주세요.';
    return;
  }

  // ---------- 목록 읽기 ----------
  var SECT = /(품절|절판|전자책|알라딘\s*배송|중고|판매자|개인\s*판매|해외|직배송|배송)/;
  function txt(el) { return (el && (el.textContent || '') || '').replace(/\s+/g, ' ').trim(); }
  function abs(u) { if (!u) return ''; if (u.indexOf('//') === 0) return 'https:' + u; if (u.indexOf('http') === 0) return u; return ''; }
  function sectionOf(el, doc) {
    // 상품 링크에서 위로 올라가며, 앞쪽 형제들 중 짧은 묶음 이름(품절·전자책·알라딘 배송·중고 …)을 찾음
    var cur = el;
    for (var depth = 0; cur && depth < 16; depth++, cur = cur.parentElement) {
      var p = cur.previousElementSibling, n = 0;
      while (p && n < 40) {
        var tx = txt(p), m = tx.match(SECT);
        if (m && tx.length <= 30 && !/원|\d{2,}/.test(tx.replace(/\(\d+\)|\d+$/, ''))) return secName(p, tx);
        p = p.previousElementSibling; n++;
      }
    }
    return '';
  }
  // 묶음 이름: 머리 줄 안의 글자 칸(label·strong·span 등) 중 묶음 이름이 든 가장 짧은 것 (「접기」 같은 버튼 글자 빼기)
  function secName(el, tx) {
    var best = '', cands = el.querySelectorAll('label, strong, b, span, h2, h3, h4, p, div');
    for (var i = 0; i < cands.length; i++) { var c = txt(cands[i]); if (c && SECT.test(c) && (!best || c.length < best.length)) best = c; }
    best = (best || tx).replace(/\s*(접기|펼치기|전체\s*선택|선택\s*삭제|삭제)\s*/g, ' ').replace(/\s*\(?\d+\)?\s*$/, '').trim();
    return /품절|절판/.test(best) ? '품절·절판' : best;
  }
  // 장바구니의 「함께 구매한 상품」·추천 같은 칸은 장바구니 상품이 아님: 체크 상자가 있는 칸만, 추천 제목 아래는 뺌
  var NOTCART = /함께\s*구매|추천|최근\s*본|이\s*상품을\s*구매|많이\s*구매/;
  function inCart(a) {
    var cur = a;
    for (var d = 0; cur && d < 8; d++, cur = cur.parentElement) {
      if (cur.querySelector && cur.querySelector('input[type="checkbox"]')) {
        var cbs = cur.querySelectorAll('input[type="checkbox"]'); if (cbs.length <= 2) return true;      // 상품 한 칸(체크 상자 1~2개)
      }
    }
    return false;
  }
  function underRecommend(a) {
    var cur = a;
    for (var d = 0; cur && d < 16; d++, cur = cur.parentElement) {
      var p = cur.previousElementSibling, n = 0;
      while (p && n < 10) { var tx = txt(p); if (tx && tx.length < 60 && NOTCART.test(tx)) return true; p = p.previousElementSibling; n++; }
    }
    return false;
  }
  // 구매일: 「구매·주문」 근처의 날짜를 먼저, 없으면 칸 안의 날짜. 달·일이 말이 안 되면 버림 (2025-08-45 같은 잘못 읽기 방지)
  function buyDate(s) {
    s = s.replace(/\s+/g, ' ');
    var re = /(20\d\d)\s*[.\-\/년]\s*(\d{1,2})\s*[.\-\/월]\s*(\d{1,2})(?!\d)/g, m, cands = [];
    while ((m = re.exec(s))) { var mo = +m[2], d = +m[3]; if (mo >= 1 && mo <= 12 && d >= 1 && d <= 31) cands.push({ i: m.index, v: m[1] + '-' + ('0' + mo).slice(-2) + '-' + ('0' + d).slice(-2) }); }
    if (!cands.length) return '';
    var k = s.search(/구매|주문/); if (k >= 0) { cands.sort(function (a, b) { return Math.abs(a.i - k) - Math.abs(b.i - k); }); }
    return cands[0].v;
  }
  function parse(doc) {
    var out = [], seen = {};
    // 알라딘 모바일 목록 칸 (구매내역·베스트 목록과 같은 틀)
    var boxes = doc.querySelectorAll('.browse_list_box[itemId], .browse_list_box[itemid]');
    for (var i = 0; i < boxes.length; i++) {
      var b = boxes[i], id = b.getAttribute('itemId') || b.getAttribute('itemid'); if (!id || seen[id]) continue; seen[id] = 1;
      var tt = txt(b.querySelector('.b_book_t')).replace(/^\d+\.\s*/, ''), img = b.querySelector('img.i_cover, img');
      var pub = txt(b.querySelector('a[href*="PublisherSearch"]'));
      out.push({ id: id, t: tt, cover: abs(img && (img.getAttribute('src') || '')), pub: pub, buy: buyDate(b.textContent || ''), sec: '' });
    }
    // 그 밖의 화면(장바구니 등): 상품 링크마다 가장 가까운 상품 칸에서 제목·표지
    var links = doc.querySelectorAll('a[href*="ItemId="], a[href*="itemid="], a[href*="ItemID="]');
    for (var j = 0; j < links.length; j++) {
      var a = links[j], mm = (a.getAttribute('href') || '').match(/item[iI][dD]=(\d+)/i); if (!mm || seen[mm[1]]) continue;
      if (mode === 'cart' && (underRecommend(a) || !inCart(a))) continue;
      var cell = a.closest('li, tr, .item, [class*="item"], [class*="Item"], [class*="cart"], [class*="basket"]') || a.parentElement;
      var tTxt = txt(a) || (a.querySelector('img') && a.querySelector('img').getAttribute('alt')) || '';
      if (!tTxt || tTxt.length < 2) { var t2 = cell && cell.querySelector('[class*="title"], [class*="tit"], strong, b'); tTxt = txt(t2); }
      if (!tTxt) continue;
      seen[mm[1]] = 1;
      var im = cell && cell.querySelector('img[src*="image.aladin"], img');
      // 가격: 「5,000원」만 들어 있는 칸에서 (제목 끝 숫자와 붙어 읽히지 않게)
      var price = '', leaves = cell ? cell.querySelectorAll('*') : [];
      for (var q = 0; q < leaves.length && !price; q++) { var lt = txt(leaves[q]); if (leaves[q].children.length === 0 && /^[\d,]+\s*원/.test(lt)) price = lt.match(/^([\d,]+)/)[1]; }
      out.push({ id: mm[1], t: tTxt.replace(/^\d+\.\s*/, ''), cover: abs(im && im.getAttribute('src')), pub: '', buy: '', price: price ? +price.replace(/,/g, '') : 0, sec: mode === 'cart' ? sectionOf(a, doc) : '' });
    }
    return out;
  }

  // ---------- 상품 정보 채우기 (장르·출판사·발매일·전자책) ----------
  // 기억 저장: 예전엔 localStorage에 통째로 넣었는데, 수천 권이면 용량(약 5MB)을 넘어 저장이 조용히 실패했음 → IndexedDB에 책마다 따로
  var CK = 'dwbm_cache_v1', cache = {}, DB = null, PROG = null, fails = {};
  function idbOpen() { return new Promise(function (res) { try { var rq = indexedDB.open('dabwanni_bm', 1); rq.onupgradeneeded = function () { rq.result.createObjectStore('c'); rq.result.createObjectStore('p'); }; rq.onsuccess = function () { res(rq.result); }; rq.onerror = function () { res(null); }; } catch (e) { res(null); } }); }
  function put(store, k, v) { if (!DB) return; try { DB.transaction(store, 'readwrite').objectStore(store).put(v, k); } catch (e) {} }
  async function loadStore() {
    DB = await idbOpen();
    if (DB) await new Promise(function (res) { try { var rq = DB.transaction('c').objectStore('c').openCursor(); rq.onsuccess = function (e) { var cur = e.target.result; if (cur) { cache[cur.key] = cur.value; cur.continue(); } else res(); }; rq.onerror = function () { res(); }; } catch (e) { res(); } });
    try { var old = JSON.parse(localStorage.getItem(CK) || 'null'); if (old) { for (var k in old) if (!cache[k]) { cache[k] = old[k]; put('c', k, old[k]); } if (DB) localStorage.removeItem(CK); } } catch (e) {}
    if (DB) PROG = await new Promise(function (res) { try { var rq = DB.transaction('p').objectStore('p').get('prog'); rq.onsuccess = function () { res(rq.result || null); }; rq.onerror = function () { res(null); }; } catch (e) { res(null); } });
    if (!PROG) { try { PROG = JSON.parse(localStorage.getItem('dwbm_progress_v1') || 'null'); } catch (e) {} }
    if (PROG && DB) { put('p', 'prog', PROG); try { localStorage.removeItem('dwbm_progress_v1'); } catch (e) {} }
  }
  function sleep(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
  // 상품 정보 (휴대폰·컴퓨터 똑같이 동작):
  //  ① 모바일 상품 페이지 앞부분만 받아 구조화 정보(제목·표지·출판사·발매일·장르·형태)와 알라딘 ISBN 코드를 읽고
  //  ② 그 코드로 상세 정보 조각(getContents detailinfo)을 받아 「이 책의 전/후속편」 목록과 「주제분류」를 읽음.
  //  시리즈 번호는 전/후속편 목록에 든 상품 번호 중 가장 작은 것 (같은 시리즈의 책은 모두 같은 목록을 보여 줌)
  //  (휴대폰에서는 PC 상품 페이지 주소가 모바일로 넘어가 버려서 이 방법을 씀)
  function flushCache() {}      // 책마다 바로 저장하므로 따로 할 일 없음
  async function readUntil(url, enough) {
    var r = await fetch(url, { credentials: 'include' });
    if (!r.body || !r.body.getReader) return await r.text();
    var rd = r.body.getReader(), dec = new TextDecoder(), h = '';
    while (true) {
      var x = await rd.read(); if (x.done) break; h += dec.decode(x.value, { stream: true });
      if (enough(h)) { try { rd.cancel(); } catch (e) {} break; }
    }
    return h;
  }
  var liText = function (li) { return (li.match(/>([^<>]+)<\/a>/g) || []).map(function (x) { return x.replace(/<\/a>|>/g, '').trim(); }).filter(Boolean).join(' > '); };
  function failed(why, old) { fails[why] = (fails[why] || 0) + 1; return { fail: why, old: old }; }
  async function detail(id) {
    var old = cache[id];
    if (old && old.mv && old.cats) return old;      // 상세 조각까지 읽은 책만 건너뜀
    var d = { k: '', mv: 1 };
    try {
      var h = await readUntil('/m/mproduct.aspx?ItemId=' + id, function (s) { var a = s.indexOf('application/ld+json'); return a >= 0 && s.indexOf('</script>', a) >= 0 && /isbn:\s*"[0-9A-Z]{8,}"/.test(s); });
      var ld = h.match(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g) || [];
      for (var i = 0; i < ld.length; i++) {
        try { var o = JSON.parse(ld[i].replace(/^<script[^>]*>|<\/script>$/g, ''));
          if (o['@type'] === 'Book') {
            var we = (o.workExample || [])[0] || {}, g = String(o.genre || ''), f = String(we.bookFormat || '');
            d.t = o.name || ''; d.cover = o.image || ''; d.pub = (o.publisher && o.publisher.name) || ''; d.date = we.datePublished || '';
            d.eb = /EBook/i.test(f) ? 1 : 0; d.g = g.slice(0, 80); d.f = f.replace(/^https?:\/\/schema\.org\//, '');
            var isC = /만화|코믹|웹툰|그래픽\s*노블|BL|툰/.test(g), isL = /라이트\s*노벨|라노벨|라이트노벨/.test(g);
            d.k = isC ? 'c' : isL ? 'l' : /GraphicNovel/i.test(f) ? 'c' : '';
          }
        } catch (e) {}
      }
      if (!d.t && /19세 이상/.test(h)) { d.adult = 1; var old = cache[id] || {}; ['t', 'cover', 'pub', 'date', 'eb', 'k', 'g'].forEach(function (k2) { if (old[k2] != null && d[k2] == null) d[k2] = old[k2]; }); }
      var code = (h.match(/isbn:\s*"([0-9A-Z]{8,})"/) || [])[1];      // 새 책 K…, 전자책 E…, 옛 책은 ISBN 숫자
      if (code) try {      // 상세 조각을 못 받아도 책 정보(분류는 장르로)는 살림
        var h2 = await (await fetch('/shop/product/getContents.aspx?ISBN=' + code + '&name=detailinfo&type=6&date=15', { credentials: 'include' })).text();
        var si = h2.indexOf('id="u_series"');
        if (si >= 0) {
          var ids = (h2.slice(si, h2.indexOf('</ul>', si)).match(/[Ii]tem[Ii]d=(\d+)/g) || []).map(function (x) { return +x.replace(/\D/g, ''); });
          if (ids.length) { d.sid = String(Math.min.apply(null, ids)); d.sn = ids.length; }
        }
        var ca = h2.match(/<div id="category_all"[^>]*>([\s\S]*?)<\/div>/) || h2.match(/<div id="category_short"[^>]*>([\s\S]*?)<\/div>/);
        d.cats = [];
        if (ca) d.cats = (ca[1].match(/<li[^>]*>[\s\S]*?<\/li>/g) || []).map(liText).filter(Boolean).slice(0, 4);
        if (d.cats && d.cats.length) { var cl = d.cats.some(function (p) { return /만화\/라이트노벨 > 라이트 노벨/.test(p); }), cc = d.cats.some(function (p) { return /만화\/라이트노벨 > (?!라이트 노벨)/.test(p); }); if (cc || cl) d.k = cc ? 'c' : 'l'; }
      } catch (e2) { d.mv = 0; }      // 다음에 다시 시도
    } catch (e) { return failed('연결', old); }
    if (!d.t && !d.adult) return failed('다른 화면', old);      // 정상 상품 화면이 아님 (막힘·오류 화면 등) → 저장하지 않고 다시 시도
    cache[id] = d; put('c', id, d);
    return d;
  }

  // ---------- 진행 저장: 구매내역 목록을 읽은 쪽과 목록을 알라딘 쪽에 저장해 두고, 다시 누르면 거기서 이어서 ----------
  var PK = 'dwbm_progress_v1';
  function loadProg() { return PROG; }
  function saveProg(p) { PROG = p; if (DB) put('p', 'prog', p); else { try { localStorage.setItem(PK, JSON.stringify(p)); } catch (e) {} } }
  var slim = function (x) { return { id: x.id, t: x.t, cover: x.cover, pub: x.pub, buy: x.buy, sec: x.sec, price: x.price }; };
  var all = [], working = false, stopNow = false;

  async function readList() {
    if (mode !== 'purchase') { all = parse(document); return; }
    var prog = loadProg(), start = 2, rows = 0, known = null;
    if (prog && prog.mode === 'purchase' && !prog.done && prog.items && prog.items.length) {
      all = prog.items; start = prog.lastPage + 1; rows = prog.rows || 0;
      msg.textContent = '지난번에 ' + prog.lastPage + '쪽까지 읽었습니다. ' + start + '쪽부터 이어서 읽습니다.';
    } else {
      all = parse(document);
      if (prog && prog.done && prog.items) { known = {}; prog.items.forEach(function (x) { known[x.id] = 1; }); }
      // 한 쪽에 50권씩 보이는지 시험
      try {
        var u1 = new URL(location.href); u1.searchParams.set('page', 1); u1.searchParams.set('ViewRowsCount', 50);
        var got1 = parse(new DOMParser().parseFromString(await (await fetch(u1.toString(), { credentials: 'include' })).text(), 'text/html'));
        if (got1.length > all.length) { rows = 50; var h0 = {}; all.forEach(function (x) { h0[x.id] = 1; }); got1.forEach(function (x) { if (!h0[x.id]) all.push(x); }); }
      } catch (e) {}
    }
    for (var p = start; p <= 5000 && !stopNow; p++) {
      var u = new URL(location.href); u.searchParams.set('page', p); if (rows) u.searchParams.set('ViewRowsCount', rows);
      var got = parse(new DOMParser().parseFromString(await (await fetch(u.toString(), { credentials: 'include' })).text(), 'text/html'));
      var have = {}, add = 0, fresh = 0; all.forEach(function (x) { have[x.id] = 1; });
      got.forEach(function (x) { if (!have[x.id]) { all.push(x); add++; } if (known && !known[x.id]) fresh++; });
      msg.textContent = '목록을 읽는 중… ' + p + '쪽, ' + all.length + '권 (중간에 멈춰도 다음에 이어서 읽습니다)';
      saveProg({ mode: 'purchase', done: false, lastPage: p, rows: rows, items: all.map(slim), at: Date.now() });
      if (!add) break;
      if (known && !fresh) {                                  // 지난번에 끝까지 읽었으면, 새로 산 책이 안 나오는 쪽에서 멈추고 지난 목록과 합침
        var h2 = {}; all.forEach(function (x) { h2[x.id] = 1; }); prog.items.forEach(function (x) { if (!h2[x.id]) all.push(x); });
        break;
      }
      await sleep(600);
    }
    if (!stopNow) saveProg({ mode: 'purchase', done: true, lastPage: 0, rows: rows, items: all.map(slim), at: Date.now() });
  }
  function fill(x, d) {
    if (d.fail) { x.failed = d.fail; if (d.old) { d = d.old; } else return; } else x.failed = '';
    x.g = d.g; x.f = d.f; x.sid = d.sid; x.cats = d.cats; if (d.t) x.t = d.t; if (d.cover) x.cover = d.cover; if (d.pub) x.pub = d.pub; x.date = d.date || ''; x.eb = d.eb || /^\s*\[eBook\]/i.test(x.t) || /전자책/.test(x.sec || '') ? 1 : 0; x.kind = d.k || (d.adult ? 'c' : ''); }
  var picked = function () { return all.filter(function (x) { return x.kind === 'c' || x.kind === 'l'; }); };
  function workingButtons() {
    row.innerHTML = '';
    btn('지금까지 보내기', true, function () { send(false); });
    btn('멈추기', false, function () { stopNow = true; });
  }
  var wake = null;
  async function keepAwake() { try { if (navigator.wakeLock && !wake) { wake = await navigator.wakeLock.request('screen'); wake.addEventListener('release', function () { wake = null; }); } } catch (e) {} }
  document.addEventListener('visibilitychange', function () { if (document.visibilityState === 'visible' && working) keepAwake(); });
  async function run() {
    closeBtn.remove(); working = true; workingButtons(); keepAwake();
    msg.textContent = '목록을 읽는 중…';
    await readList();
    if (stopNow && mode === 'purchase') { var pg0 = (loadProg() || {}).lastPage; msg.textContent = '목록을 ' + pg0 + '쪽까지 읽고 멈췄습니다. 다시 누르면 ' + (pg0 + 1) + '쪽부터 이어서 읽습니다.'; finish(); return; }
    if (!all.length) { msg.textContent = '이 화면에서 상품을 찾지 못했습니다. 알라딘 화면 구조가 다를 수 있습니다. 이 화면 캡처를 다봤니 관리자에게 보내 주세요.'; finish(); return; }
    var i = 0, done = 0, need = all.filter(function (x) { return !(cache[x.id] && cache[x.id].mv && cache[x.id].cats); }).length;
    var streak = 0, queue = all.slice(), round = 0;
    var showing = function () {
      var left = need - fresh0, sec = fresh0 > 10 ? Math.round((Date.now() - t0) / fresh0 * left / 1000) : 0, nf = all.filter(function (x) { return x.failed; }).length;
      msg.textContent = (round ? '읽기 실패한 책 다시 시도 중 (' + round + '번째)… ' : '책 정보를 확인하는 중… ' + done + ' / ' + all.length) + ' · 만화·라이트노벨 ' + picked().length + '권' + (nf ? ' · 다시 읽을 책 ' + nf + '권' : '') + (!round && left > 0 ? ' · 새로 읽는 책 ' + left + '권 남음' + (sec ? ', 약 ' + Math.max(1, Math.round(sec / 60)) + '분' : '') : '') + ' · 화면을 켜 둔 채로 두세요';
    };
    var worker = async function () {
      while (!stopNow && queue.length) {
        var x = queue.shift(), had = !!(cache[x.id] && cache[x.id].mv && cache[x.id].cats);
        var d = await detail(x.id); fill(x, d); if (!round) done++;
        if (!had && !d.fail) fresh0++;
        if (d.fail) { streak++; if (streak >= 8) { msg.textContent = '알라딘 응답이 원활하지 않아 잠시 쉬었다가 이어서 읽습니다…'; await sleep(20000); streak = 0; } }
        else streak = 0;
        showing();
        if (!had) await sleep(150);
      }
    };
    var t0 = Date.now(), fresh0 = 0;
    await Promise.all([worker(), worker(), worker(), worker()]);
    // 실패한 책만 모아 쉬었다가 다시 (최대 8번, 갈수록 오래 쉼, 동시 2개)
    for (round = 1; round <= 8 && !stopNow; round++) {
      queue = all.filter(function (x) { return x.failed; }); if (!queue.length) break;
      msg.textContent = '읽기 실패한 책 ' + queue.length + '권을 ' + (round * 5) + '초 뒤 다시 읽습니다…'; await sleep(round * 5000);
      await Promise.all([worker(), worker()]);
    }
    round = 0;
    working = false; try { wake && wake.release(); } catch (e) {}
    var items = picked();
    var nf = all.filter(function (x) { return x.failed; }), nfOld = nf.filter(function (x) { return x.kind; }).length, why = Object.keys(fails).map(function (k) { return k + ' ' + fails[k] + '회'; }).join(', ');
    msg.textContent = (stopNow ? '멈췄습니다. 여기까지 확인한 ' + done + '권' : '전체 ' + all.length + '권') + ' 중 만화·라이트노벨 ' + items.length + '권' + (stopNow ? '. 다시 누르면 이어서 진행합니다.' : '을 찾았습니다.') +
      (nf.length ? ' 끝내 읽지 못한 책 ' + nf.length + '권(예전 정보로 처리 ' + nfOld + '권)은 다음에 다시 읽습니다. 실패 사유: ' + why : '');
    row.innerHTML = '';
    if (items.length) btn('다봤니로 보내기', true, function () { send(true); });
    btn('닫기', false, function () { box.remove(); window.__dwBM = null; });
  }
  // 보내기: 중간에 보내도 확인은 계속되고, 다 끝나면 마지막으로 한 번 더 보내면 됨 (다봤니 쪽은 겹치지 않게 합침)
  function send(final) {
    var items = picked().map(function (x) { return { id: x.id, t: x.t, cover: x.cover, pub: x.pub, buy: x.buy, date: x.date, eb: x.eb, kind: x.kind, price: x.price, sec: x.sec, g: x.g, f: x.f, sid: x.sid, cats: x.cats }; });
    if (!items.length) { msg.textContent = '아직 보낼 만화·라이트노벨이 없습니다.'; return; }
    var w = window.open(DW + '/#comics-import', 'dabwanni'), payload;
    if (mode === 'cart') {
      var secs = [], idx = {};
      items.forEach(function (x) { var n = x.sec || '기타'; if (!(n in idx)) { idx[n] = secs.length; secs.push({ name: n, items: [] }); } secs[idx[n]].items.push(x); });
      payload = { type: 'dabwanni-aladin', kind: 'cart', items: items, sections: secs };
    } else payload = { type: 'dabwanni-aladin', kind: 'purchase', items: items };
    var keep = msg.textContent; msg.textContent = '보내는 중… (' + items.length + '권)';
    var tries = 0, timer = setInterval(function () { tries++; try { w && w.postMessage(payload, DW); } catch (e) {} if (tries > 60) { clearInterval(timer); msg.textContent = '전달하지 못했습니다. 다봤니 창이 열렸는지 확인한 뒤 다시 눌러 주세요.'; } }, 500);
    window.addEventListener('message', function onAck(e) {
      if (e.origin !== DW || !e.data || e.data.type !== 'dabwanni-aladin-ack') return;
      clearInterval(timer); window.removeEventListener('message', onAck);
      var note = mode === 'cart' ? '장바구니 ' + e.data.added + '권을 백업했습니다.' : '새로 들어간 책 ' + e.data.added + '권.';
      if (working) { msg.textContent = '보냈습니다. ' + note + ' 계속 확인하는 중입니다.'; workingButtons(); }
      else { msg.textContent = '보냈습니다. ' + note; finish(); }
    });
  }
  msg.textContent = mode === 'cart' ? '이 장바구니의 만화·라이트노벨을 다봤니에 백업합니다.' : '구매내역의 만화·라이트노벨을 모두 읽어 다봤니로 가져옵니다. 쪽이 많으면 몇 분 걸릴 수 있습니다.';
  var startMsg = msg.textContent; msg.textContent = '준비하는 중…';
  loadStore().then(function () {
    msg.textContent = startMsg;
    var pr = loadProg();
    if (mode === 'purchase' && pr && !pr.done && pr.items && pr.items.length) msg.textContent = '지난번에 목록을 ' + pr.lastPage + '쪽까지 읽었습니다. 「시작」을 누르면 이어서 진행합니다.';
    btn('시작', true, run);
  });
})();
