import { ready, session, json } from './_g.js';
export async function onRequestGet({request, env}){
  const s = ready(env) ? await session(request, env) : null;
  return json({ready: ready(env), connected: !!s, email: s?.email || null});
}
