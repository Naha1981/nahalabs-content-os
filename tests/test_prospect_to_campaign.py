from pathlib import Path
from backend.app.storage import init_db, upsert_prospect, update_qualification
from backend.app.campaigns import list_active_campaigns
from backend.app.main import auto_start_campaign, CampaignCreateRequest


def seed(path: Path):
    init_db(path)
    record = {
        "name":"Demo Salon","city":"Johannesburg","category":"hair salon",
        "score":91,"grade":"A+","social_gap_score":95,"health_score":90,
        "radar_json":{},"google_url":"https://example.com/demo-salon"
    }
    p=upsert_prospect(record,path)
    return p


def test_auto_campaign_requires_qualification(tmp_path: Path):
    db=tmp_path/'r.db'; p=seed(db)
    import backend.app.main as main
    from backend.app.storage import get_prospect
    monkeypatch = __import__('pytest').MonkeyPatch()
    monkeypatch.setattr(main, 'get_prospect', lambda pid: get_prospect(pid, db))
    try:
        main.auto_start_campaign(p['id'], CampaignCreateRequest())
    except Exception as exc:
        assert 'QUALIFIED' in str(exc)
    else:
        assert False, 'Unqualified prospect was allowed to launch a campaign'
    finally:
        monkeypatch.undo()


def test_active_campaign_guard(tmp_path: Path, monkeypatch):
    db=tmp_path/'r.db'; p=seed(db)
    update_qualification(p['id'], {'qualification_status':'QUALIFIED','priority':'HOT'}, db)
    import backend.app.main as main
    monkeypatch.setattr(main, 'get_prospect', lambda pid: __import__('backend.app.storage', fromlist=['get_prospect']).get_prospect(pid, db))
    monkeypatch.setattr(main, 'create_campaign', lambda pid,name,objective: __import__('backend.app.campaigns', fromlist=['create_campaign']).create_campaign(pid,name,objective,db))
    monkeypatch.setattr(main, 'list_active_campaigns', lambda pid: __import__('backend.app.campaigns', fromlist=['list_active_campaigns']).list_active_campaigns(pid,db))
    monkeypatch.setattr(main, 'build_content_learning', lambda pid: {'signals':[]})
    monkeypatch.setattr(main, 'list_patterns', lambda limit=10: [])
    monkeypatch.setattr(main, 'generate_content_assets', lambda *a, **k: [])
    monkeypatch.setattr(main, 'create_content_assets', lambda *a, **k: [])
    first=main.auto_start_campaign(p['id'], CampaignCreateRequest())
    assert first['created'] is True
    second=main.auto_start_campaign(p['id'], CampaignCreateRequest())
    assert second['created'] is False and second['reason']=='ACTIVE_CAMPAIGN_EXISTS'
