from pathlib import Path
from backend.app.storage import init_db, upsert_prospect, update_qualification


def record():
    return {
        'name':'Test Salon','city':'Johannesburg','category':'hair salon','website':'https://example.com',
        'score':82,'grade':'A','social_gap_score':90,'health_score':90,
        'social_gap':{'headline':'Strong Social Gap detected.'},
        'channels':[{'platform':'Instagram','url':'https://instagram.com/test','last_meaningful_post_days':180,'posts_last_365d':52}],
        'evidence':[]
    }


def test_outreach_fields_persist(tmp_path: Path):
    db=tmp_path/'outreach.db'; init_db(db)
    p=upsert_prospect(record(),db)
    updated=update_qualification(p['id'], {'contact_status':'QUEUED','outreach_channel':'WHATSAPP','outreach_draft':'Hi Test Salon','follow_up_at':'2026-09-20T10:00'},db)
    assert updated['contact_status']=='QUEUED'
    assert updated['outreach_channel']=='WHATSAPP'
    assert updated['outreach_draft']=='Hi Test Salon'
    assert updated['follow_up_at']=='2026-09-20T10:00'
