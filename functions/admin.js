// /admin : 관리자 로그인 (GET 화면, POST 확인). /admin?logout 으로 나가기
import { token } from './_auth.js';
const page = (msg = '') => `<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>다봤니 관리자</title><style>
:root{color-scheme:light dark;--bg:#F4F6F9;--ink:#18202E;--line:#D5DBE3;--sub:#5B6676}
@media (prefers-color-scheme:dark){:root{--bg:#10151E;--ink:#E7ECF3;--line:#2B3443;--sub:#97A3B6}}
body{margin:0;min-height:100vh;display:grid;place-items:center;background:var(--bg);color:var(--ink);font-family:system-ui,-apple-system,"Apple SD Gothic Neo",sans-serif}
form{width:min(320px,90vw);display:grid;gap:12px}
h1{font-size:22px;margin:0 0 6px}
input{font-size:16px;height:44px;padding:0 12px;border:1px solid var(--line);border-radius:10px;background:transparent;color:var(--ink)}
button{height:44px;border:0;border-radius:10px;background:var(--ink);color:var(--bg);font-size:16px;font-weight:700;white-space:nowrap}
p{color:#E0313A;margin:0;font-size:14px}</style></head><body>
<form method="post"><h1>다봤니 관리자</h1>${msg ? `<p>${msg}</p>` : ''}<input type="password" name="pw" autocomplete="current-password" placeholder="비밀번호" autofocus><button>들어가기</button></form></body></html>`;
const html = (s, extra = {}) => new Response(s, {headers: {'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store', ...extra}});
export async function onRequestGet({request, env}){
  const u = new URL(request.url);
  if (u.searchParams.has('logout')) return new Response(null, {status: 302, headers: {Location: '/', 'Set-Cookie': 'dwa=; Path=/; Max-Age=0; Secure; HttpOnly; SameSite=Lax'}});
  return html(page());
}
export async function onRequestPost({request, env}){
  if (!env.ADMIN_PASSWORD) return html(page('서버에 ADMIN_PASSWORD가 설정되지 않았습니다.'), {});
  const f = await request.formData();
  if ((f.get('pw') || '') !== env.ADMIN_PASSWORD) return html(page('비밀번호가 맞지 않습니다.'));
  return new Response(null, {status: 302, headers: {Location: '/', 'Set-Cookie': `dwa=${await token(env)}; Path=/; Max-Age=31536000; Secure; HttpOnly; SameSite=Lax`}});
}
