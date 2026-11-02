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
    // 위로 올라가며 앞쪽 형제들에서 묶음 이름(전자책·알라딘 배송·중고 …)을 찾음
    var cur = el;
    for (var depth = 0; cur && depth < 12; depth++, cur = cur.parentElement) {
      var p = cur.previousElementSibling, n = 0;
      while (p && n < 30) { var tx = txt(p); if (tx && tx.length < 40 && SECT.test(tx)) return tx.replace(/\s*\d+\s*$/, ''); p = p.previousElementSibling; n++; }
    }
    return '';
  }
  function parse(doc) {
    var out = [], seen = {};
    // 알라딘 모바일 목록 칸 (구매내역·베스트 목록과 같은 틀)
    var boxes = doc.querySelectorAll('.browse_list_box[itemId], .browse_list_box[itemid]');
    for (var i = 0; i < boxes.length; i++) {
      var b = boxes[i], id = b.getAttribute('itemId') || b.getAttribute('itemid'); if (!id || seen[id]) continue; seen[id] = 1;
      var tt = txt(b.querySelector('.b_book_t')).replace(/^\d+\.\s*/, ''), img = b.querySelector('img.i_cover, img');
      var pub = txt(b.querySelector('a[href*="PublisherSearch"]')), m = (b.textContent || '').match(/(20\d\d)[.\-년\s]+(\d{1,2})[.\-월\s]+(\d{1,2})/);
      out.push({ id: id, t: tt, cover: abs(img && (img.getAttribute('src') || '')), pub: pub, buy: m ? m[1] + '-' + ('0' + m[2]).slice(-2) + '-' + ('0' + m[3]).slice(-2) : '', sec: '' });
    }
    // 그 밖의 화면(장바구니 등): 상품 링크마다 가장 가까운 상품 칸에서 제목·표지
    var links = doc.querySelectorAll('a[href*="ItemId="], a[href*="itemid="], a[href*="ItemID="]');
    for (var j = 0; j < links.length; j++) {
      var a = links[j], mm = (a.getAttribute('href') || '').match(/item[iI][dD]=(\d+)/i); if (!mm || seen[mm[1]]) continue;
      var cell = a.closest('li, tr, .item, [class*="item"], [class*="Item"], [class*="cart"], [class*="basket"]') || a.parentElement;
      var tTxt = txt(a) || (a.querySelector('img') && a.querySelector('img').getAttribute('alt')) || '';
      if (!tTxt || tTxt.length < 2) { var t2 = cell && cell.querySelector('[class*="title"], [class*="tit"], strong, b'); tTxt = txt(t2); }
      if (!tTxt) continue;
      seen[mm[1]] = 1;
      var im = cell && cell.querySelector('img[src*="image.aladin"], img');
      // 가격: 「5,000원」만 들어 있는 칸에서 (제목 끝 숫자와 붙어 읽히지 않게)
      var price = '', leaves = cell ? cell.querySelectorAll('*') : [];
      for (var q = 0; q < leaves.length && !price; q++) { var lt = txt(leaves[q]); if (leaves[q].children.length === 0 && /^[\d,]+\s*원/.test(lt)) price = lt.match(/^([\d,]+)/)[1]; }
      out.push({ id: mm[1], t: tTxt.replace(/^\d+\.\s*/, ''), cover: abs(im && im.getAttribute('src')), pub: '', buy: '', price: price ? +price.replace(/,/g, '') : 0, sec: mode === 'cart' ? sectionOf(cell || a, doc) : '' });
    }
    return out;
  }

  // ---------- 상품 정보 채우기 (장르·출판사·발매일·전자책) ----------
  var CK = 'dwbm_cache_v1', cache = {};
  try { cache = JSON.parse(localStorage.getItem(CK) || '{}'); } catch (e) {}
  function sleep(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
  function detail(id) {
    if (cache[id]) return Promise.resolve(cache[id]);
    return fetch('/m/mproduct.aspx?ItemId=' + id, { credentials: 'include' }).then(function (r) { return r.text(); }).then(function (h) {
      var d = { k: '' };
      var ld = h.match(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g) || [];
      for (var i = 0; i < ld.length; i++) {
        try { var o = JSON.parse(ld[i].replace(/^<script[^>]*>|<\/script>$/g, ''));
          if (o['@type'] === 'Book') {
            var we = (o.workExample || [])[0] || {}, g = String(o.genre || ''), f = String(we.bookFormat || '');
            d.t = o.name || ''; d.cover = o.image || ''; d.pub = (o.publisher && o.publisher.name) || ''; d.date = we.datePublished || '';
            d.eb = /EBook/i.test(f) ? 1 : 0;
            d.k = /라이트\s*노벨|라노벨|라이트노벨/.test(g) ? 'l' : (/GraphicNovel/i.test(f) || /만화|코믹|웹툰|그래픽노블|BL|순정|소년|소녀|청년/.test(g)) ? 'c' : '';
          }
        } catch (e) {}
      }
      if (!d.t && /19세 이상/.test(h)) d.adult = 1;
      cache[id] = d; try { localStorage.setItem(CK, JSON.stringify(cache)); } catch (e) {}
      return d;
    }).catch(function () { return { k: '' }; });
  }

  var items = [], payload = null;
  function run() {
    closeBtn.remove();
    msg.textContent = '목록을 읽는 중…';
    var all = parse(document), pages = 1;
    var next = Promise.resolve();
    if (mode === 'purchase') {
      // 다음 쪽이 있으면 이어서 읽음 (새 상품이 안 나오면 멈춤)
      var loop = function (p) {
        if (p > 60) return Promise.resolve();
        var u = new URL(location.href); u.searchParams.set('page', p);
        return fetch(u.toString(), { credentials: 'include' }).then(function (r) { return r.text(); }).then(function (h) {
          var doc = new DOMParser().parseFromString(h, 'text/html'), got = parse(doc), have = {}, add = 0;
          all.forEach(function (x) { have[x.id] = 1; }); got.forEach(function (x) { if (!have[x.id]) { all.push(x); add++; } });
          pages = p; msg.textContent = '목록을 읽는 중… ' + p + '쪽, ' + all.length + '권';
          if (add) return sleep(800).then(function () { return loop(p + 1); });
        });
      };
      next = loop(2);
    }
    next.then(function () {
      if (!all.length) { msg.textContent = '이 화면에서 상품을 찾지 못했습니다. 알라딘 화면 구조가 다를 수 있습니다. 이 화면 캡처를 다봤니 관리자에게 보내 주세요.'; finish(); return; }
      var i = 0;
      var step = function () {
        if (i >= all.length) return Promise.resolve();
        var x = all[i++]; msg.textContent = '책 정보를 확인하는 중… ' + i + ' / ' + all.length;
        var had = !!cache[x.id];
        return detail(x.id).then(function (d) {
          if (d.t) x.t = x.t || d.t; if (d.cover) x.cover = d.cover; if (d.pub) x.pub = d.pub; x.date = d.date || ''; x.eb = d.eb || /^\s*\[eBook\]/i.test(x.t) || /전자책/.test(x.sec) ? 1 : 0;
          x.kind = d.k || (d.adult ? 'c' : '');
          return had ? null : sleep(500);
        }).then(step);
      };
      return step().then(function () {
        items = all.filter(function (x) { return x.kind === 'c' || x.kind === 'l'; });
        msg.textContent = '전체 ' + all.length + '권 중 만화·라이트노벨 ' + items.length + '권을 찾았습니다.';
        row.innerHTML = '';
        if (!items.length) { finish(); return; }
        btn('다봤니로 보내기', true, send); btn('닫기', false, function () { box.remove(); window.__dwBM = null; });
      });
    });
  }
  function send() {
    var w = window.open(DW + '/#comics-import', 'dabwanni');
    if (mode === 'cart') {
      var secs = [], idx = {};
      items.forEach(function (x) { var n = x.sec || '기타'; if (!(n in idx)) { idx[n] = secs.length; secs.push({ name: n, items: [] }); } secs[idx[n]].items.push(x); });
      payload = { type: 'dabwanni-aladin', kind: 'cart', items: items, sections: secs };
    } else payload = { type: 'dabwanni-aladin', kind: 'purchase', items: items };
    row.innerHTML = ''; msg.textContent = '보내는 중… (' + items.length + '권)';
    var tries = 0, timer = setInterval(function () { tries++; try { w && w.postMessage(payload, DW); } catch (e) {} if (tries > 60) { clearInterval(timer); msg.textContent = '전달하지 못했습니다. 다봤니 창이 열렸는지 확인한 뒤 다시 눌러 주세요.'; row.innerHTML = ''; btn('다시 보내기', true, send); } }, 500);
    window.addEventListener('message', function onAck(e) {
      if (e.origin !== DW || !e.data || e.data.type !== 'dabwanni-aladin-ack') return;
      clearInterval(timer); window.removeEventListener('message', onAck);
      msg.textContent = '보냈습니다. ' + (mode === 'cart' ? '장바구니 ' + e.data.added + '권을 백업했습니다.' : '새로 들어간 책 ' + e.data.added + '권.'); finish();
    });
  }
  msg.textContent = mode === 'cart' ? '이 장바구니의 만화·라이트노벨을 다봤니에 백업합니다.' : '구매내역의 만화·라이트노벨을 모두 읽어 다봤니로 가져옵니다. 쪽이 많으면 몇 분 걸릴 수 있습니다.';
  btn('시작', true, run);
})();
