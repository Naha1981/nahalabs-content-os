from pathlib import Path
from backend.app.storage import init_db, upsert_prospect
from backend.app.revenue import create_revenue_event, revenue_summary

def test_revenue_events_and_summary(tmp_path: Path):
    db=tmp_path/'x.db'; init_db(db)
    p=upsert_prospect({'name':'Demo Business','city':'Johannesburg','category':'salon','score':85,'grade':'A','social_gap_score':80,'health_score':90},db)
    create_revenue_event(p['id'],'LEAD',path=db)
    create_revenue_event(p['id'],'MEETING',path=db)
    create_revenue_event(p['id'],'WON',2500,path=db)
    create_revenue_event(p['id'],'REVENUE',1200,path=db)
    out=revenue_summary(p['id'],path=db)
    assert out['counts']['LEAD']==1 and out['counts']['MEETING']==1 and out['counts']['WON']==1
    assert out['commercial_value']==3700

def test_invalid_revenue_event(tmp_path: Path):
    db=tmp_path/'x.db'; init_db(db)
    p=upsert_prospect({'name':'Demo','city':'Joburg','category':'service','score':70,'grade':'B','social_gap_score':70,'health_score':80},db)
    try: create_revenue_event(p['id'],'REFUND',path=db)
    except ValueError: pass
    else: assert False
