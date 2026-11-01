import { isAdmin } from '../_auth.js';
export async function onRequestGet({request, env}){
  return Response.json({admin: await isAdmin(request, env)}, {headers: {'Cache-Control': 'no-store'}});
}
