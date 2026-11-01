import { ready, rid, redirectUri, SCOPE } from './_g.js';
export async function onRequestGet({request, env}){
  if (!ready(env)) return new Response('서버에 구글 설정이 없습니다.', {status: 500});
  const state = rid();
  const u = new URL('https://accounts.google.com/o/oauth2/v2/auth');
  u.search = new URLSearchParams({client_id: env.GOOGLE_CLIENT_ID, redirect_uri: redirectUri(request), response_type: 'code', scope: SCOPE,
    access_type: 'offline', prompt: 'consent', include_granted_scopes: 'true', state}).toString();
  return new Response(null, {status: 302, headers: {Location: u.toString(), 'Set-Cookie': `gst=${state}; Path=/api/gauth; Max-Age=600; Secure; HttpOnly; SameSite=Lax`}});
}
