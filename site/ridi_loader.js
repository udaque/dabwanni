(function () {
  if (window.__dwRidiL) { var o = document.getElementById('dwrl'); if (o) o.remove(); }
  window.__dwRidiL = 1; window.__dwRidi = 0;
  var D = 'https://dabwanni.pages.dev', b = document.createElement('div'); b.id = 'dwrl';
  b.style.cssText = 'position:fixed;left:12px;right:12px;bottom:12px;z-index:2147483647;background:#1B2130;color:#E7ECF3;border-radius:16px;padding:16px;font:15px/1.5 -apple-system,sans-serif';
  b.textContent = '다봤니 연결 중… 새 창이 열리면 이 화면으로 돌아와 주세요.'; document.body.appendChild(b);
  var w = window.open(D + '/ridi.html', 'dabwanni'), n = 0, t;
  addEventListener('message', function f(e) {
    if (e.origin !== D || !e.data || e.data.type !== 'dw-ridi-code') return;
    removeEventListener('message', f); clearInterval(t); b.remove();
    var s = document.createElement('script'); s.textContent = e.data.code; document.body.appendChild(s);
  });
  t = setInterval(function () { n++; try { w && w.postMessage({ type: 'dw-ridi-hello' }, D); } catch (x) {} if (n > 100) { clearInterval(t); b.textContent = '다봤니 창과 연결하지 못했습니다. 팝업 차단을 끄고 다시 눌러 주세요.'; } }, 300);
})();
