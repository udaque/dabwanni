// 관리자 확인: ADMIN_PASSWORD로 만든 서명 값을 쿠키(dwa)에 넣어 둠 (픽픽과 같은 방식)
export async function token(env){
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(env.ADMIN_PASSWORD || ''), {name: 'HMAC', hash: 'SHA-256'}, false, ['sign']);
  const sig = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode('dabwanni-admin-v1'));
  return [...new Uint8Array(sig)].map(b => b.toString(16).padStart(2, '0')).join('');
}
export async function isAdmin(request, env){
  if (!env.ADMIN_PASSWORD) return false;
  const c = request.headers.get('Cookie') || '';
  const m = c.match(/(?:^|;\s*)dwa=([0-9a-f]+)/);
  return !!m && m[1] === await token(env);
}
