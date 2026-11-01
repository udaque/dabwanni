// 브라우저가 드라이브에 쓸 짧은 접근 토큰을 받아 감 (갱신 토큰은 서버에만)
import { ready, session, json } from './_g.js';
export async function onRequestPost({request, env}){
  if (!ready(env)) return json({error: 'nosetup'}, 500);
  const s = await session(request, env); if (!s) return json({error: 'notconnected'}, 401);
  const r = await fetch('https://oauth2.googleapis.com/token', {method: 'POST', headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    body: new URLSearchParams({client_id: env.GOOGLE_CLIENT_ID, client_secret: env.GOOGLE_CLIENT_SECRET, refresh_token: s.rt, grant_type: 'refresh_token'})});
  const t = await r.json();
  if (!r.ok) { if (t.error === 'invalid_grant') await env.EDITS.delete('gs:' + s.sid); return json({error: t.error || 'token'}, 401); }
  return json({access_token: t.access_token, expires_in: t.expires_in, email: s.email});
}
