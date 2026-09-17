from pathlib import Path
from backend.app.storage import init_db, upsert_prospect
from backend.app.outreach_events import create_outreach_event, list_outreach_events, outreach_summary

def test_outreach_events_are_persisted(tmp_path: Path):
    db=tmp_path/'x.db'; init_db(db)
    p=upsert_prospect({'name':'Demo Salon','city':'Johannesburg','category':'hair salon','score':88,'grade':'A','social_gap_score':90,'health_score':90,'google_url':'https://example.com'},db)
    e=create_outreach_event(p['id'],'EMAIL','SENT','Social Gap audit','Human reviewed',path=db)
    assert e['event_type']=='SENT'
    out=outreach_summary(p['id'],path=db)
    assert out['count']==1
    assert out['last_event']['channel']=='EMAIL'
