from pathlib import Path
from backend.app.storage import init_db, upsert_prospect
from backend.app.crm import create_opportunity, update_opportunity, get_opportunity, crm_summary

def seed(db):
    init_db(db); return upsert_prospect({'name':'Demo','city':'Johannesburg','category':'salon','score':85,'grade':'A','social_gap_score':80,'health_score':90},db)

def test_crm_lifecycle_and_history(tmp_path:Path):
    db=tmp_path/'x.db'; p=seed(db)
    o=create_opportunity(p['id'],'Reactivation retainer',12000,path=db)
    assert o['stage']=='DISCOVERY'
    o=update_opportunity(o['id'],{'stage':'PROPOSAL','note':'Proposal sent'},db)
    o=update_opportunity(o['id'],{'stage':'WON'},db)
    assert [h['to_stage'] for h in o['history']] == ['WON','PROPOSAL','DISCOVERY']
    assert crm_summary(db)['won_value']==12000

def test_invalid_stage(tmp_path:Path):
    db=tmp_path/'x.db'; p=seed(db)
    try: create_opportunity(p['id'],'Bad',stage='NOPE',path=db)
    except ValueError: pass
    else: assert False
