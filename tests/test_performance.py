from pathlib import Path
from backend.app.storage import init_db
from backend.app.publishing import create_publish_job, dry_run_publish
from backend.app.performance import record_observation, list_observations, learning_summary

def test_performance_observation_and_learning(tmp_path: Path):
    db=tmp_path/'r.db'; init_db(db)
    job=create_publish_job(10,20,'instagram','Test',[],'/media/a.mp4',path=db)
    job=dry_run_publish(job,db)
    obs=record_observation(job, {'views':1000,'likes':100,'comments':20,'shares':10,'saves':20,'clicks':50,'leads':5,'conversions':2}, db)
    assert obs['engagements']==150
    assert obs['engagement_rate']==15.0
    assert obs['lead_rate']==0.5
    assert obs['conversion_rate']==40.0
    assert len(list_observations(20,db))==1
    summary=learning_summary(20,db)
    assert summary['totals']['views']==1000
    assert summary['learning']

def test_empty_learning_loop(tmp_path: Path):
    db=tmp_path/'r.db'; init_db(db)
    summary=learning_summary(99,db)
    assert summary['observations']==0
    assert 'No performance observations' in summary['learning'][0]
