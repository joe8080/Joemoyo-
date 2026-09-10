// Mary Jane Agent OS gateway — the control plane behind the board.
//
// This is the Chief's `agent-os` edge function with additive changes for the
// JoeMoyo board (every original action keeps its behaviour):
//   GET                      serves the Agent OS board (board.html, read from
//                            agent_os_config.board_html — see publish_board.py)
//   dashboard (admin)        + per-agent board state, recent runs, latest metrics
//   register_agent (admin)   + notes, board metadata
//   issue_agent_key (admin)  + board metadata
//   heartbeat (agent)        + status / task / result / note / metrics → the card's
//                              "Now / Last" line; done/error logs a run + event
//   whoami (agent)           the agent's roster row (status → paused?)
//
// Deploy: cd agent_os/edge && supabase functions deploy agent-os --no-verify-jwt
// Board:  python main.py os publish-board   (uploads board.html into the DB)
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "@supabase/supabase-js";

const enc = new TextEncoder();
const CORS = {
  "access-control-allow-origin": "*",
  "access-control-allow-headers": "content-type,x-agent-os-key,x-agent-key",
  "access-control-allow-methods": "GET,POST,OPTIONS",
};
const PAGE_CSP = "default-src 'self'; style-src 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; script-src 'unsafe-inline'; connect-src 'self'; img-src 'self' data:";
const HEARTBEAT_STATUSES = ["online", "running", "done", "idle", "error", "standby"];

function json(body, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { ...CORS, "content-type": "application/json; charset=utf-8", "cache-control": "no-store", "x-content-type-options": "nosniff" } });
}
async function sha256(v) {
  const d = await crypto.subtle.digest("SHA-256", enc.encode(v));
  return Array.from(new Uint8Array(d), b => b.toString(16).padStart(2, "0")).join("");
}
function safeEq(a,b) {
  if (a.length !== b.length) return false;
  let x=0; for(let i=0;i<a.length;i++) x |= a.charCodeAt(i)^b.charCodeAt(i); return x===0;
}
function makeToken(prefix) {
  const bytes=new Uint8Array(32); crypto.getRandomValues(bytes);
  const s=btoa(String.fromCharCode(...bytes)).replaceAll("+","-").replaceAll("/","_").replaceAll("=","");
  return `${prefix}_${s}`;
}
function dbClient() {
  const url=Deno.env.get("SUPABASE_URL")??"";
  const secretKeys=JSON.parse(Deno.env.get("SUPABASE_SECRET_KEYS")??"{}");
  const key=secretKeys.default??Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")??"";
  if(!url||!key) throw new Error("server_configuration_error");
  return createClient(url,key,{auth:{persistSession:false,autoRefreshToken:false}});
}
function supervisorOf(reportsTo){ return reportsTo && reportsTo!=="user" ? reportsTo : null; }
function clip(v, n){ return String(v ?? "").slice(0, n); }
function isObj(v){ return v && typeof v === "object" && !Array.isArray(v); }

async function adminOK(req,db){
  const supplied=req.headers.get("x-agent-os-key")??"";
  if(!supplied.startsWith("mjos_")||supplied.length<30) return false;
  const {data}=await db.from("agent_os_config").select("config_value").eq("config_key","admin_auth").maybeSingle();
  const expected=String(data?.config_value?.sha256??"");
  return expected.length===64 && safeEq(await sha256(supplied),expected);
}
async function agentAuth(req,db){
  const supplied=req.headers.get("x-agent-key")??"";
  if(!supplied.startsWith("agent_")||supplied.length<30) return null;
  const h=await sha256(supplied);
  const {data,error}=await db.from("agent_connections").select("agent_key,scopes,active").eq("key_hash",h).eq("active",true).maybeSingle();
  if(error||!data) return null;
  return data;
}
async function issueAgentKey(db,agentKey,metadata){
  const {data:r,error}=await db.from("agent_ops_roster").select("agent_key,provider,model,grok_agent_id,capabilities").eq("agent_key",agentKey).maybeSingle();
  if(error||!r) throw new Error("unknown_agent");
  const token=makeToken(`agent_${agentKey}`), h=await sha256(token);
  const row={agent_key:agentKey,provider:r.provider,model:r.model,external_agent_id:r.grok_agent_id,connection_type:r.grok_agent_id?"grok_agent":"api",key_hash:h,scopes:r.capabilities??[],active:true,updated_at:new Date().toISOString()};
  if(isObj(metadata)) row.metadata=metadata;
  const {error:e}=await db.from("agent_connections").upsert(row,{onConflict:"agent_key"});
  if(e) throw e;
  return token;
}
async function dashboard(db){
  const [agents,tasks,approvals,events,handoffs,queue,roster,conns,runs,metrics]=await Promise.all([
    db.from("v_agent_os_agents").select("*").order("role").order("display_name"),
    db.from("agent_tasks").select("id,title,domain,task_type,priority,status,assigned_to_agent,assigned_to_supervisor,requires_approval,due_at,error,created_at,updated_at").order("created_at",{ascending:false}).limit(100),
    db.from("agent_approvals").select("id,task_id,requested_by_agent,approval_type,action_summary,risk_level,status,requested_at,decided_at,decision_note,payload").order("requested_at",{ascending:false}).limit(60),
    db.from("agent_events").select("id,event_type,source_agent,source_system,domain,severity,subject,created_at,processed_at").order("created_at",{ascending:false}).limit(100),
    db.from("agent_handoffs").select("id,task_id,from_agent,to_agent,handoff_type,status,created_at,completed_at").order("created_at",{ascending:false}).limit(60),
    db.rpc("agent_os_queue_metrics"),
    db.from("agent_ops_roster").select("agent_key,heartbeat_status,notes,updated_at"),
    db.from("agent_connections").select("agent_key,metadata,last_error,active"),
    db.from("agent_ops_runs").select("id,agent_key,run_type,checklist,result,summary,metrics,created_at").order("created_at",{ascending:false}).limit(60),
    db.from("agent_ops_metrics").select("as_of_date,domain,metric_key,metric_value,metric_text,unit,direction,source_agent,notes,created_at").order("as_of_date",{ascending:false}).order("created_at",{ascending:false}).limit(80)
  ]);
  for(const r of [agents,tasks,approvals,events,handoffs,queue,roster,conns,runs,metrics]) if(r.error) throw new Error(r.error.message);
  const a=agents.data??[],t=tasks.data??[],ap=approvals.data??[];
  const byKey=Object.fromEntries((roster.data??[]).map(r=>[r.agent_key,r]));
  const connByKey=Object.fromEntries((conns.data??[]).filter(c=>c.active).map(c=>[c.agent_key,c]));
  for(const x of a){
    const r=byKey[x.agent_key]??{}, c=connByKey[x.agent_key]??{};
    x.heartbeat_status=r.heartbeat_status??"unknown"; x.notes=r.notes??null; x.updated_at=r.updated_at??null;
    x.board=isObj(c.metadata)&&isObj(c.metadata.board)?c.metadata.board:null; x.last_error=c.last_error??null;
  }
  return {generated_at:new Date().toISOString(),agents:a,tasks:t,approvals:ap,events:events.data??[],handoffs:handoffs.data??[],runs:runs.data??[],metrics:metrics.data??[],queue:(queue.data??[])[0]??null,
    summary:{agents:a.length,active_agents:a.filter(x=>x.status==="active").length,os_linked:a.filter(x=>x.agent_os_api_connected===true).length,legacy_live:a.filter(x=>String(x.live_status).startsWith("legacy_")).length,open_tasks:t.filter(x=>!["completed","failed","cancelled"].includes(x.status)).length,pending_approvals:ap.filter(x=>x.status==="pending").length,failures_24h:a.filter(x=>x.last_result==="FAIL"&&x.last_run_at&&Date.now()-new Date(x.last_run_at).getTime()<86400000).length}};
}

// The board page (agent_os/board.html) lives in agent_os_config under
// config_key "board_html" — publish it with `python main.py os publish-board`.
// It is cached per instance for 60s so GETs stay cheap.
let boardCache={html:"",at:0};
const FALLBACK_PAGE=`<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Mary Jane Agent OS</title></head><body style="font-family:system-ui,sans-serif;background:#131211;color:#EFE8DC;padding:40px;line-height:1.5"><h1 style="font-weight:800">Agent OS</h1><p>The gateway is up, but the board page is not installed yet.</p><p>From the JoeMoyo repo run: <code>python main.py os publish-board</code></p></body></html>`;
async function boardPage(){
  if(boardCache.html&&Date.now()-boardCache.at<60000) return boardCache.html;
  try{
    const db=dbClient();
    const {data}=await db.from("agent_os_config").select("config_value").eq("config_key","board_html").maybeSingle();
    const html=String(data?.config_value?.html??"");
    if(html){boardCache={html,at:Date.now()};return html;}
  }catch(_e){/* fall through to the placeholder */}
  return FALLBACK_PAGE;
}

Deno.serve(async req=>{
  if(req.method==="OPTIONS") return new Response("ok",{headers:CORS});
  if(req.method==="GET") return new Response(await boardPage(),{headers:{"content-type":"text/html; charset=utf-8","cache-control":"no-store","x-content-type-options":"nosniff","content-security-policy":PAGE_CSP}});
  if(req.method!=="POST") return json({error:"method_not_allowed"},405);
  const db=dbClient(),body=await req.json().catch(()=>({})),action=String(body.action??"");

  const adminActions=new Set(["dashboard","issue_agent_key","register_agent","create_task","decide_approval","set_agent_status"]);
  if(adminActions.has(action)){
    if(!(await adminOK(req,db))) return json({error:"unauthorised"},401);
    try{
      if(action==="dashboard") return json(await dashboard(db));
      if(action==="issue_agent_key"){
        const agentKey=String(body.agent_key??"").trim();if(!agentKey)return json({error:"agent_key_required"},400);
        const token=await issueAgentKey(db,agentKey,body.metadata);
        await db.from("agent_events").insert({event_type:"agent_key_issued",source_system:"agent-os",domain:"systems",severity:"info",subject:`OS key issued for ${agentKey}`,payload:{agent_key:agentKey}});
        return json({agent_key:agentKey,agent_key_secret:token,endpoint:`${Deno.env.get("SUPABASE_URL")}/functions/v1/agent-os`,header:"x-agent-key",shown_once:true});
      }
      if(action==="register_agent"){
        const agentKey=String(body.agent_key??"").trim().toLowerCase();if(!/^[a-z0-9_]{2,60}$/.test(agentKey))return json({error:"invalid_agent_key"},400);
        const row={agent_key:agentKey,display_name:String(body.display_name??agentKey).slice(0,120),role:String(body.role??"worker"),status:"active",domain:String(body.domain??"ops").slice(0,80),reports_to:String(body.reports_to??"chief"),provider:String(body.provider??"unassigned"),connection_mode:"api",capabilities:Array.isArray(body.capabilities)?body.capabilities:[],notes:clip(body.notes??"Registered through Mary Jane Agent OS",600),updated_at:new Date().toISOString()};
        const {error}=await db.from("agent_ops_roster").upsert(row,{onConflict:"agent_key"});if(error)throw error;
        const token=await issueAgentKey(db,agentKey,body.metadata);
        await db.from("agent_permissions").upsert({agent_key:agentKey,capability:"user_interface",action:"speak_directly",mode:"deny",limits:{},notes:"Reports through Mary Jane Chief."},{onConflict:"agent_key,capability,action"});
        await db.from("agent_events").insert({event_type:"agent_registered",source_system:"agent-os",domain:row.domain,subject:`${row.display_name} registered`,payload:{agent_key:agentKey}});
        return json({agent_key:agentKey,agent_key_secret:token,endpoint:`${Deno.env.get("SUPABASE_URL")}/functions/v1/agent-os`,header:"x-agent-key",shown_once:true},201);
      }
      if(action==="create_task"){
        const assigned=String(body.assigned_to_agent??"").trim();const {data:r}=await db.from("agent_ops_roster").select("agent_key,reports_to,domain").eq("agent_key",assigned).maybeSingle();if(!r)return json({error:"unknown_assigned_agent"},400);
        const row={created_by_agent:"chief",assigned_to_agent:assigned,assigned_to_supervisor:supervisorOf(r.reports_to),domain:String(body.domain??r.domain),task_type:String(body.task_type??"work"),title:String(body.title??"").slice(0,240),instructions:String(body.instructions??"").slice(0,20000),context:body.context??{},priority:Math.max(1,Math.min(Number(body.priority??3),5)),requires_approval:Boolean(body.requires_approval),due_at:body.due_at??null};if(!row.title||!row.instructions)return json({error:"title_and_instructions_required"},400);
        const {data,error}=await db.from("agent_tasks").insert(row).select("*").single();if(error)throw error;await db.from("agent_events").insert({event_type:"task_created",source_agent:"chief",domain:row.domain,subject:row.title,task_id:data.id,payload:{assigned_to_agent:assigned}});return json({task:data},201);
      }
      if(action==="decide_approval"){
        const id=String(body.approval_id??""),status=String(body.status??"");if(!["approved","rejected"].includes(status))return json({error:"invalid_decision"},400);
        const {data:a,error}=await db.from("agent_approvals").update({status,decided_at:new Date().toISOString(),decided_by:"user",decision_note:String(body.note??"").slice(0,4000)}).eq("id",id).eq("status","pending").select("*").maybeSingle();if(error)throw error;if(!a)return json({error:"approval_not_pending"},409);
        if(a.task_id)await db.from("agent_tasks").update({status:status==="approved"?"pending":"blocked",approval_id:a.id,updated_at:new Date().toISOString()}).eq("id",a.task_id);
        await db.from("agent_events").insert({event_type:"approval_decided",source_system:"agent-os",domain:"ops",severity:status==="approved"?"info":"amber",subject:`Approval ${status}: ${a.action_summary}`,task_id:a.task_id,payload:{approval_id:a.id}});return json({approval:a});
      }
      if(action==="set_agent_status"){
        const key=String(body.agent_key??""),status=String(body.status??"");if(!["active","stalled","paused","retired"].includes(status))return json({error:"invalid_status"},400);const {error}=await db.from("agent_ops_roster").update({status,updated_at:new Date().toISOString()}).eq("agent_key",key);if(error)throw error;
        await db.from("agent_events").insert({event_type:"agent_status_set",source_system:"agent-os",domain:"systems",severity:status==="active"?"info":"amber",subject:`${key} set to ${status}`,payload:{agent_key:key,status}});
        return json({ok:true});
      }
    }catch(e){return json({error:e instanceof Error?e.message:"admin_action_failed"},500)}
  }

  const agent=await agentAuth(req,db);if(!agent)return json({error:"agent_unauthorised"},401);const agentKey=String(agent.agent_key);
  try{
    if(action==="whoami"){
      const {data:r}=await db.from("agent_ops_roster").select("agent_key,display_name,role,status,domain,reports_to,heartbeat_status,last_seen_at").eq("agent_key",agentKey).maybeSingle();
      const {data:c}=await db.from("agent_connections").select("metadata").eq("agent_key",agentKey).maybeSingle();
      return json({...(r??{agent_key:agentKey}),paused:r?.status==="paused",board:isObj(c?.metadata)&&isObj(c.metadata.board)?c.metadata.board:null});
    }
    if(action==="heartbeat"){
      const now=new Date().toISOString();
      const {data:r}=await db.from("agent_ops_roster").select("status,domain").eq("agent_key",agentKey).maybeSingle();
      const {data:c}=await db.from("agent_connections").select("metadata").eq("agent_key",agentKey).maybeSingle();
      const meta=isObj(c?.metadata)?c.metadata:{}; const prev=isObj(meta.board)?meta.board:{};
      // A plain heartbeat (no status) means "alive": online — unless it carries
      // a task line while a run is in progress, which keeps it running.
      const status=body.status!==undefined&&body.status!==null?String(body.status):(body.task!==undefined&&prev.status==="running"?"running":"online");
      if(!HEARTBEAT_STATUSES.includes(status))return json({error:"invalid_status"},400);
      const board={...prev,status,updated_at:now};
      if(body.source_system!==undefined) board.source=clip(body.source_system,80);
      if(body.task!==undefined) board.task=clip(body.task,300);
      if(status==="running"&&prev.status!=="running"){board.started_at=now;board.result=null;board.note=null;board.finished_at=null;board.duration_s=null;}
      if(body.result!==undefined) board.result=clip(body.result,600);
      if(body.note!==undefined) board.note=clip(body.note,600);
      if(isObj(body.metrics)) board.metrics={...(isObj(prev.metrics)?prev.metrics:{}),...body.metrics};
      if(["done","error","idle"].includes(status)&&prev.status==="running"&&prev.started_at){board.finished_at=now;board.duration_s=Math.max(0,Math.round((Date.parse(now)-Date.parse(prev.started_at))/1000));}
      await Promise.all([
        db.from("agent_connections").update({last_seen_at:now,last_error:null,metadata:{...meta,board},updated_at:now}).eq("agent_key",agentKey),
        db.from("agent_ops_roster").update({last_seen_at:now,heartbeat_status:status,updated_at:now}).eq("agent_key",agentKey)]);
      if((status==="done"||status==="error")&&body.log_run!==false&&(board.result||board.note||board.task)){
        const ok=status==="done", summary=clip(ok?(board.result||board.task):(board.note||board.task),5000);
        await db.from("agent_ops_runs").insert({agent_key:agentKey,run_type:clip(body.run_type??"heartbeat",80),checklist:"Agent OS heartbeat",result:ok?"PASS":"FAIL",summary,metrics:isObj(body.metrics)?body.metrics:{}});
        await db.from("agent_events").insert({event_type:ok?"run_finished":"run_failed",source_agent:agentKey,source_system:board.source??"agent-api",domain:r?.domain??"ops",severity:ok?"info":"red",subject:clip(summary,1000),payload:{task:board.task??null,result:board.result??null,note:board.note??null,metrics:isObj(body.metrics)?body.metrics:{}}});
      }
      return json({ok:true,agent_key:agentKey,server_time:now,status:r?.status??"active",paused:r?.status==="paused"});
    }
    if(action==="pull_tasks"){
      const {data,error}=await db.from("agent_tasks").select("*").eq("assigned_to_agent",agentKey).in("status",["pending","claimed","running"]).order("priority",{ascending:false}).order("created_at",{ascending:true}).limit(Math.max(1,Math.min(Number(body.limit??10),25)));if(error)throw error;return json({tasks:data??[]});
    }
    if(action==="claim_task"){
      const id=String(body.task_id??"");const {data,error}=await db.from("agent_tasks").update({status:"claimed",claimed_at:new Date().toISOString(),attempt_count:Number(body.attempt_count??1),updated_at:new Date().toISOString()}).eq("id",id).eq("assigned_to_agent",agentKey).eq("status","pending").select("*").maybeSingle();if(error)throw error;if(!data)return json({error:"task_not_claimable"},409);return json({task:data});
    }
    if(action==="start_task"){
      const id=String(body.task_id??"");const {data,error}=await db.from("agent_tasks").update({status:"running",started_at:new Date().toISOString(),updated_at:new Date().toISOString()}).eq("id",id).eq("assigned_to_agent",agentKey).in("status",["pending","claimed"]).select("*").maybeSingle();if(error)throw error;if(!data)return json({error:"task_not_startable"},409);return json({task:data});
    }
    if(action==="complete_task"||action==="fail_task"){
      const id=String(body.task_id??""),ok=action==="complete_task",patch={status:ok?"completed":"failed",result:ok?(body.result??{}):null,error:ok?null:String(body.error??"agent_failed").slice(0,10000),completed_at:new Date().toISOString(),updated_at:new Date().toISOString()};
      const {data,error}=await db.from("agent_tasks").update(patch).eq("id",id).eq("assigned_to_agent",agentKey).in("status",["claimed","running"]).select("*").maybeSingle();if(error)throw error;if(!data)return json({error:"task_not_completable"},409);
      await db.from("agent_ops_runs").insert({agent_key:agentKey,run_type:"agent_os_task",result:ok?"PASS":"FAIL",summary:ok?String(body.summary??data.title).slice(0,5000):String(body.error??data.title).slice(0,5000),metrics:{task_id:id}});await db.from("agent_events").insert({event_type:ok?"task_completed":"task_failed",source_agent:agentKey,domain:data.domain,severity:ok?"info":"red",subject:data.title,task_id:id,payload:ok?(body.result??{}):{error:patch.error}});return json({task:data});
    }
    if(action==="handoff"){
      const id=String(body.task_id??""),to=String(body.to_agent??"");const {data:task}=await db.from("agent_tasks").select("*").eq("id",id).eq("assigned_to_agent",agentKey).in("status",["pending","claimed","running","blocked"]).maybeSingle();if(!task)return json({error:"task_not_owned_or_handoffable"},403);const {data:target}=await db.from("agent_ops_roster").select("agent_key,reports_to").eq("agent_key",to).maybeSingle();if(!target)return json({error:"unknown_target_agent"},400);
      const {data:h,error}=await db.from("agent_handoffs").insert({task_id:id,from_agent:agentKey,to_agent:to,handoff_type:String(body.handoff_type??"delegate"),context:body.context??{},status:"sent"}).select("*").single();if(error)throw error;await db.from("agent_tasks").update({assigned_to_agent:to,assigned_to_supervisor:supervisorOf(target.reports_to),status:"pending",updated_at:new Date().toISOString()}).eq("id",id);return json({handoff:h});
    }
    if(action==="request_approval"){
      const taskId=body.task_id?String(body.task_id):null;if(taskId){const {data:t}=await db.from("agent_tasks").select("id").eq("id",taskId).eq("assigned_to_agent",agentKey).in("status",["pending","claimed","running"]).maybeSingle();if(!t)return json({error:"task_not_approval_eligible"},409)}
      const risk=String(body.risk_level??"medium");if(!["low","medium","high","critical"].includes(risk))return json({error:"invalid_risk_level"},400);const summary=String(body.action_summary??"").trim();if(!summary)return json({error:"action_summary_required"},400);
      const {data:a,error}=await db.from("agent_approvals").insert({task_id:taskId,requested_by_agent:agentKey,approval_type:String(body.approval_type??"external_action"),action_summary:summary.slice(0,1000),risk_level:risk,payload:body.payload??{},expires_at:body.expires_at??null}).select("*").single();if(error)throw error;if(taskId)await db.from("agent_tasks").update({status:"waiting_approval",requires_approval:true,approval_id:a.id,updated_at:new Date().toISOString()}).eq("id",taskId);return json({approval:a},201);
    }
    if(action==="emit_event"){
      const sev=String(body.severity??"info");if(!["info","amber","red"].includes(sev))return json({error:"invalid_severity"},400);const {data,error}=await db.from("agent_events").insert({event_type:String(body.event_type??"agent_event"),source_agent:agentKey,source_system:String(body.source_system??"agent-api"),domain:String(body.domain??"ops"),severity:sev,subject:String(body.subject??"Agent event").slice(0,1000),payload:body.payload??{},task_id:body.task_id??null,dedupe_key:body.dedupe_key??null}).select("*").single();if(error)throw error;return json({event:data},201);
    }
    if(action==="permissions"){const {data,error}=await db.from("agent_permissions").select("capability,action,mode,limits,notes").eq("agent_key",agentKey).eq("active",true);if(error)throw error;return json({agent_key:agentKey,permissions:data??[]})}
    if(action==="context"){const {data,error}=await db.from("agent_ops_knowledge").select("knowledge_key,domain,title,body,importance,metadata,updated_at").eq("shared",true).eq("status","active").order("importance",{ascending:false}).order("updated_at",{ascending:false}).limit(60);if(error)throw error;return json({agent_key:agentKey,knowledge:data??[]})}
    return json({error:"unknown_action"},400);
  }catch(e){await db.from("agent_connections").update({last_error:e instanceof Error?e.message:"agent_action_failed",updated_at:new Date().toISOString()}).eq("agent_key",agentKey);return json({error:e instanceof Error?e.message:"agent_action_failed"},500)}
});
