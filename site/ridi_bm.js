/* 다봤니 · 리디 구매내역 가져오기 (리디 내 서재 https://ridibooks.com/library 에서 실행)
   리디 화면은 외부 스크립트를 막아서(보안 정책) 이 코드 전체가 북마크 안에 들어감.
   ① 내 서재 목록(library-api, 로그인 필요) → 책 번호·구매일  ② 책 정보(book-api) → 제목·표지·작가·시리즈·분류 */
(async () => {
  if (window.__dwRidi) return; window.__dwRidi = 1;
  var LIB = 'https://library-api.ridibooks.com', BK = 'https://book-api.ridibooks.com', DW = 'https://dabwanni.pages.dev';
  var box = document.createElement('div');
  box.style.cssText = 'position:fixed;left:12px;right:12px;bottom:12px;z-index:2147483647;background:#1B2130;color:#E7ECF3;border-radius:16px;padding:16px;font:15px/1.5 -apple-system,sans-serif;box-shadow:0 8px 30px rgba(0,0,0,.4)';
  box.innerHTML = '<b style="display:block;margin-bottom:6px">다봤니 · 리디 구매내역 가져오기</b><div id="dwrm" style="color:#97A3B6;font-size:14px"></div><div id="dwrb" style="display:flex;gap:8px;flex-wrap:wrap;margin-top:12px"></div>';
  document.body.appendChild(box);
  var msg = function (s) { box.querySelector('#dwrm').textContent = s; };
  var btn = function (label, main, fn) { var b = document.createElement('button'); b.textContent = label; b.style.cssText = 'height:40px;padding:0 16px;border-radius:10px;border:1px solid ' + (main ? '#E85A5A' : '#2B3443') + ';background:' + (main ? '#E85A5A' : '#10151E') + ';color:#fff;font-size:15px;font-weight:700;white-space:nowrap'; b.onclick = fn; box.querySelector('#dwrb').appendChild(b); return b; };
  var clearBtns = function () { box.querySelector('#dwrb').innerHTML = ''; };
  var close = function () { box.remove(); window.__dwRidi = 0; };
  var sleep = function (ms) { return new Promise(function (r) { setTimeout(r, ms); }); };
  var J = async function (u, cred) {
    for (var k = 0; k < 3; k++) {
      try { var r = await fetch(u, cred ? { credentials: 'include' } : {}); if (r.status === 401) throw new Error('login'); if (r.ok) return await r.json(); } catch (e) { if (e.message === 'login') throw e; }
      await sleep(800 * (k + 1));
    }
    throw new Error(u.replace(/\?.*$/, '').replace(/^https:\/\/[^/]+/, ''));
  };
  var ROLE = { author: '지은이', comic_author: '만화', story_writer: '글', illustrator: '그림', original_author: '원작', original_illustrator: '원작 그림', translator: '옮긴이', planner: '기획', editor: '편집', adaptor: '각색' };
  var items = [];
  async function run() {
    clearBtns(); btn('닫기', false, close);
    // ① 내 서재 목록: 시리즈(묶음) 단위 → 묶음 안의 책들
    var units = [], own = new Map();
    var add = function (x) {
      if (!x || !x.b_id) return;
      var exp = String(x.expire_date || ''), rent = /rent/i.test(String(x.service_type || '')) || x.is_ridiselect || (exp && !/^9999/.test(exp));
      if (!rent) own.set(String(x.b_id), String(x.purchase_date || '').slice(0, 10));      // 대여·리디셀렉트는 뺌
    };
    for (var o = 0; ; o += 48) {
      var d = await J(LIB + '/items/main/?offset=' + o + '&limit=48', 1), it = d.items || [];
      units.push.apply(units, it); msg('내 서재 목록을 읽는 중… ' + units.length + '묶음');
      if (it.length < 48) break; await sleep(150);
    }
    for (var i = 0; i < units.length; i++) {
      var u = units[i];
      if ((u.unit_count || 1) <= 1) { add(u); continue; }
      for (var p = 0; ; p += 48) {
        var e = await J(LIB + '/items/main/' + u.unit_id + '?offset=' + p + '&limit=48', 1), list = e.items || [];
        list.forEach(add); if (list.length < 48) break; await sleep(120);
      }
      msg('묶음 안의 책을 읽는 중… ' + (i + 1) + ' / ' + units.length + ' (' + own.size + '권)'); await sleep(120);
    }
    // ② 책 정보 (50권씩)
    var ids = Array.from(own.keys()), skipped = 0;
    for (var s = 0; s < ids.length; s += 50) {
      var part = ids.slice(s, s + 50), books = await J(BK + '/books?b_ids=' + part.join(','));
      (books || []).forEach(function (x) {
        var cats = x.categories || [], comic = cats.some(function (c) { return c.genre === 'comic'; });
        if (!comic) { skipped++; return; }      // 만화·웹툰·라이트노벨만 (소설 등은 뺌)
        var ln = cats.some(function (c) { return c.sub_genre === 'lightnovel' || /라이트\s*노벨|라노벨/.test(c.name || ''); });
        var ser = x.series || {}, sp = ser.property || {}, tt = x.title || {};
        items.push({
          id: 'r' + x.id, t: String(tt.main || ''), sub: String(tt.sub || ''), cover: x.thumbnail && (x.thumbnail.large || x.thumbnail.small) ? String(x.thumbnail.large || x.thumbnail.small).replace(/#.*$/, '') : '',
          pub: x.publisher && x.publisher.name || '', date: String((x.publish && x.publish.ebook_publish) || '').slice(0, 10), buy: own.get(String(x.id)) || '',
          kind: ln ? 'l' : 'c', eb: 1, src: 'ridi', rcat: cats.map(function (c) { return c.name; }).join(', '),
          ppl: (x.authors || []).map(function (a) { return { n: a.name, r: ROLE[a.role] || a.role }; }),
          sid: ser.id ? 'r' + ser.id : '', vol: ser.volume, unit: sp.unit || '', rfin: sp.is_completed && sp.total_book_count ? sp.total_book_count : 0
        });
      });
      msg('책 정보를 읽는 중… ' + Math.min(s + 50, ids.length) + ' / ' + ids.length); await sleep(150);
    }
    msg('리디 구매 ' + ids.length + '권 중 만화·라이트노벨 ' + items.length + '권을 찾았습니다.' + (skipped ? ' (만화가 아닌 책 ' + skipped + '권 제외)' : ''));
    clearBtns(); if (items.length) btn('다봤니로 보내기', true, send); btn('닫기', false, close);
  }
  // 다봤니로 전달: 누를 때마다 새 창으로 열고, 답이 올 때까지 보냄. 창이 닫히면 알아채고 다시 누르라고 알림
  var SEND = {};
  function send() {
    if (SEND.timer) clearInterval(SEND.timer); if (SEND.ack) window.removeEventListener('message', SEND.ack);
    var w = window.open(DW + '/#comics-import', 'dabwanni' + Date.now()), payload = { type: 'dabwanni-ridi', items: items }, tries = 0;
    if (!w) { msg('다봤니 창을 열지 못했습니다. 팝업 차단을 끄고 다시 눌러 주세요.'); return; }
    try { w.focus(); } catch (e) {}
    msg('보내는 중… (' + items.length + '권)');
    SEND.timer = setInterval(function () {
      tries++;
      if (w.closed) { clearInterval(SEND.timer); window.removeEventListener('message', SEND.ack); msg('다봤니 창이 닫혀 전달하지 못했습니다. 「다봤니로 보내기」를 다시 눌러 주세요.'); return; }
      try { w.postMessage(payload, DW); } catch (e) {}
      if (tries > 240) { clearInterval(SEND.timer); msg('전달하지 못했습니다. 「다봤니로 보내기」를 다시 눌러 주세요.'); }
    }, 500);
    SEND.ack = function (e) {
      if (e.origin !== DW || !e.data || e.data.type !== 'dabwanni-aladin-ack') return;      // 다봤니가 받았다는 답
      clearInterval(SEND.timer); window.removeEventListener('message', SEND.ack);
      msg('보냈습니다. 새로 들어간 책 ' + e.data.added + '권.'); clearBtns(); btn('닫기', false, close);
    };
    window.addEventListener('message', SEND.ack);
  }
  msg('리디에서 산 만화·라이트노벨을 다봤니로 가져옵니다.');
  btn('시작', true, function () { run().catch(function (e) { msg(e.message === 'login' ? '리디에 로그인한 상태로 내 서재에서 다시 눌러 주세요.' : '읽는 중 문제가 생겼습니다: ' + e.message + ' — 이 화면을 캡처해 주세요.'); clearBtns(); btn('닫기', false, close); }); });
  btn('닫기', false, close);
})();
