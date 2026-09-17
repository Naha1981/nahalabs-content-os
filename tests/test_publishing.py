from pathlib import Path
from backend.app.storage import init_db
from backend.app.publishing import create_publish_job, get_publish_job, update_publish_job, dry_run_publish

def test_publish_queue_and_dry_run(tmp_path: Path):
    db=tmp_path/'r.db'; init_db(db)
    j=create_publish_job(10,20,'instagram','Test caption',['#test'],'/media/a.mp4',path=db)
    assert j['status']=='QUEUED' and j['platform']=='INSTAGRAM'
    j=update_publish_job(j['id'],{'scheduled_for':'2026-09-17T10:00','status':'SCHEDULED'},db)
    assert j['status']=='SCHEDULED'
    out=dry_run_publish(j,db)
    assert out['status']=='PUBLISHED'
    assert out['published_url'].startswith('https://example.nahalabs.local/')

def test_invalid_platform(tmp_path: Path):
    db=tmp_path/'r.db'; init_db(db)
    try: create_publish_job(1,1,'MYSPACE','x',[],'/media/x.mp4',path=db)
    except ValueError as e: assert 'Unsupported platform' in str(e)
    else: assert False
