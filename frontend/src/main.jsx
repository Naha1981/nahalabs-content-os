import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const API = '';

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
      const text = await response.text();
      let data;
      try { data = text ? JSON.parse(text) : {}; } catch { data = { detail: text || `Request failed (${response.status})` }; }
      if (!response.ok) throw new Error(data.detail || `Radar API unavailable (${response.status})`);
      setProspects(data.prospects || []);
      setSelected(data.prospects?.[0] ?? null);
      if (!data.prospects?.length) setError('No verified prospects returned. Try another category or location.');
    } catch (err) {
      setProspects([]); setSelected(null);
      setError(`${err.message}. Check the backend health and browser worker.`);
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

function ProspectWorkspace({data,onBack,onRefresh,loading}) { const p=data?.prospect||{}; const s=data?.summary||{}; const q=data?.qualification||{}; const counts=data?.revenue?.counts||{}; const latest=[...(data?.outreach?.events||[]).map(x=>({at:x.occurred_at,type:`OUTREACH · ${x.channel} · ${x.event_type}`,note:x.note})), ...(data?.performance||[]).map(x=>({at:x.observed_at,type:`PERFORMANCE · ${x.platform||'channel'}`,note:`${x.views||0} views · ${x.likes||0} likes · ${x.leads||0} leads`})), ...(data?.opportunities||[]).map(x=>({at:x.updated_at,type:`OPPORTUNITY · ${x.stage}`,note:`R${Number(x.value||0).toLocaleString()} · ${x.name}`})), ...(data?.campaigns||[]).map(x=>({at:x.updated_at,type:`CAMPAIGN · ${x.stage}`,note:x.name}))].sort((a,b)=>String(b.at).localeCompare(String(a.at))).slice(0,12); return <section className="workspacehub panel"><div className="inthead"><div><div className="eyebrow">UNIFIED PROSPECT WORKSPACE · v0.32</div><h2>{p.name}</h2><p>{p.category} · {p.city} · Score {p.score} · Grade {p.grade}</p></div><div className="formrow"><button className="secondary" onClick={onBack}>Back to prospects</button><button onClick={onRefresh} disabled={loading}>{loading?'Refreshing…':'Refresh'}</button></div></div><div className="workspace-summary"><Metric label="Qualification" value={q.status||'—'} /><Metric label="Priority" value={q.priority||'—'} /><Metric label="Contact" value={q.contact_status||'—'} /><Metric label="Campaigns" value={s.campaigns||0} /><Metric label="Outreach" value={s.outreach||0} /><Metric label="Pipeline" value={`R${Number(s.pipeline_value||0).toLocaleString()}`} /><Metric label="Won" value={`R${Number(s.won_value||0).toLocaleString()}`} /><Metric label="Commercial" value={`R${Number(s.revenue_value||0).toLocaleString()}`} /></div><div className="hubgrid"><div className="panel hubpanel"><div className="eyebrow">OPERATING STATE</div><h3>{q.next_action||'No next action recorded.'}</h3><p>{q.notes||'No seller notes recorded.'}</p><div className="hubcounts"><span>{s.content} content</span><span>{s.production} production</span><span>{s.publishing} publishing</span><span>{s.performance} observations</span></div></div><div className="panel hubpanel"><div className="eyebrow">REVENUE SIGNALS</div><div className="reason"><span>Leads</span><b>{counts.LEAD||0}</b></div><div className="reason"><span>Meetings</span><b>{counts.MEETING||0}</b></div><div className="reason"><span>Won events</span><b>{counts.WON||0}</b></div><div className="reason"><span>Recorded revenue</span><b>R{Number(s.revenue_value||0).toLocaleString()}</b></div></div></div><div className="hubgrid"><div className="panel hubpanel"><div className="eyebrow">CAMPAIGNS & OPPORTUNITIES</div>{(data?.campaigns||[]).slice(0,6).map(c=><div className="hubitem" key={`c${c.id}`}><b>{c.name}</b><span>{c.stage} · {c.status}</span></div>)}{(data?.opportunities||[]).slice(0,6).map(o=><div className="hubitem" key={`o${o.id}`}><b>{o.name}</b><span>{o.stage} · R{Number(o.value||0).toLocaleString()}</span></div>)}{!data?.campaigns?.length&&!data?.opportunities?.length&&<p>No campaigns or opportunities yet.</p>}</div><div className="panel hubpanel"><div className="eyebrow">RECENT ACTIVITY</div>{latest.map((x,i)=><div className="hubitem" key={i}><b>{x.type}</b><span>{x.note||'—'} · {x.at?new Date(x.at).toLocaleString():'—'}</span></div>)}{!latest.length&&<p>No activity recorded yet.</p>}</div></div><div className="panel hubpanel"><div className="eyebrow">EVIDENCE & CHANNELS</div><div className="evidence-links">{p.website&&<a href={p.website} target="_blank" rel="noreferrer">Website ↗</a>}{p.google_url&&<a href={p.google_url} target="_blank" rel="noreferrer">Google ↗</a>}{(p.channels||[]).filter(x=>x.url).map(x=><a href={x.url} target="_blank" rel="noreferrer" key={x.platform}>{x.platform} ↗</a>)}</div><p>{q.next_action?'Next action: '+q.next_action:'No next action recorded.'}</p></div></section>; }

function CRMPipeline({data,onRefresh}) { const stages=['DISCOVERY','QUALIFIED','PROPOSAL','NEGOTIATION','WON','LOST']; const pretty=s=>s.replaceAll('_',' '); const vals=data?.values||{}; return <section className="command panel"><div className="inthead"><div><div className="eyebrow">CRM & OPPORTUNITY PIPELINE · v0.31</div><h2>Turn commercial intent into a visible operating pipeline.</h2></div><button onClick={onRefresh}>Refresh</button></div><div className="workspace-summary"><Metric label="Opportunities" value={data?.count||0} /><Metric label="Total pipeline" value={`R${Number(vals.pipeline||0).toLocaleString()}`} /><Metric label="Won" value={`R${Number(vals.won||0).toLocaleString()}`} /></div><div className="kanban">{stages.map(stage=><div key={stage} className="panel"><div className="listhead"><small>{pretty(stage)}</small><span>{(data?.columns?.[stage]||[]).length}</span></div>{(data?.columns?.[stage]||[]).map(o=><div className="hubitem" key={o.id}><b>{o.name}</b><span>R{Number(o.value||0).toLocaleString()} · {o.owner||'unassigned'}</span></div>)}</div>)}</div></section>; }

function Metric({label,value}){return <div className="metric"><small>{label}</small><strong>{value}</strong></div>}

function ProspectDetail({prospect:p}) { return <article className="detail panel"><div className="eyebrow">EVIDENCE-BACKED PROSPECT</div><h2>{p.name}</h2><p className="muted">{p.category} · {p.city}</p><div className="score"><strong>{p.score}</strong><span>Grade {p.grade}</span></div><p>{p.description || 'No description returned.'}</p><div className="reasons">{(p.reasons||[]).map((r,i)=><div className="reason" key={i}><span>Signal</span><b>{r}</b></div>)}</div><div className="evidence">{p.website&&<a href={p.website} target="_blank" rel="noreferrer">Website ↗</a>}{p.phone&&<span>Phone {p.phone}</span>}{p.email&&<span>Email {p.email}</span>}{p.google_url&&<a href={p.google_url} target="_blank" rel="noreferrer">Google ↗</a>}</div><div className="reasons">{(p.channels||[]).map((c,i)=><div className="reason" key={i}><span>{c.platform}</span><b>{c.handle || c.url || 'Not verified'}</b></div>)}</div></article>; }

function PatternVault({patterns}) { return <section className="command panel"><div className="inthead"><div><div className="eyebrow">PATTERNVAULT</div><h2>Reusable content structures, separated from source content.</h2></div></div>{patterns.map((p,i)=><article className="panel hubpanel" key={p.id||i}><h3>{p.name||p.title||`Pattern ${i+1}`}</h3><p>{p.summary||p.description||''}</p></article>)}</section>; }
function DailyOperator({data,loading,onRefresh}) { return <section className="command panel"><div className="inthead"><div><div className="eyebrow">TODAY'S OPERATOR</div><h2>Evidence-backed next actions.</h2></div><button onClick={onRefresh} disabled={loading}>{loading?'Refreshing…':'Refresh'}</button></div>{data&&<pre>{JSON.stringify(data,null,2)}</pre>}</section>; }
function AutomationCenter({data,onRefresh}) { return <section className="command panel"><div className="inthead"><div><div className="eyebrow">AUTOMATION CONTROL</div><h2>Scheduled jobs and automation health.</h2></div><button onClick={onRefresh}>Refresh</button></div>{data&&<pre>{JSON.stringify(data,null,2)}</pre>}</section>; }
function CampaignCommandCenter({data,loading,onRefresh}) { return <section className="command panel"><div className="inthead"><div><div className="eyebrow">CAMPAIGN COMMAND CENTER</div><h2>Campaigns, blockers and next actions.</h2></div><button onClick={onRefresh} disabled={loading}>{loading?'Refreshing…':'Refresh'}</button></div>{data&&<pre>{JSON.stringify(data,null,2)}</pre>}</section>; }

createRoot(document.getElementById('root')).render(<App />);
