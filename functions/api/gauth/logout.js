import { session, json } from './_g.js';
export async function onRequestPost({request, env}){
  const s = await session(request, env);
  if (s) { await env.EDITS.delete('gs:' + s.sid); try { await fetch('https://oauth2.googleapis.com/revoke?token=' + encodeURIComponent(s.rt), {method: 'POST'}); } catch {} }
  return new Response(JSON.stringify({ok: true}), {headers: {'Content-Type': 'application/json', 'Cache-Control': 'no-store', 'Set-Cookie': 'dws=; Path=/; Max-Age=0; Secure; HttpOnly; SameSite=Lax'}});
}
