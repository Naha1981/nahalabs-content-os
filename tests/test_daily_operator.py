from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime, timezone, timedelta
from backend.app.storage import init_db, upsert_many
from backend.app.campaigns import create_campaign, update_campaign
from backend.app.crm import create_opportunity
from backend.app.daily_operator import daily_operator


def test_daily_operator_surfaces_due_and_blocked_work():
    with TemporaryDirectory() as d:
        path=Path(d)/'r.db'; init_db(path)
        p=upsert_many([{'name':'Test Salon','city':'Johannesburg','category':'Hair','score':91,'grade':'A+','social_gap_score':90,'health_score':95}],path=path)[0]
        from backend.app.storage import _connect
        with _connect(path) as c:
            c.execute('UPDATE prospects SET qualification_status="QUALIFIED", priority="HOT", contact_status="NOT_CONTACTED", follow_up_at=? WHERE id=?',((datetime.now(timezone.utc)-timedelta(hours=1)).isoformat(),p['id']))
        c=create_campaign(p['id'],'Reactivate',path=path); update_campaign(c['id'],{'status':'BLOCKED','blockers':['Approval required']},path=path)
        o=create_opportunity(p['id'],'Pilot',15000,next_follow_up_at=(datetime.now(timezone.utc)-timedelta(hours=2)).isoformat(),path=path)
        out=daily_operator(path)
        kinds={x['kind'] for x in out['actions']}
        assert out['total_actions']>=3
        assert 'OUTREACH' in kinds
        assert 'FOLLOW_UP' in kinds
        assert 'CAMPAIGN' in kinds
        assert 'DEAL_FOLLOW_UP' in kinds


def test_daily_operator_does_not_invent_actions_for_empty_database():
    with TemporaryDirectory() as d:
        path=Path(d)/'r.db'; init_db(path)
        out=daily_operator(path, datetime(2026,1,1,tzinfo=timezone.utc))
        assert out['total_actions']==0
        assert out['actions']==[]
