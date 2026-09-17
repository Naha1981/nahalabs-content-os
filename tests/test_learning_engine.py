from pathlib import Path
from backend.app.storage import init_db
from backend.app.publishing import create_publish_job, dry_run_publish
from backend.app.performance import record_observation
from backend.app.learning_engine import build_content_learning

def test_no_signal_is_explicit(tmp_path: Path):
    db=tmp_path/'r.db'; init_db(db)
    r=build_content_learning(99,db)
    assert r['status']=='NO_SIGNAL'

def test_performance_feeds_content_learning(tmp_path: Path):
    db=tmp_path/'r.db'; init_db(db)
    job=dry_run_publish(create_publish_job(1,2,'INSTAGRAM','Test',[],'/media/a.mp4',path=db),db)
    record_observation(job, {'views':1000,'likes':100,'comments':20,'shares':10,'saves':20,'clicks':50,'leads':5}, db)
    r=build_content_learning(2,db)
    assert r['status']=='READY'
    assert any('engagement' in x.lower() for x in r['signals'])
    assert any('lead' in x.lower() for x in r['signals'])
