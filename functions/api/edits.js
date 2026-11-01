// 직접 수정 목록. KV(EDITS)의 'edits' 한 칸에 모두 담음
// 모양: { w: { 작품번호: { 칸: {v, mode:'fixed'|'temp', base, at} } }, p: { 인물번호: { ko: {…} } } }
// 확정(fixed)은 언제나 적용, 임시(temp)는 원천 값이 수정할 때의 값(base)과 같을 때만 적용 (사이트에서 판단)
import { isAdmin } from '../_auth.js';
const FIELDS = {w: ['title', 'ko', 'e', 'y', 'q', 'ty', 'd'], p: ['ko']};
const load = async env => JSON.parse((await env.EDITS.get('edits')) || '{"w":{},"p":{}}');
export async function onRequestGet({env}){
  if (!env.EDITS) return Response.json({w: {}, p: {}}, {headers: {'Cache-Control': 'no-store'}});
  return new Response(JSON.stringify(await load(env)), {headers: {'Content-Type': 'application/json', 'Cache-Control': 'no-store'}});
}
export async function onRequestPost({request, env}){
  if (!(await isAdmin(request, env))) return Response.json({error: '관리자만 수정할 수 있습니다.'}, {status: 403});
  if (!env.EDITS) return Response.json({error: '서버에 EDITS 저장소가 연결되지 않았습니다.'}, {status: 500});
  const b = await request.json();
  const scope = b.scope === 'p' ? 'p' : 'w', id = String(b.id || ''), mode = b.mode === 'temp' ? 'temp' : 'fixed';
  if (!id || id.length > 120) return Response.json({error: '잘못된 번호'}, {status: 400});
  const all = await load(env); all[scope] = all[scope] || {};
  const cur = all[scope][id] || {};
  for (const [f, v] of Object.entries(b.changes || {})) {
    if (!FIELDS[scope].includes(f)) continue;
    if (v === null || v === '') delete cur[f];
    else cur[f] = {v, mode, base: (b.base || {})[f] ?? null, at: new Date().toISOString().slice(0, 10)};
  }
  if (Object.keys(cur).length) all[scope][id] = cur; else delete all[scope][id];
  await env.EDITS.put('edits', JSON.stringify(all));
  return Response.json(all, {headers: {'Cache-Control': 'no-store'}});
}
