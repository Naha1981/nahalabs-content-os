import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const API = '/api';

function App() {
  const [query, setQuery] = useState('hair salon');
  const [location, setLocation] = useState('Johannesburg, South Africa');
  const [limit, setLimit] = useState(10);
  const [prospects, setProspects] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [view, setView] = useState('database');
  const [queue, setQueue] = useState([]);
  const [minScore, setMinScore] = useState(0);
  const [status, setStatus] = useState('');
  const [priority, setPriority] = useState('');
  const [patterns, setPatterns] = useState([]);
  const [commandCenter, setCommandCenter] = useState(null);
  const [crm, setCrm] = useState(null);
  const [workspaceData, setWorkspaceData] = useState(null);
  const [dailyOperator, setDailyOperator] = useState(null);
  const [automation, setAutomation] = useState(null);

  const loadDatabase = async () => {
    setLoading(true); setError('');
    try {
      const response = await fetch(`${API}/api/v1/prospects?min_score=${minScore}&status=${status}&priority=${priority}&limit=100`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Prospect database unavailable');
      setProspects(data.prospects || []); setSelected(data.prospects?.[0] ?? null);
    } catch (err) { setError(`${err.message}. Start the backend first.`); }
    finally { setLoading(false); }
  };

  const loadQueue = async () => {
    setLoading(true); setError(''); setView('queue');
    try {
      const response = await fetch(`${API}/api/v1/prospects/outreach-queue?limit=100`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Outreach queue unavailable');
      setQueue(data.queue || []);
      if (data.queue?.length) setSelected(data.queue[0]);
      else setSelected(null);
    } catch (err) { setError(`${err.message}. Start the backend first.`); }
    finally { setLoading(false); }
  };

  const loadPatterns = async () => {
    setLoading(true); setError(''); setView('patterns');
    try {
      const response = await fetch(`${API}/api/v1/patterns?limit=100`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'PatternVault unavailable');
      setPatterns(data.patterns || []);
      setSelected(null);
    } catch (err) { setError(`${err.message}. Start the backend first.`); }
    finally { setLoading(false); }
  };

  const loadDailyOperator = async () => {
    setLoading(true); setError(''); setView('operator'); setSelected(null);
    try {
      const response = await fetch(`${API}/api/v1/daily-operator`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Daily operator unavailable');
      setDailyOperator(data);
    } catch (err) { setError(`${err.message}. Start the backend first.`); }
    finally { setLoading(false); }
  };

  const loadAutomation = async () => {
    setLoading(true); setError(''); setView('automation'); setSelected(null);
    try {
      const [jr, hr] = await Promise.all([fetch(`${API}/api/v1/scheduler/jobs`), fetch(`${API}/api/v1/scheduler/health`)]);
      const jobs = await jr.json(); const health = await hr.json();
      if (!jr.ok) throw new Error(jobs.detail || 'Automation jobs unavailable');
      setAutomation({jobs: jobs.jobs || [], health});
    } catch (err) { setError(`${err.message}. Start the backend first.`); }
    finally { setLoading(false); }
  };

  const loadCommandCenter = async () => {
    setLoading(true); setError(''); setView('command'); setSelected(null);
    try {
      const response = await fetch(`${API}/api/v1/campaign-command-center`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Campaign command center unavailable');
      setCommandCenter(data);
    } catch (err) { setError(`${err.message}. Start the backend first.`); }
    finally { setLoading(false); }
  };

  const runRadar = async () => {
    setLoading(true); setError('');
    try {
      const response = await fetch(`${API}/api/v1/prospects/radar/run`, {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ query, location, limit, headless: true }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Radar API unavailable');
      setProspects(data.prospects || []);
      setSelected(data.prospects?.[0] ?? null);
      if (!data.prospects?.length) setError('No verified prospects returned. Try another category or location.');
    } catch (err) {
      setProspects([]); setSelected(null);
      setError(`${err.message}. Start the backend and browser worker, then run the scan again.`);
    } finally { setLoading(false); }
  };

  const loadCRM=async()=>{try{const r=await fetch(`${API}/api/v1/crm/summary`);const d=await r.json();if(r.ok)setCrm(d)}catch(e){console.error(e)}};
  useEffect(()=>{if(view==='crm')loadCRM()},[view]);
  useEffect(()=>{const h=e=>openWorkspace(e.detail);window.addEventListener('open-prospect-workspace',h);return()=>window.removeEventListener('open-prospect-workspace',h)},[]);
  const openWorkspace=async(p)=>{setLoading(true);setError('');try{const r=await fetch(`${API}/api/v1/prospects/${p.id}/workspace`);const d=await r.json();if(!r.ok)throw new Error(d.detail||'Workspace unavailable');setWorkspaceData(d);setView('workspace');setSelected(p)}catch(e){setError(e.message)}finally{setLoading(false)}};
  return <main className="shell">
    <header className="topbar"><div><strong>NahaLabs Reactivate</strong><span> / v0.38.5</span></div><span>Evidence first · Social Gap explained</span></header>
    <section className="hero compact">
      <div><div className="eyebrow">PROSPECT RADAR</div><h1>Find businesses where the digital audience already exists — but the content engine has gone quiet.</h1>
        <p>The radar now runs discovery → website enrichment → social evidence → scoring. It only presents prospects supported by returned evidence.</p>
        <div className="controls"><button className="secondary" onClick={() => { setView('database'); loadDatabase(); }} disabled={loading}>Saved prospects</button><button className="secondary" onClick={loadQueue} disabled={loading}>Outreach queue {queue.length ? `(${queue.length})` : ''}</button><button className="secondary" onClick={loadPatterns} disabled={loading}>PatternVault</button><button className="secondary" onClick={loadDailyOperator} disabled={loading}>Today's Operator</button><button className="secondary" onClick={loadAutomation}>Automation Control</button><button className="secondary" onClick={loadCommandCenter} disabled={loading}>Campaign Command Center</button><button className="secondary" onClick={()=>setView('crm')} disabled={loading}>CRM Pipeline</button><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Business category"/><input value={location} onChange={e=>setLocation(e.target.value)} placeholder="Location"/><input type="number" min="1" max="50" value={limit} onChange={e=>setLimit(Number(e.target.value))}/><button onClick={runRadar} disabled={loading}>{loading ? 'Scanning…' : 'Run Prospect Radar'}</button><select value={minScore} onChange={e=>setMinScore(Number(e.target.value))}><option value={0}>All scores</option><option value={70}>70+</option><option value={80}>80+</option><option value={90}>90+</option></select><select value={status} onChange={e=>setStatus(e.target.value)}><option value="">All qualification</option><option value="UNQUALIFIED">Unqualified</option><option value="QUALIFIED">Qualified</option><option value="NURTURE">Nurture</option><option value="DISQUALIFIED">Disqualified</option></select><select value={priority} onChange={e=>setPriority(e.target.value)}><option value="">All priority</option><option value="HOT">Hot</option><option value="HIGH">High</option><option value="NORMAL">Normal</option><option value="LOW">Low</option></select></div>
        {error && <div className="notice">{error}</div>}
      </div>
      <div className="radarstat"><span>VISIBLE</span><strong>{prospects.length || '—'}</strong><small>{prospects.length ? `${prospects.length} prospects` : 'No scan yet'}</small></div>
    </section>

    {view === 'automation' ? <AutomationCenter data={automation} onRefresh={loadAutomation} /> : view === 'operator' ? <DailyOperator data={dailyOperator} loading={loading} onRefresh={loadDailyOperator} /> : view === 'patterns' ? <PatternVault patterns={patterns} /> : view === 'workspace' ? <ProspectWorkspace data={workspaceData} onBack={()=>setView('database')} onRefresh={()=>selected&&openWorkspace(selected)} loading={loading} /> : view === 'command' ? <CampaignCommandCenter data={commandCenter} loading={loading} onRefresh={loadCommandCenter} /> : view === 'crm' ? <CRMPipeline data={crm} onRefresh={loadCRM} /> : ((view === 'queue' ? queue : prospects).length > 0) && <section className="workspace">
      <aside className="list panel"><div className="listhead"><small>{view === 'queue' ? 'OUTREACH QUEUE' : 'PROSPECTS'}</small><span>{view === 'queue' ? queue.length : prospects.length}</span></div>
        {(view === 'queue' ? queue : prospects).map((p, i) => <button className={`prospect ${selected === p ? 'selected' : ''}`} key={`${p.name}-${i}`} onClick={() => setSelected(p)}><div><strong>{p.name}</strong><span>{p.category} · {p.city}</span></div><b>{p.score}</b></button>)}
      </aside>
      {selected && <ProspectDetail prospect={selected} />}
    </section>}

    {!prospects.length && !error && <section className="empty panel"><div className="eyebrow">READY</div><h2>Run a live discovery scan to turn businesses into evidence-backed sales prospects.</h2><p>Results will show the public evidence behind the score and explain the Social Gap instead of hiding it inside a number.</p></section>}
  </main>;
}


function ProspectWorkspace({data,onBack,onRefresh,loading}) {
  const p=data?.prospect||{}; const s=data?.summary||{}; const q=data?.qualification||{};
  const counts=data?.revenue?.counts||{};
  const latest=[...(data?.outreach?.events||[]).map(x=>({at:x.occurred_at,type:`OUTREACH · ${x.channel} · ${x.event_type}`,note:x.note})), ...(data?.performance||[]).map(x=>({at:x.observed_at,type:`PERFORMANCE · ${x.platform||'channel'}`,note:`${x.views||0} views · ${x.likes||0} likes · ${x.leads||0} leads`})), ...(data?.opportunities||[]).map(x=>({at:x.updated_at,type:`OPPORTUNITY · ${x.stage}`,note:`R${Number(x.value||0).toLocaleString()} · ${x.name}`})), ...(data?.campaigns||[]).map(x=>({at:x.updated_at,type:`CAMPAIGN · ${x.stage}`,note:x.name}))].sort((a,b)=>String(b.at).localeCompare(String(a.at))).slice(0,12);
  return <section className="workspacehub panel">
    <div className="inthead"><div><div className="eyebrow">UNIFIED PROSPECT WORKSPACE · v0.32</div><h2>{p.name}</h2><p>{p.category} · {p.city} · Score {p.score} · Grade {p.grade}</p></div><div className="formrow"><button className="secondary" onClick={onBack}>Back to prospects</button><button onClick={onRefresh} disabled={loading}>{loading?'Refreshing…':'Refresh'}</button></div></div>
    <div className="workspace-summary"><Metric label="Qualification" value={q.status||'—'} /><Metric label="Priority" value={q.priority||'—'} /><Metric label="Contact" value={q.contact_status||'—'} /><Metric label="Campaigns" value={s.campaigns||0} /><Metric label="Outreach" value={s.outreach||0} /><Metric label="Pipeline" value={`R${Number(s.pipeline_value||0).toLocaleString()}`} /><Metric label="Won" value={`R${Number(s.won_value||0).toLocaleString()}`} /><Metric label="Commercial" value={`R${Number(s.revenue_value||0).toLocaleString()}`} /></div>
    <div className="hubgrid">
      <div className="panel hubpanel"><div className="eyebrow">OPERATING STATE</div><h3>{q.next_action||'No next action recorded.'}</h3><p>{q.notes||'No seller notes recorded.'}</p><div className="hubcounts"><span>{s.content} content</span><span>{s.production} production</span><span>{s.publishing} publishing</span><span>{s.performance} observations</span></div></div>
      <div className="panel hubpanel"><div className="eyebrow">REVENUE SIGNALS</div><div className="reason"><span>Leads</span><b>{counts.LEAD||0}</b></div><div className="reason"><span>Meetings</span><b>{counts.MEETING||0}</b></div><div className="reason"><span>Won events</span><b>{counts.WON||0}</b></div><div className="reason"><span>Recorded revenue</span><b>R{Number(s.revenue_value||0).toLocaleString()}</b></div></div>
    </div>
    <div className="hubgrid">
      <div className="panel hubpanel"><div className="eyebrow">CAMPAIGNS & OPPORTUNITIES</div>{(data?.campaigns||[]).slice(0,6).map(c=><div className="hubitem" key={`c${c.id}`}><b>{c.name}</b><span>{c.stage} · {c.status}</span></div>)}{(data?.opportunities||[]).slice(0,6).map(o=><div className="hubitem" key={`o${o.id}`}><b>{o.name}</b><span>{o.stage} · R{Number(o.value||0).toLocaleString()}</span></div>)}{!data?.campaigns?.length&&!data?.opportunities?.length&&<p>No campaigns or opportunities yet.</p>}</div>
      <div className="panel hubpanel"><div className="eyebrow">RECENT ACTIVITY</div>{latest.map((x,i)=><div className="hubitem" key={i}><b>{x.type}</b><span>{x.note||'—'} · {x.at?new Date(x.at).toLocaleString():'—'}</span></div>)}{!latest.length&&<p>No activity recorded yet.</p>}</div>
    </div>
    <div className="panel hubpanel"><div className="eyebrow">EVIDENCE & CHANNELS</div><div className="evidence-links">{p.website&&<a href={p.website} target="_blank" rel="noreferrer">Website ↗</a>}{p.google_url&&<a href={p.google_url} target="_blank" rel="noreferrer">Google ↗</a>}{(p.channels||[]).filter(x=>x.url).map(x=><a href={x.url} target="_blank" rel="noreferrer" key={x.platform}>{x.platform} ↗</a>)}</div><p>{q.next_action?'Next action: '+q.next_action:'No next action recorded.'}</p></div>
  </section>;
}

function CRMPipeline({data,onRefresh}) {
  const stages=['DISCOVERY','QUALIFIED','PROPOSAL','NEGOTIATION','WON','LOST'];
  const pretty=s=>s.replaceAll('_',' '); const vals=data?.values||{};
  return <section className="command panel"><div className="inthead"><div><div className="eyebrow">CRM & OPPORTUNITY PIPELINE · v0.31</div><h2>Turn commercial intent into a visible pipeline.</h2><p>Explicit opportunity records, deal values, follow-ups and stage history. No revenue is inferred from social metrics.</p></div><button className="secondary" onClick={onRefresh}>Refresh</button></div>
    <div className="commandstats"><div><small>OPEN PIPELINE</small><strong>R{Number(data?.pipeline_value||0).toLocaleString()}</strong></div><div><small>WON</small><strong>R{Number(data?.won_value||0).toLocaleString()}</strong></div>{stages.slice(0,4).map(s=><div key={s}><small>{pretty(s)}</small><strong>{data?.counts?.[s]||0}</strong></div>)}</div>
    <div className="crmboard">{stages.map(stage=><div className="crmcolumn" key={stage}><div className="crmcolhead"><b>{pretty(stage)}</b><span>{data?.counts?.[stage]||0} · R{Number(vals[stage]||0).toLocaleString()}</span></div>{(data?.opportunities||[]).filter(o=>o.stage===stage).map(o=><article className="crmcard" key={o.id}><strong>{o.name}</strong><span>Opportunity #{o.id} · Prospect #{o.prospect_id}</span><b>R{Number(o.value||0).toLocaleString()}</b>{o.next_follow_up_at&&<small>Follow up: {new Date(o.next_follow_up_at).toLocaleString()}</small>}{o.note&&<p>{o.note}</p>}</article>)}{!(data?.opportunities||[]).some(o=>o.stage===stage)&&<div className="crmempty">No opportunities</div>}</div>)}</div>
  </section>;
}

function AutomationCenter({data,onRefresh}) {
  const [busy,setBusy]=useState({});
  const toggle=async(j)=>{setBusy(x=>({...x,[j.id]:true}));try{const r=await fetch(`${API}/api/v1/scheduler/jobs/${j.id}/toggle`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({enabled:!j.enabled})});if(!r.ok)throw new Error('Toggle failed');await onRefresh()}finally{setBusy(x=>({...x,[j.id]:false}))}};
  const run=async(j)=>{setBusy(x=>({...x,[j.id]:true}));try{const r=await fetch(`${API}/api/v1/scheduler/jobs/${j.id}/run`,{method:'POST'});if(!r.ok){const d=await r.json();throw new Error(d.detail||'Run failed')}await onRefresh()}finally{setBusy(x=>({...x,[j.id]:false}))}};
  const h=data?.health||{};
  return <section className="automation panel"><div className="inthead"><div><div className="eyebrow">AUTOMATION CONTROL CENTER · v0.35</div><h2>Control the machine.</h2><p>Scheduled jobs, execution health and manual controls in one place.</p></div><button className="secondary" onClick={onRefresh}>Refresh</button></div>
    <div className="statgrid"><div><small>HEALTH</small><strong>{h.health||'—'}</strong></div><div><small>ENABLED</small><strong>{h.jobs_enabled??'—'}/{h.jobs_total??'—'}</strong></div><div><small>SUCCEEDED</small><strong>{h.runs_succeeded??0}</strong></div><div><small>FAILED</small><strong>{h.runs_failed??0}</strong></div></div>
    <div className="assetgrid">{(data?.jobs||[]).map(j=><article className="asset" key={j.id}><div className="assetmeta"><span className="eyebrow">JOB #{j.id}</span><span className={j.enabled?'queued':'muted'}>{j.enabled?'ENABLED':'DISABLED'}</span></div><h3>{j.name}</h3><p><b>Schedule:</b> {j.cron} · {j.timezone}</p><p><b>Last run:</b> {j.last_run_at||'Never'} · <b>Status:</b> {j.last_status}</p><div className="assetfoot"><button className="secondary" disabled={busy[j.id]} onClick={()=>toggle(j)}>{j.enabled?'Disable':'Enable'}</button><button disabled={busy[j.id]||!j.enabled} onClick={()=>run(j)}>{busy[j.id]?'Running…':'Run now'}</button></div></article>)}</div>
  </section>;
}

function DailyOperator({data,loading,onRefresh}) {
  const actions=data?.actions||[];
  return <section className="command panel">
    <div className="inthead"><div><div className="eyebrow">DAILY OPERATOR · v0.33</div><h2>What needs attention today.</h2><p>Deterministic work surfaced from persisted prospect, campaign, outreach, publishing and CRM data. Nothing is sent or published automatically.</p></div><button className="secondary" onClick={onRefresh} disabled={loading}>{loading?'Refreshing…':'Refresh'}</button></div>
    <div className="commandstats"><div><small>ACTIONS</small><strong>{data?.total_actions||0}</strong></div>{Object.entries(data?.counts||{}).map(([k,v])=><div key={k}><small>{k.replaceAll('_',' ')}</small><strong>{v}</strong></div>)}</div>
    <div className="commandlist">{actions.map((a,i)=><article className="commandrow" key={`${a.kind}-${a.prospect_id}-${a.entity_id||i}`}><div className="commandidentity"><strong>{a.prospect_name}</strong><span>{a.city} · Score {a.score} · {a.seller_priority}</span><small>{a.kind}</small></div><div className="commandstage"><b>{a.action}</b><span>{a.due_at ? `Due ${new Date(a.due_at).toLocaleString()}` : 'Today'}</span></div><div className="commandnext"><small>WHY</small><strong>{a.reason}</strong></div></article>)}{!actions.length&&<div className="empty"><h3>Nothing urgent surfaced.</h3><p>Reactivate found no persisted action requiring attention from the current data.</p></div>}</div>
  </section>;
}

function CampaignCommandCenter({data,loading,onRefresh}) {
  const [filter,setFilter]=useState('ACTIVE');
  const rows=(data?.campaigns||[]).filter(c=>filter==='ALL'||(filter==='ACTIVE'&&!['COMPLETED','BLOCKED'].includes(c.status))||(filter==='BLOCKED'&&c.status==='BLOCKED')||(filter==='APPROVAL'&&c.status==='AWAITING_APPROVAL')||(filter==='PRODUCTION'&&c.status==='IN_PRODUCTION')||(filter==='PUBLISH'&&c.status==='READY_TO_PUBLISH')||(filter==='MEASURE'&&c.status==='MEASURING'));
  const counts=data?.counts||{};
  return <section className="command panel">
    <div className="inthead"><div><div className="eyebrow">CAMPAIGN COMMAND CENTER · v0.30</div><h2>One operating view for every reactivation campaign.</h2><p>See what is moving, what is blocked, and the next human action. State is read from persisted campaign, production, publishing and measurement records.</p></div><button className="secondary" onClick={onRefresh} disabled={loading}>{loading?'Refreshing…':'Refresh'}</button></div>
    <div className="commandstats">
      <div><small>ACTIVE</small><strong>{counts.active||0}</strong></div><div><small>APPROVAL</small><strong>{counts.awaiting_approval||0}</strong></div><div><small>PRODUCTION</small><strong>{counts.in_production||0}</strong></div><div><small>READY TO PUBLISH</small><strong>{counts.ready_to_publish||0}</strong></div><div><small>MEASURING</small><strong>{counts.measuring||0}</strong></div><div><small>BLOCKED</small><strong>{counts.blocked||0}</strong></div>
    </div>
    <div className="commandfilters">{['ACTIVE','ALL','BLOCKED','APPROVAL','PRODUCTION','PUBLISH','MEASURE'].map(x=><button key={x} className={filter===x?'':'secondary'} onClick={()=>setFilter(x)}>{x}</button>)}</div>
    <div className="commandlist">{rows.map(c=><article className="commandrow" key={c.id}>
      <div className="commandidentity"><strong>{c.prospect_name}</strong><span>{c.category} · {c.city} · Score {c.score}</span><small>Campaign #{c.id} · updated {new Date(c.updated_at).toLocaleString()}</small></div>
      <div className="commandstage"><b>{c.stage}</b><span>{c.status}</span></div>
      <div className="commandcounts"><span>{c.asset_ids?.length||0} assets</span><span>{c.production_job_ids?.length||0} production</span><span>{c.publishing_job_ids?.length||0} publishing</span><span>{c.performance_count||0} observations</span><span>{c.outreach_count||0} outreach events</span><span>{c.revenue_leads||0} leads</span><span>{c.meetings||0} meetings</span><span>R{Number(c.commercial_value||0).toLocaleString()} commercial value</span></div>
      <div className="commandnext"><small>NEXT ACTION</small><strong>{c.next_action||'—'}</strong>{c.last_outreach_event&&<span>Last outreach: {c.last_outreach_event} · {c.last_outreach_channel}</span>}{c.blockers?.map((b,i)=><span className="blocker" key={i}>⚠ {b}</span>)}</div>
    </article>)}{!rows.length&&<div className="empty"><h3>No campaigns in this view.</h3><p>Start a campaign from a qualified prospect, then return here to operate it.</p></div>}</div>
  </section>;
}

function PatternVault({patterns}) {
  const [form,setForm]=useState({title:'',source_url:'',source_type:'URL',transcript:'',hook:'',promise:'',structure:'',cta:'',angle:'',audience:'',format:'',emotional_trigger:'',tags:[],notes:''});
  const [saving,setSaving]=useState(false); const [status,setStatus]=useState('');
  const set=(k,v)=>setForm(x=>({...x,[k]:v}));
  const ingest=async()=>{setSaving(true);setStatus('');try{const r=await fetch(`${API}/api/v1/patterns/ingest`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:form.title,source_url:form.source_url,source_type:form.source_type,transcript:form.transcript,audience:form.audience,tags:form.tags,notes:form.notes})});const d=await r.json();if(!r.ok)throw new Error(d.detail||'Could not ingest source');if(!d.saved)throw new Error(d.error||'Source did not produce a verified extract');setStatus(`Ingested and saved: ${d.pattern.title}`);setForm({...form,title:'',source_url:'',transcript:'',notes:''});window.location.reload();}catch(e){setStatus(e.message)}finally{setSaving(false)}};
  const upload=async(e)=>{const file=e.target.files?.[0];if(!file)return;setSaving(true);setStatus('');try{const body=new FormData();body.append('file',file);const r=await fetch(`${API}/api/v1/patterns/ingest-file`,{method:'POST',body});const d=await r.json();if(!r.ok)throw new Error(d.detail||'Could not ingest file');if(!d.saved)throw new Error('No extractable transcript text found');setStatus(`Uploaded and saved: ${d.pattern.title}`);window.location.reload();}catch(err){setStatus(err.message)}finally{setSaving(false);e.target.value=''}};
  const save=async()=>{if(!form.title.trim())return;setSaving(true);try{const r=await fetch(`${API}/api/v1/patterns`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(form)});const d=await r.json();if(!r.ok)throw new Error(d.detail||'Could not save pattern');window.location.reload()}catch(e){setStatus(e.message)}finally{setSaving(false)}};
  return <section className="patternvault panel"><div className="detailhead"><div><div className="eyebrow">CONTENT INTELLIGENCE · PATTERNVAULT v0.16</div><h2>Ingest the source. Extract the pattern.</h2><p>Paste a public page URL, supply a transcript, or upload a text/Markdown/JSON transcript. Video/audio transcription remains a separate worker.</p></div><div className="score"><small>STORED</small><strong>{patterns.length}</strong></div></div><div className="patternform"><input value={form.title} onChange={e=>set('title',e.target.value)} placeholder="Pattern title (optional for URL)"/><input value={form.source_url} onChange={e=>set('source_url',e.target.value)} placeholder="Public source URL"/><textarea value={form.transcript} onChange={e=>set('transcript',e.target.value)} placeholder="Paste transcript/text here (optional if URL is readable)"/><div className="formrow"><button onClick={ingest} disabled={saving}>{saving?'Ingesting…':'Ingest source → PatternVault'}</button><label className="secondary filebtn">Upload transcript<input type="file" accept=".txt,.md,.markdown,.json,text/plain,text/markdown,application/json" onChange={upload} hidden/></label><button className="secondary" onClick={save} disabled={saving||!form.title.trim()}>Save manually</button></div>{status&&<div className="notice">{status}</div>}</div><div className="patternlist">{patterns.map(p=><article className="pattern" key={p.id}><div><div className="eyebrow">{p.format || 'PATTERN'} · {p.source_type}</div><h3>{p.title}</h3><p>{p.hook || p.angle || 'No extracted pattern fields yet.'}</p>{p.source_url&&<a href={p.source_url} target="_blank" rel="noreferrer">Source ↗</a>}</div><div><small>STRUCTURE</small><strong>{p.structure || 'Not extracted'}</strong><small>CTA</small><strong>{p.cta || 'Not extracted'}</strong></div></article>)}</div></section>;
}

function ProspectDetail({ prospect: p }) {
  const gap = p.social_gap;
  const links = useMemo(() => {
    const values = [{label:'Website', url:p.website}, {label:'Google', url:p.google_url}];
    (p.channels || []).forEach(c => c.url && values.push({label:c.platform, url:c.url}));
    return values.filter(x => x.url);
  }, [p]);
  return <section className="detail panel">
    <div className="formrow" style={{justifyContent:'flex-end'}}><button className="secondary" onClick={()=>window.dispatchEvent(new CustomEvent('open-prospect-workspace',{detail:p}))}>Open unified workspace ↗</button></div>
    <div className="detailhead"><div><div className="eyebrow">PROSPECT · {gap?.state || 'UNKNOWN'} · {p.priority || 'NORMAL'}</div><h2>{p.name}</h2><p>{p.category} · {p.city}{p.phone ? ` · ${p.phone}` : ''}</p><small>Seen {p.scan_count || 1} time{(p.scan_count || 1) === 1 ? '' : 's'} · Last scanned {p.last_seen_at ? new Date(p.last_seen_at).toLocaleString() : '—'}</small></div><div className="score"><small>OPPORTUNITY</small><strong>{p.score}</strong><span>Grade {p.grade}</span></div></div>
    <div className="evidence-links">{links.map(l => <a href={l.url} target="_blank" rel="noreferrer" key={l.label}>{l.label} ↗</a>)}</div>
    <div className="metrics"><Metric label="Audience" value={p.channels?.[0]?.followers ? `${p.channels[0].followers.toLocaleString()} followers` : 'Not verified'} /><Metric label="Inactivity" value={p.channels?.[0]?.last_meaningful_post_days != null ? `${p.channels[0].last_meaningful_post_days} days` : 'Not verified'} /><Metric label="Historical activity" value={`${p.historical_activity_score}/100`} /><Metric label="Business health" value={`${p.health_score}/100`} /></div>
    <div className={`gap ${gap?.state === 'OBSERVED' ? 'observed' : 'unverified'}`}><div><div className="eyebrow">SOCIAL GAP · {p.social_gap_score}/100</div><h3>{gap?.headline || 'Social Gap not verified.'}</h3><p>{gap?.details || 'No activity evidence available.'}</p></div><div className="signals">{(gap?.signals || []).map(s => <div key={s.label}><small>{s.label}</small><b>{s.value}</b></div>)}</div></div>
    <Qualification prospect={p} />
    <OutreachIntelligence prospect={p} />
    <ContentConcepts prospect={p} />
    <ContentStudio prospect={p} />
    <CampaignControl prospect={p} />
    <ProductionPipeline prospect={p} />
    <OutreachQueue prospect={p} />
    <div className="bottomgrid"><div><div className="eyebrow">WHY THIS PROSPECT</div>{[['Audience',p.audience_score],['Content dependency',p.content_dependency_score],['Monetization',p.monetization_score],['Competitive gap',p.competitive_gap_score],['Contactability',p.contactability_score]].map(([label,value]) => <div className="reason" key={label}><span>{label}</span><b>{value}/100</b></div>)}</div><div><div className="eyebrow">PUBLIC EVIDENCE</div>{p.evidence?.length ? p.evidence.map((e,i) => <div className="evidence" key={`${e.claim}-${i}`}><div><strong>{e.claim}</strong><span>{e.value}</span></div><a href={e.source_url} target="_blank" rel="noreferrer">{e.state} ↗</a></div>) : <p>No clickable evidence recorded.</p>}</div></div>
  </section>;
}
function Metric({label,value}) { return <div className="metric"><small>{label}</small><strong>{value}</strong></div> }

function Qualification({prospect:p}) {
  const [saving,setSaving]=useState(false);
  const [form,setForm]=useState({qualification_status:p.qualification_status||'UNQUALIFIED',priority:p.priority||'NORMAL',contact_status:p.contact_status||'NOT_CONTACTED',notes:p.notes||'',next_action:p.next_action||''});
  const save=async()=>{setSaving(true); try { const r=await fetch(`${API}/api/v1/prospects/${p.id}/qualification`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify(form)}); const data=await r.json(); if(!r.ok) throw new Error(data.detail||'Could not save'); Object.assign(p,data); } catch(e){ alert(e.message); } finally {setSaving(false);} };
  const launch=async()=>{setSaving(true); try { const r=await fetch(`${API}/api/v1/prospects/${p.id}/campaigns/auto`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:`${p.name} Reactivation`,content_count:3,platform:'INSTAGRAM_REELS'})}); const data=await r.json(); if(!r.ok) throw new Error(data.detail||'Could not launch campaign'); alert(data.created?'Reactivation campaign launched. Review the generated assets.':'An active campaign already exists for this prospect.'); } catch(e){ alert(e.message); } finally {setSaving(false);} };
  const set=(k,v)=>setForm(x=>({...x,[k]:v}));
  return <div className="qualification panel"><div><div className="eyebrow">SALES QUALIFICATION → CAMPAIGN · v0.33</div><h3>Turn evidence into a next action.</h3><p>Qualification is seller-owned. A qualified prospect can now move directly into a guarded reactivation campaign.</p></div><div className="qualgrid"><label>Status<select value={form.qualification_status} onChange={e=>set('qualification_status',e.target.value)}><option>UNQUALIFIED</option><option>QUALIFIED</option><option>NURTURE</option><option>DISQUALIFIED</option></select></label><label>Priority<select value={form.priority} onChange={e=>set('priority',e.target.value)}><option>HOT</option><option>HIGH</option><option>NORMAL</option><option>LOW</option></select></label><label>Contact<select value={form.contact_status} onChange={e=>set('contact_status',e.target.value)}><option>NOT_CONTACTED</option><option>QUEUED</option><option>CONTACTED</option><option>REPLIED</option><option>MEETING</option><option>WON</option><option>LOST</option></select></label><label>Next action<input value={form.next_action} onChange={e=>set('next_action',e.target.value)} placeholder="e.g. Send Social Gap audit"/></label><label className="wide">Notes<textarea value={form.notes} onChange={e=>set('notes',e.target.value)} placeholder="Why is this prospect worth pursuing?"/></label></div><div className="formrow"><button onClick={save} disabled={saving}>{saving?'Saving…':'Save qualification'}</button><button className="secondary" onClick={launch} disabled={saving||form.qualification_status!=='QUALIFIED'}>{saving?'Working…':'Launch reactivation →'}</button></div></div>
}
function OutreachIntelligence({prospect:p}) {
  const [data,setData]=useState(null); const [loading,setLoading]=useState(false); const [open,setOpen]=useState(true);
  const load=async()=>{setLoading(true); try {const r=await fetch(`${API}/api/v1/prospects/${p.id}/outreach-intelligence`); const d=await r.json(); if(!r.ok) throw new Error(d.detail||'Could not load intelligence'); setData(d.intelligence);} catch(e){setData({state:'ERROR',why_it_matters:e.message});} finally {setLoading(false);}};
  useEffect(()=>{if(p.id) load();},[p.id]);
  return <div className="intelligence panel"><div className="inthead"><div><div className="eyebrow">OUTREACH INTELLIGENCE</div><h3>Turn the prospect into the sales asset.</h3><p>Observed evidence → why it matters → content opportunity → human-reviewed outreach.</p></div><button className="secondary" onClick={()=>setOpen(!open)}>{open?'Collapse':'Expand'}</button></div>
    {loading && <p>Building evidence-backed audit…</p>}
    {open && data && <div className="intelgrid"><div><div className="eyebrow">WHAT WE OBSERVED · {data.state}</div>{(data.what_we_observed||[]).slice(0,5).map((e,i)=><div className="evidence" key={i}><div><strong>{e.claim}</strong><span>{e.value}</span></div>{e.source_url&&<a href={e.source_url} target="_blank" rel="noreferrer">{e.state} ↗</a>}</div>)}</div><div><div className="eyebrow">WHY IT MATTERS</div><p>{data.why_it_matters}</p><div className="eyebrow">CONTENT OPPORTUNITIES</div><ul>{(data.content_opportunities||[]).map((x,i)=><li key={i}>{x}</li>)}</ul></div><div><div className="eyebrow">UGC SCRIPT</div><pre>{data.ugc_script}</pre></div><div><div className="eyebrow">FIRST CONTACT</div><textarea readOnly value={data.outreach_message||''}/><small>{data.recommended_action}</small></div></div>}
  </div>;
}

function ContentConcepts({prospect:p}) {
  const [data,setData]=useState(null); const [loading,setLoading]=useState(false);
  const load=async()=>{setLoading(true); try{const r=await fetch(`${API}/api/v1/prospects/${p.id}/content-concepts`); const d=await r.json(); if(!r.ok) throw new Error(d.detail||'Could not load concepts'); setData(d)}catch(e){setData({concepts:[],error:e.message})}finally{setLoading(false)}};
  useEffect(()=>{if(p.id) load()},[p.id]);
  return <div className="concepts panel"><div className="inthead"><div><div className="eyebrow">CONTENT INTELLIGENCE</div><h3>What this business could post next.</h3><p>Concepts use saved structures as inspiration, while the business's own evidence supplies the story.</p></div><button className="secondary" onClick={load}>{loading?'Building…':'Refresh concepts'}</button></div>{data?.error&&<p>{data.error}</p>}<div className="conceptgrid">{(data?.concepts||[]).map((c,i)=><article className="concept" key={i}><div className="eyebrow">{c.format}</div><h4>{c.title}</h4><p><b>Hook:</b> {c.hook}</p><p><b>Angle:</b> {c.angle}</p><p><b>CTA:</b> {c.cta}</p><small>{c.source_pattern} · {c.originality_note}</small></article>)}</div></div>;
}

function ContentStudio({prospect:p}) {
  const [assets,setAssets]=useState([]); const [loading,setLoading]=useState(false); const [generating,setGenerating]=useState(false); const [error,setError]=useState('');
  const load=async()=>{setLoading(true);setError('');try{const r=await fetch(`${API}/api/v1/prospects/${p.id}/content-assets`);const d=await r.json();if(!r.ok)throw new Error(d.detail||'Could not load content assets');setAssets(d.assets||[])}catch(e){setError(e.message)}finally{setLoading(false)}};
  useEffect(()=>{if(p.id)load()},[p.id]);
  const generate=async()=>{setGenerating(true);setError('');try{const r=await fetch(`${API}/api/v1/prospects/${p.id}/content/generate`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({count:3})});const d=await r.json();if(!r.ok)throw new Error(d.detail||'Could not generate content');setAssets(d.assets||[])}catch(e){setError(e.message)}finally{setGenerating(false)}};
  const patch=async(id,updates)=>{const r=await fetch(`${API}/api/v1/content-assets/${id}`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify(updates)});const d=await r.json();if(!r.ok)throw new Error(d.detail||'Could not save content');setAssets(xs=>xs.map(x=>x.id===id?d:x))};
  return <div className="contentstudio panel"><div className="inthead"><div><div className="eyebrow">AI CONTENT ENGINE · v0.17</div><h3>Turn the prospect evidence into production-ready content.</h3><p>Generate scripts and captions from the Social Gap, verified business facts and PatternVault structures. Every asset remains human-reviewable.</p></div><button onClick={generate} disabled={generating}>{generating?'Generating…':'Generate 3 content assets'}</button></div>{loading&&<p>Loading content assets…</p>}{error&&<div className="notice">{error}</div>}<div className="assetgrid">{assets.map(a=><article className="asset" key={a.id}><div className="assetmeta"><span className="eyebrow">{a.type} · {a.verification_state}</span><select value={a.status} onChange={e=>patch(a.id,{status:e.target.value}).catch(e=>setError(e.message))}><option>DRAFT</option><option>REVIEW</option><option>APPROVED</option><option>PRODUCED</option><option>PUBLISHED</option><option>ARCHIVED</option></select></div><input className="assettitle" value={a.title} onChange={e=>setAssets(xs=>xs.map(x=>x.id===a.id?{...x,title:e.target.value}:x))} onBlur={e=>patch(a.id,{title:e.target.value}).catch(e=>setError(e.message))}/><label>Hook<textarea value={a.hook} onChange={e=>setAssets(xs=>xs.map(x=>x.id===a.id?{...x,hook:e.target.value}:x))} onBlur={e=>patch(a.id,{hook:e.target.value}).catch(e=>setError(e.message))}/></label><label>Script<textarea value={a.script} onChange={e=>setAssets(xs=>xs.map(x=>x.id===a.id?{...x,script:e.target.value}:x))} onBlur={e=>patch(a.id,{script:e.target.value}).catch(e=>setError(e.message))}/></label><label>Caption<textarea value={a.caption} onChange={e=>setAssets(xs=>xs.map(x=>x.id===a.id?{...x,caption:e.target.value}:x))} onBlur={e=>patch(a.id,{caption:e.target.value}).catch(e=>setError(e.message))}/></label><div className="assetfoot"><b>CTA:</b> {a.cta}<small>Pattern: {a.pattern_source}</small><small>{a.notes}</small><button className="secondary" disabled={a.status==='DRAFT'} onClick={async()=>{try{const r=await fetch(`${API}/api/v1/content-assets/${a.id}/production`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({platform:'INSTAGRAM_REELS'})});const d=await r.json();if(!r.ok)throw new Error(d.detail||'Could not create production brief');alert(`Production brief #${d.production.id} ready`)}catch(e){setError(e.message)}}}>Create production brief</button></div></article>)}</div></div>;
}

function CampaignControl({prospect:p}) {
  const [campaigns,setCampaigns]=useState([]); const [busy,setBusy]=useState(false); const [msg,setMsg]=useState('');
  const load=async()=>{try{const r=await fetch(`${API}/api/v1/prospects/${p.id}/campaigns`);const d=await r.json();if(r.ok)setCampaigns(d.campaigns||[])}catch(e){setMsg(e.message)}};
  useEffect(()=>{if(p.id)load()},[p.id]);
  const start=async()=>{setBusy(true);setMsg('');try{const r=await fetch(`${API}/api/v1/prospects/${p.id}/campaigns`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:`${p.name} Reactivation`,content_count:3,platform:'INSTAGRAM_REELS'})});const d=await r.json();if(!r.ok)throw new Error(d.detail||'Could not start campaign');setCampaigns(x=>[d,...x]);setMsg('Campaign planned. Review and approve the generated assets before production.')}catch(e){setMsg(e.message)}finally{setBusy(false)}};
  const advance=async(id)=>{setBusy(true);setMsg('');try{const r=await fetch(`${API}/api/v1/campaigns/${id}/advance`,{method:'POST'});const d=await r.json();if(!r.ok)throw new Error(d.detail||'Could not advance campaign');setCampaigns(xs=>xs.map(x=>x.id===id?d:x));setMsg(d.next_action||'Campaign advanced.')}catch(e){setMsg(e.message)}finally{setBusy(false)}};
  return <section className="qualification panel"><div className="inthead"><div><div className="eyebrow">AUTONOMOUS CAMPAIGNS · v0.27</div><h3>Orchestrate the reactivation campaign.</h3><p>Reactivate can plan content, wait for approval, coordinate production, package publishing and hand results back to the learning loop. Live platform actions remain credential-gated.</p></div><button onClick={start} disabled={busy}>{busy?'Working…':'Start reactivation campaign'}</button></div>{msg&&<div className="notice">{msg}</div>}<div className="assetgrid">{campaigns.map(c=><article className="asset" key={c.id}><div className="assetmeta"><span className="eyebrow">CAMPAIGN #{c.id} · {c.stage}</span><span className="queued">{c.status}</span></div><h4>{c.name}</h4><p><b>Assets:</b> {c.asset_ids?.length||0} · <b>Production:</b> {c.production_job_ids?.length||0} · <b>Publishing:</b> {c.publishing_job_ids?.length||0}</p>{c.blockers?.map((b,i)=><p key={i}>⚠ {b}</p>)}<small>Next: {c.next_action||'—'}</small>{c.stage==='APPROVAL'&&<button className="secondary" onClick={()=>advance(c.id)} disabled={busy}>Check approvals → production</button>}{c.stage==='PRODUCTION'&&<button className="secondary" onClick={()=>advance(c.id)} disabled={busy}>Check production → publishing</button>}{c.stage==='PUBLISH'&&<button className="secondary" onClick={()=>advance(c.id)} disabled={busy}>Start measurement</button>}{c.stage==='MEASURE'&&<button className="secondary" onClick={()=>advance(c.id)} disabled={busy}>Close campaign loop</button>}</article>)}</div></section>;
}

function ProductionPipeline({prospect:p}) {
  const [jobs,setJobs]=useState([]); const [publishing,setPublishing]=useState([]); const [loading,setLoading]=useState(false); const [rendering,setRendering]=useState({}); const [error,setError]=useState(''); const [provider,setProvider]=useState('LOCAL_FFMPEG_PREVIEW'); const [model,setModel]=useState('veo-3-1'); const [selectedJobs,setSelectedJobs]=useState([]); const [assembly,setAssembly]=useState(null); const [pubPlatform,setPubPlatform]=useState('INSTAGRAM'); const [pubSchedule,setPubSchedule]=useState('');
  const load=async()=>{setLoading(true);setError('');try{const [r,pr]=await Promise.all([fetch(`${API}/api/v1/prospects/${p.id}/production-jobs`),fetch(`${API}/api/v1/prospects/${p.id}/publishing-jobs`)]);const d=await r.json();const pd=await pr.json();if(!r.ok)throw new Error(d.detail||'Could not load production jobs');setJobs(d.jobs||[]);if(pr.ok)setPublishing(pd.jobs||[])}catch(e){setError(e.message)}finally{setLoading(false)}};
  useEffect(()=>{if(p.id)load()},[p.id]);
  const patch=async(id,status)=>{try{const r=await fetch(`${API}/api/v1/production-jobs/${id}`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({status})});const d=await r.json();if(!r.ok)throw new Error(d.detail||'Could not update job');setJobs(xs=>xs.map(x=>x.id===id?d:x))}catch(e){setError(e.message)}};
  const render=async(id)=>{setRendering(x=>({...x,[id]:true}));setError('');try{const endpoint=provider==='KIE'?`${API}/api/v1/production-jobs/${id}/ai-submit`:`${API}/api/v1/production-jobs/${id}/render`;const body=provider==='KIE'?{provider:'KIE',model}:{provider:'LOCAL_FFMPEG_PREVIEW'};const r=await fetch(endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const d=await r.json();if(!r.ok)throw new Error(d.detail||'Render failed');setJobs(xs=>xs.map(x=>x.id===id?d.job:x))}catch(e){setError(e.message)}finally{setRendering(x=>({...x,[id]:false}))}};
  const publishPackage=async(j)=>{setError('');try{const r=await fetch(`${API}/api/v1/production-jobs/${j.id}/publish-package`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({platform:pubPlatform,scheduled_for:pubSchedule,hashtags:[]})});const d=await r.json();if(!r.ok)throw new Error(d.detail||'Could not queue publishing');setPublishing(xs=>[d.publishing,...xs]);setPubSchedule('')}catch(e){setError(e.message)}}; const dryPublish=async(id)=>{try{const r=await fetch(`${API}/api/v1/publishing-jobs/${id}/publish`,{method:'POST'});const d=await r.json();if(!r.ok)throw new Error(d.detail||'Publish failed');setPublishing(xs=>xs.map(x=>x.id===id?d.publishing:x))}catch(e){setError(e.message)}};
  const refreshAi=async(id)=>{try{const r=await fetch(`${API}/api/v1/production-jobs/${id}/ai-status`);const d=await r.json();if(!r.ok)throw new Error(d.detail||'Could not read AI status');setJobs(xs=>xs.map(x=>x.id===id?d.job:x))}catch(e){setError(e.message)}};
  return <div className="production panel"><div className="inthead"><div><div className="eyebrow">MEDIA PRODUCTION · v0.26</div><h3>Render a local preview or submit a real AI video job.</h3><p>Local FFmpeg is free and deterministic. KIE submits an asynchronous Veo 3.1 generation task; the API key stays server-side.</p></div><div className="formrow"><select value={provider} onChange={e=>setProvider(e.target.value)}><option value="LOCAL_FFMPEG_PREVIEW">Local FFmpeg preview</option><option value="KIE">KIE · Veo 3.1</option></select>{provider==='KIE'&&<select value={model} onChange={e=>setModel(e.target.value)}><option value="veo-3-1">Veo 3.1</option></select>}<button className="secondary" onClick={load}>{loading?'Loading…':'Refresh jobs'}</button><button onClick={assemble} disabled={!selectedJobs.length}>Assemble {selectedJobs.length||''} clip{selectedJobs.length===1?'':'s'}</button><select value={pubPlatform} onChange={e=>setPubPlatform(e.target.value)}><option>INSTAGRAM</option><option>FACEBOOK</option><option>TIKTOK</option><option>LINKEDIN</option><option>YOUTUBE</option></select><input type="datetime-local" value={pubSchedule} onChange={e=>setPubSchedule(e.target.value)} title="Optional schedule" /></div></div>{error&&<div className="notice">{error}</div>}<div className="assetgrid">{jobs.map(j=><article className="asset" key={j.id}><div className="assetmeta"><label><input type="checkbox" disabled={j.status!=='RENDERED'} checked={selectedJobs.includes(j.id)} onChange={e=>setSelectedJobs(xs=>e.target.checked?[...xs,j.id]:xs.filter(id=>id!==j.id))}/> Assemble</label><span className="eyebrow">JOB #{j.id} · {j.production_type}</span>{j.status==='RENDERED'?<span className="queued">RENDERED</span>:<select value={j.status} onChange={e=>patch(j.id,e.target.value)}><option>BRIEF_READY</option><option>IN_PRODUCTION</option><option>READY_TO_PUBLISH</option><option>PUBLISHED</option><option>BLOCKED</option></select>}</div><h4>{j.title}</h4><p><b>Platform:</b> {j.platform} · {j.aspect_ratio} · {j.duration_seconds}s</p><p><b>Hook:</b> {j.hook}</p><p><b>Voiceover:</b> {j.voiceover}</p><p><b>Shots:</b> {j.shot_list?.join(' · ')}</p><p><b>CTA:</b> {j.cta}</p><small>{j.production_notes}</small>{j.render_error&&<div className="notice">{j.render_error}</div>}<div className="assetfoot"><button className="secondary" disabled={rendering[j.id] || j.status==='PUBLISHED'} onClick={()=>render(j.id)}>{rendering[j.id]?'Submitting…':provider==='KIE'?'Generate with KIE':'Render local preview'}</button>{j.media_url&&<button className="secondary" onClick={async()=>{try{const r=await fetch(`${API}/api/v1/production-jobs/${j.id}/media-layer`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({voice:'en'})});const d=await r.json();if(!r.ok)throw new Error(d.detail||'Media layer failed');setJobs(xs=>xs.map(x=>x.id===j.id?d.job:x))}catch(e){setError(e.message)}}}>Add voice + captions</button>}{(j.status==='READY_TO_PUBLISH'||j.status==='RENDERED')&&j.media_url&&<button className="secondary" onClick={()=>publishPackage(j)}>Queue publish</button>}{provider==='KIE'&&j.provider_task_id&&j.status==='IN_PRODUCTION'&&<button className="secondary" onClick={()=>refreshAi(j.id)}>Check KIE status</button>}{j.media_url&&<a className="secondary" href={j.media_url.startsWith('http')?j.media_url:`${API}${j.media_url}`} target="_blank" rel="noreferrer">Open video ↗</a>}</div>{j.media_url&&<video className="video-preview" controls preload="metadata" src={`${API}${j.media_url}`} />}</article>)}</div>{publishing.length>0&&<div className="publishing panel"><div className="eyebrow">PUBLISHING QUEUE · v0.23</div><h3>Scheduled publishing packages</h3><div className="assetgrid">{publishing.map(x=><article className="asset" key={x.id}><span className="eyebrow">#{x.id} · {x.platform}</span><span className="queued">{x.status}</span><p><b>Schedule:</b> {x.scheduled_for||'Immediate'}</p><p>{x.caption}</p>{x.published_url&&<a className="secondary" href={x.published_url} target="_blank" rel="noreferrer">Published record ↗</a>}{x.status!=='PUBLISHED'&&<button onClick={()=>dryPublish(x.id)}>Dry-run publish</button>}</article>)}</div></div>}<PerformancePanel prospect={p} /></div>;
}

function PerformancePanel({prospect:p}) {
  const [summary,setSummary]=useState(null); const [learning,setLearning]=useState(null); const [jobs,setJobs]=useState([]); const [status,setStatus]=useState("");
  const [form,setForm]=useState({publishing_job_id:"",views:0,likes:0,comments:0,shares:0,saves:0,clicks:0,leads:0,conversions:0,impressions:0});
  const set=(k,v)=>setForm(x=>({...x,[k]:v}));
  const load=async()=>{try{const [a,l,b]=await Promise.all([fetch(`${API}/api/v1/prospects/${p.id}/learning`),fetch(`${API}/api/v1/prospects/${p.id}/content-learning`),fetch(`${API}/api/v1/prospects/${p.id}/publishing-jobs`)]); const d=await a.json(),learn=await l.json(),j=await b.json(); if(a.ok)setSummary(d); if(l.ok)setLearning(learn); if(b.ok){setJobs(j.jobs||[]); if(!form.publishing_job_id&&j.jobs?.[0])setForm(x=>({...x,publishing_job_id:String(j.jobs[0].id)}));}}catch(e){setStatus(e.message)}};
  useEffect(()=>{if(p.id)load()},[p.id]);
  const save=async()=>{if(!form.publishing_job_id){setStatus("Select a publishing job first.");return} setStatus(""); try{const body={}; for(const k of ["views","likes","comments","shares","saves","clicks","leads","conversions","impressions"]){body[k]=Number(form[k]||0)} const r=await fetch(`${API}/api/v1/publishing-jobs/${form.publishing_job_id}/performance`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)}); const d=await r.json(); if(!r.ok)throw new Error(d.detail||"Could not record performance"); setStatus("Performance recorded."); load();}catch(e){setStatus(e.message)}};
  return <section className="performance panel"><div className="detailhead"><div><div className="eyebrow">PERFORMANCE & LEARNING · v0.25</div><h3>Close the loop.</h3><p>Record observed results and turn them into transparent learning signals.</p></div><div className="score"><small>OBSERVATIONS</small><strong>{summary?.observations ?? "—"}</strong></div></div><div className="metrics"><Metric label="Views" value={(summary?.totals?.views||0).toLocaleString()} /><Metric label="Engagement" value={`${summary?.totals?.engagement_rate||0}%`} /><Metric label="Leads" value={(summary?.totals?.leads||0).toLocaleString()} /><Metric label="Conversions" value={(summary?.totals?.conversions||0).toLocaleString()} /></div><div className="gap"><div><div className="eyebrow">LEARNING SIGNALS</div>{(summary?.learning||["No performance observations yet."]).map((x,i)=><p key={i}>{x}</p>)}{learning?.signals?.length>0&&<><div className="eyebrow">CONTENT ENGINE BRIEF</div>{learning.signals.map((x,i)=><p key={`c${i}`}><b>→</b> {x}</p>)}</>}</div></div><div className="patternform"><div className="formrow"><select value={form.publishing_job_id} onChange={e=>set("publishing_job_id",e.target.value)}><option value="">Publishing job</option>{jobs.map(j=><option key={j.id} value={j.id}>#{j.id} · {j.platform} · {j.status}</option>)}</select><input type="number" min="0" value={form.views} onChange={e=>set("views",e.target.value)} placeholder="Views"/><input type="number" min="0" value={form.likes} onChange={e=>set("likes",e.target.value)} placeholder="Likes"/><input type="number" min="0" value={form.comments} onChange={e=>set("comments",e.target.value)} placeholder="Comments"/><input type="number" min="0" value={form.shares} onChange={e=>set("shares",e.target.value)} placeholder="Shares"/></div><div className="formrow"><input type="number" min="0" value={form.saves} onChange={e=>set("saves",e.target.value)} placeholder="Saves"/><input type="number" min="0" value={form.clicks} onChange={e=>set("clicks",e.target.value)} placeholder="Clicks"/><input type="number" min="0" value={form.leads} onChange={e=>set("leads",e.target.value)} placeholder="Leads"/><input type="number" min="0" value={form.conversions} onChange={e=>set("conversions",e.target.value)} placeholder="Conversions"/><button onClick={save}>Record performance</button></div>{status&&<div className="notice">{status}</div>}</div></section>;
}

function OutreachQueue({prospect:p}) {
  const [channel,setChannel]=useState(p.outreach_channel || 'WHATSAPP');
  const [follow,setFollow]=useState(p.follow_up_at || '');
  const [draft,setDraft]=useState(p.outreach_draft || '');
  const [saving,setSaving]=useState(false);
  const queue=async()=>{
    setSaving(true);
    try {
      const r=await fetch(`${API}/api/v1/prospects/${p.id}/outreach/queue`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({channel,follow_up_at:follow})});
      const data=await r.json(); if(!r.ok) throw new Error(data.detail||'Could not queue outreach');
      Object.assign(p,data); setDraft(data.outreach_draft || '');
    } catch(e){ alert(e.message); } finally { setSaving(false); }
  };
  return <div className="outreach panel"><div><div className="eyebrow">OUTREACH QUEUE</div><h3>Turn this verified prospect into a personal first contact.</h3><p>Drafts are generated from the evidence-backed Social Gap. Nothing is sent automatically.</p></div><div className="outgrid"><label>Channel<select value={channel} onChange={e=>setChannel(e.target.value)}><option>WHATSAPP</option><option>EMAIL</option><option>INSTAGRAM</option><option>FACEBOOK</option><option>LINKEDIN</option><option>PHONE</option></select></label><label>Follow-up date/time<input type="datetime-local" value={follow} onChange={e=>setFollow(e.target.value)} /></label><label className="wide">Draft<textarea value={draft} onChange={e=>setDraft(e.target.value)} placeholder="Queue the prospect to generate a draft…" /></label></div><button onClick={queue} disabled={saving}>{saving?'Queueing…':p.contact_status==='QUEUED'?'Update outreach':'Queue outreach'}</button>{p.contact_status==='QUEUED' && <span className="queued">Queued · {p.outreach_channel || channel}</span>}</div>
}

createRoot(document.getElementById('root')).render(<App />);
