from pathlib import Path
from backend.app.storage import init_db, create_content_assets, update_content_asset
from backend.app.campaigns import create_campaign, get_campaign, update_campaign

def test_campaign_lifecycle_storage(tmp_path: Path):
    db=tmp_path/'r.db'; init_db(db)
    c=create_campaign(7,'Demo Reactivation',path=db)
    assert c['status']=='PLANNED' and c['stage']=='PLAN'
    c=update_campaign(c['id'],{'status':'AWAITING_APPROVAL','stage':'APPROVAL','asset_ids':[1,2],'blockers':['review assets'],'next_action':'Approve'},db)
    assert c['asset_ids']==[1,2] and c['blockers']==['review assets']
    assert get_campaign(c['id'],db)['next_action']=='Approve'
