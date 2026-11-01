// 구글 동기화: 로그인 유지(갱신 토큰)는 서버 KV(EDITS)에 'gs:<세션>'으로 보관, 브라우저에는 세션 번호 쿠키(dws)만
export const SCOPE = 'https://www.googleapis.com/auth/drive.appdata openid email';
export const ready = env => !!(env.GOOGLE_CLIENT_ID && env.GOOGLE_CLIENT_SECRET && env.EDITS);
export const cookie = (req, name) => ((req.headers.get('Cookie') || '').match(new RegExp('(?:^|;\\s*)' + name + '=([A-Za-z0-9_-]+)')) || [])[1] || null;
export const rid = () => [...crypto.getRandomValues(new Uint8Array(24))].map(b => b.toString(16).padStart(2, '0')).join('');
export const redirectUri = req => new URL(req.url).origin + '/api/gauth/callback';
export async function session(req, env){
  const sid = cookie(req, 'dws'); if (!sid || !env.EDITS) return null;
  const s = await env.EDITS.get('gs:' + sid, 'json'); return s ? {sid, ...s} : null;
}
export const json = (o, status = 200) => Response.json(o, {status, headers: {'Cache-Control': 'no-store'}});
