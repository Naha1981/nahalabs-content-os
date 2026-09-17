from pathlib import Path
from backend.app.storage import init_db, upsert_prospect
from backend.app.campaigns import create_campaign, update_campaign
from backend.app.command_center import campaign_command_center

def test_command_center_aggregates_campaigns(tmp_path: Path):
    db=tmp_path/'x.db'; init_db(db)
    p=upsert_prospect({'name':'Demo Salon','city':'Johannesburg','category':'hair salon','score':88,'grade':'A','social_gap_score':90,'health_score':90,'google_url':'https://example.com'},db)
    c=create_campaign(p['id'],'Demo Reactivation',path=db)
    update_campaign(c['id'],{'stage':'APPROVAL','status':'AWAITING_APPROVAL','blockers':['Approve asset'], 'next_action':'Review asset'},db)
    out=campaign_command_center(db)
    assert out['counts']['total']==1
    assert out['counts']['awaiting_approval']==1
    assert out['campaigns'][0]['prospect_name']=='Demo Salon'
    assert out['campaigns'][0]['has_blockers'] is True

def test_command_center_surfaces_commercial_outcomes(tmp_path: Path):
    from backend.app.revenue import create_revenue_event
    db=tmp_path/'y.db'; init_db(db)
    p=upsert_prospect({'name':'Revenue Demo','city':'Johannesburg','category':'gym','score':90,'grade':'A+','social_gap_score':90,'health_score':95},db)
    c=create_campaign(p['id'],'Revenue Campaign',path=db)
    create_revenue_event(p['id'],'LEAD',campaign_id=c['id'],path=db)
    create_revenue_event(p['id'],'WON',amount=5000,campaign_id=c['id'],path=db)
    out=campaign_command_center(db)
    row=out['campaigns'][0]
    assert row['revenue_event_count']==2
    assert row['revenue_leads']==1
    assert row['won_count']==1
    assert row['commercial_value']==5000
