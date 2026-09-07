'use client';

import { useEffect, useState } from 'react';
import { apiMode, checkApiHealth } from '../lib/api';

type Asset = { id:number; title:string; type:string; status:string; platform:string; score:number };
const assets: Asset[] = [
  {id:1,title:'The burger close-up',type:'Product demo',status:'Ready',platform:'Instagram + TikTok',score:94},
  {id:2,title:'Founder: why we make it',type:'Story',status:'Ready',platform:'Instagram',score:91},
  {id:3,title:'3 things customers ask us',type:'Education',status:'Needs approval',platform:'Instagram + Facebook',score:88},
  {id:4,title:'Friday offer',type:'Offer',status:'Needs approval',platform:'Instagram + Google',score:92},
  {id:5,title:'POV: first bite',type:'UGC',status:'Generating',platform:'TikTok + Reels',score:0},
  {id:6,title:'Behind the counter',type:'Behind the scenes',status:'Ready',platform:'TikTok',score:86}
];

export default function Home() {
  const [tab,setTab]=useState('Overview');
  const [created,setCreated]=useState(false);
  const [approved,setApproved]=useState<number[]>([]);
  const [connected,setConnected]=useState(false);
  const [apiHealthy,setApiHealthy]=useState<boolean | null>(null);
  useEffect(() => { checkApiHealth().then(setApiHealthy); }, []);
  const visible = assets.map(a => approved.includes(a.id) ? {...a,status:'Approved'} : a);

  return <main className="shell">
    <aside className="sidebar">
      <div className="brand"><span className="mark">N</span><div><strong>NahaLabs</strong><small>Content OS</small></div></div>
      <div className="business"><div className="avatar">BM</div><div><strong>Example Restaurant</strong><small>Johannesburg</small></div></div>
      <nav>{['Overview','Content','Approvals','Publishing','Analytics'].map(x=><button key={x} className={tab===x?'nav active':'nav'} onClick={()=>setTab(x)}>{x}</button>)}</nav>
      <div className="sidebarBottom"><small>Demo workspace</small><span>v1.9</span></div>
    </aside>
    <section className="main">
      <header className="top"><div><h1>{tab}</h1><p>One recording in. A month of content out.</p></div><div className="topActions"><span className={'mode '+(apiMode==='demo'?'demo':'live')}>{apiMode==='demo'?'Demo mode':'Live mode'}{apiMode==='live' ? (apiHealthy===true?' · API online':apiHealthy===false?' · API offline':'') : ''}</span><button className="outline" onClick={()=>setConnected(!connected)}>{connected?'Social accounts connected':'Connect social accounts'}</button></div></header>

      {tab==='Overview' && <>
        <section className="hero"><div><p className="eyebrow">CONTENT OS</p><h2>{created?'Your content engine is running.':'Turn one phone video into a month of content.'}</h2><p className="heroCopy">Upload a normal 20–60 second phone recording. Content OS creates strategic content, checks it, and puts the best pieces into your approval queue.</p><div className="actions"><button className="primary" onClick={()=>setCreated(true)}>{created?'Create another content pack':'Create 10 pieces of content'}</button><button className="secondary" onClick={()=>setTab('Content')}>View content</button></div></div><div className="flow"><div><b>01</b><span>Record</span><small>Normal phone footage</small></div><i>→</i><div><b>02</b><span>Generate</span><small>Strategic variations</small></div><i>→</i><div><b>03</b><span>Approve</span><small>You stay in control</small></div><i>→</i><div><b>04</b><span>Publish</span><small>Schedule everywhere</small></div></div></section>
        <section className="stats"><div><small>CONTENT THIS MONTH</small><strong>{created?10:6}</strong><span>planned assets</span></div><div><small>READY TO APPROVE</small><strong>{visible.filter(x=>x.status==='Needs approval').length}</strong><span>waiting for you</span></div><div><small>QUALITY SCORE</small><strong>91</strong><span>average across ready assets</span></div><div><small>SOCIAL ACCOUNTS</small><strong>{connected?3:0}</strong><span>{connected?'connected via Zernio':'connect to publish'}</span></div></section>
      </>}

      {tab==='Content' && <section className="panel"><div className="panelHead"><div><h2>Content pack</h2><p>Strategic mix generated from your business and performance data.</p></div><button className="primary" onClick={()=>setCreated(true)}>Create another 10</button></div><div className="assetGrid">{visible.map(a=><article className="asset" key={a.id}><div className="assetVisual"><span>{a.type}</span><b>{a.score?`${a.score}/100`:'Generating'}</b></div><div className="assetBody"><h3>{a.title}</h3><p>{a.platform}</p><div className="row"><span className={'status '+a.status.toLowerCase().replaceAll(' ','-')}>{a.status}</span>{a.status==='Needs approval'&&<button className="mini" onClick={()=>setApproved(v=>[...v,a.id])}>Approve</button>}</div></div></article>)}</div></section>}

      {tab==='Approvals' && <section className="panel"><div className="panelHead"><div><h2>Approval queue</h2><p>Nothing publishes until you approve it.</p></div></div>{visible.filter(x=>x.status==='Needs approval').length===0 ? <div className="empty"><strong>You're all caught up.</strong><span>New generated content will appear here after quality checks.</span></div> : <div className="approvalList">{visible.filter(x=>x.status==='Needs approval').map(a=><div className="approval" key={a.id}><div className="thumb">{a.type}</div><div><h3>{a.title}</h3><p>{a.platform} · quality {a.score}/100</p></div><button className="primary" onClick={()=>setApproved(v=>[...v,a.id])}>Approve</button></div>)}</div>}</section>}

      {tab==='Publishing' && <section className="panel"><div className="panelHead"><div><h2>Publishing</h2><p>Preflight, approve, then schedule. No silent publishing.</p></div><button className="outline" onClick={()=>setConnected(true)}>{connected?'Connected':'Connect accounts'}</button></div><div className="publishSteps"><div className="done"><b>1</b><div><strong>Quality gate</strong><span>Technical, brand and safety checks</span></div></div><div className="done"><b>2</b><div><strong>Zernio preflight</strong><span>Platform rules checked before submission</span></div></div><div className={approved.length?'done':'pending'}><b>3</b><div><strong>Customer approval</strong><span>{approved.length?'Approved content can be scheduled':'Approve content from the queue'}</span></div></div><div className={connected&&approved.length?'done':'pending'}><b>4</b><div><strong>Schedule & publish</strong><span>{connected&&approved.length?'Ready for publishing worker':'Connect accounts and approve content'}</span></div></div></div></section>}

      {tab==='Analytics' && <section className="panel"><div className="panelHead"><div><h2>Content intelligence</h2><p>Performance feeds the next content plan.</p></div></div><div className="insights"><div><small>BEST FORMAT</small><strong>Product demo</strong><span>+32% engagement vs. pack average</span></div><div><small>BEST PLATFORM</small><strong>Instagram Reels</strong><span>Strongest reach for current audience</span></div><div><small>NEXT EXPERIMENT</small><strong>Hook × Offer</strong><span>Test direct offer against story-led hook</span></div></div><div className="learning"><strong>The loop is active</strong><span>Published content → analytics → insights → next briefs → new content.</span></div></section>}
    </section>
  </main>
}
