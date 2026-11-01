import { ready, rid, redirectUri, cookie } from './_g.js';
const back = (hash, extra = []) => { const h = new Headers({Location: '/#' + hash, 'Cache-Control': 'no-store'}); extra.forEach(c => h.append('Set-Cookie', c)); return new Response(null, {status: 302, headers: h}); };
export async function onRequestGet({request, env}){
  if (!ready(env)) return back('sync=nosetup');
  const u = new URL(request.url), code = u.searchParams.get('code'), state = u.searchParams.get('state');
  if (u.searchParams.get('error') || !code) return back('sync=cancel');
  if (!state || state !== cookie(request, 'gst')) return back('sync=badstate');
  const r = await fetch('https://oauth2.googleapis.com/token', {method: 'POST', headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    body: new URLSearchParams({code, client_id: env.GOOGLE_CLIENT_ID, client_secret: env.GOOGLE_CLIENT_SECRET, redirect_uri: redirectUri(request), grant_type: 'authorization_code'})});
  const t = await r.json();
  if (!r.ok || !t.refresh_token) return back('sync=fail');
  let email = null;
  try { email = JSON.parse(atob(t.id_token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/'))).email || null; } catch {}
  const sid = rid();
  await env.EDITS.put('gs:' + sid, JSON.stringify({rt: t.refresh_token, email, at: Date.now()}));
  return back('sync=ok', [`dws=${sid}; Path=/; Max-Age=63072000; Secure; HttpOnly; SameSite=Lax`, 'gst=; Path=/api/gauth; Max-Age=0; Secure; HttpOnly; SameSite=Lax']);
}
