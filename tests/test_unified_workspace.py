from pathlib import Path
from tempfile import TemporaryDirectory
from backend.app.storage import init_db, upsert_many, create_content_assets
from backend.app.unified_workspace import prospect_workspace
from backend.app.outreach_events import init_outreach_events_db, create_outreach_event
from backend.app.campaigns import init_campaign_db, create_campaign
from backend.app.crm import init_crm_db, create_opportunity
from backend.app.revenue import init_revenue_db, create_revenue_event


def test_workspace_aggregates_real_prospect_data():
    with TemporaryDirectory() as d:
        path = Path(d) / 'r.db'
        init_db(path); init_outreach_events_db(path); init_campaign_db(path); init_crm_db(path); init_revenue_db(path)
        p = upsert_many([{'name':'Test Salon','city':'Johannesburg','category':'Hair','score':88,'grade':'A','qualification_status':'QUALIFIED','priority':'HIGH','contact_status':'CONTACTED','social_gap_score':80,'health_score':90}], path=path)[0]
        pid=p['id']
        create_content_assets(pid,[{'title':'Return to routine','hook':'We are back','script':'Hello','caption':'Come back','cta':'Book now'}],path=path)
        c=create_campaign(pid,'Reactivate',path=path)
        create_outreach_event(pid,'EMAIL','SENT',campaign_id=c['id'],path=path)
        create_opportunity(pid,'Pilot',12000,campaign_id=c['id'],path=path)
        create_revenue_event(pid,'LEAD',0,campaign_id=c['id'],path=path)
        w=prospect_workspace(pid,path)
        assert w['prospect']['name']=='Test Salon'
        assert w['summary']['content']==1
        assert w['summary']['campaigns']==1
        assert w['summary']['outreach']==1
        assert w['summary']['opportunities']==1
        assert w['summary']['pipeline_value']==12000
        assert w['revenue']['counts']['LEAD']==1
