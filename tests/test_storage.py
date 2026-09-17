from pathlib import Path
from backend.app.storage import init_db, upsert_prospect, list_prospects, get_prospect


def record():
    return {"name":"Test Salon","city":"Johannesburg","category":"Hair salon","website":"https://example.com","score":81.5,"grade":"A","social_gap_score":90,"health_score":92,"social_gap":{},"channels":[],"evidence":[]}


def test_upsert_deduplicates_and_tracks_scans(tmp_path: Path):
    db = tmp_path / "test.db"; init_db(db)
    first = upsert_prospect(record(), db); second = upsert_prospect(record(), db)
    assert first["id"] == second["id"]
    assert second["scan_count"] == 2
    assert len(list_prospects(db, min_score=80)) == 1
    assert get_prospect(first["id"], db)["name"] == "Test Salon"


def test_qualification_survives_rescan(tmp_path):
    from backend.app.storage import init_db, upsert_prospect, update_qualification, get_prospect
    db = tmp_path / 'q.db'; init_db(db)
    record = {'name':'Test Salon','city':'Johannesburg','category':'hair salon','score':82,'grade':'A','social_gap_score':90,'health_score':90,'website':'https://example.com'}
    first = upsert_prospect(record, db)
    updated = update_qualification(first['id'], {'qualification_status':'QUALIFIED','priority':'HOT','contact_status':'QUEUED','notes':'Strong fit','next_action':'Send audit'}, db)
    assert updated['priority'] == 'HOT'
    upsert_prospect({**record,'score':85}, db)
    final = get_prospect(first['id'], db)
    assert final['priority'] == 'HOT'
    assert final['qualification_status'] == 'QUALIFIED'
    assert final['notes'] == 'Strong fit'
    assert final['score'] == 85
