/* 다봤니 북마크 하나로 모든 사이트에서: 먼저 다봤니의 bm.js를 불러와 실행하고(알라딘 등),
   그 사이트가 보안 설정으로 바깥 js를 막아 불러오기가 실패하면(리디 등) 다봤니 연결 창(bridge)을 열어
   그 사이트에 맞는 코드를 받아 페이지 안에서 실행함 */
(function () {
  var D = 'https://dabwanni.pages.dev', s = document.createElement('script');
  s.src = D + '/bm.js?v=' + Date.now();
  s.onerror = function () {
    var o = document.getElementById('dwrl'); if (o) o.remove();
    var b = document.createElement('div'); b.id = 'dwrl';
    b.style.cssText = 'position:fixed;left:12px;right:12px;bottom:12px;z-index:2147483647;background:#1B2130;color:#E7ECF3;border-radius:16px;padding:16px;font:15px/1.5 -apple-system,sans-serif';
    b.textContent = '다봤니 연결 중… 새 창이 열리면 이 화면으로 돌아와 주세요.'; document.body.appendChild(b);
    var w = window.open(D + '/bridge', 'dabwanni'), n = 0, t;
    addEventListener('message', function f(e) {
      if (e.origin !== D || !e.data || e.data.type !== 'dw-code') return;
      removeEventListener('message', f); clearInterval(t); b.remove();
      if (!e.data.code) { alert('다봤니: 이 사이트는 아직 지원하지 않습니다.'); return; }
      window.__dwRidi = 0; var c = document.createElement('script'); c.textContent = e.data.code; document.body.appendChild(c);
    });
    t = setInterval(function () { n++; try { w && w.postMessage({ type: 'dw-hello' }, D); } catch (x) {} if (n > 100) { clearInterval(t); b.textContent = '다봤니 창과 연결하지 못했습니다. 팝업 차단을 끄고 다시 눌러 주세요.'; } }, 300);
  };
  document.body.appendChild(s);
})();
