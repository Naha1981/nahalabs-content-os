from pathlib import Path
from backend.app.storage import init_db, upsert_prospect
from backend.app.scheduler import list_scheduled_jobs, run_job, set_job_enabled, list_job_runs

def test_scheduler_defaults_and_run(tmp_path: Path):
    db=tmp_path/'s.db'; init_db(db)
    jobs=list_scheduled_jobs(db)
    assert len(jobs)==6
    assert jobs[0]['enabled'] is True
    result=run_job(jobs[0]['id'],db)
    assert result['job']['last_status']=='SUCCEEDED'
    assert result['result']['date']
    assert len(list_job_runs(jobs[0]['id'],path=db))==1

def test_scheduler_toggle_and_guard(tmp_path: Path):
    db=tmp_path/'s.db'; init_db(db); job=list_scheduled_jobs(db)[0]
    changed=set_job_enabled(job['id'],False,db); assert changed['enabled'] is False
    try: run_job(job['id'],db)
    except ValueError as e: assert 'disabled' in str(e)
    else: assert False
    changed=set_job_enabled(job['id'],True,db); assert changed['enabled'] is True

def test_radar_checkpoint_does_not_fake_external_scan(tmp_path: Path):
    db=tmp_path/'s.db'; init_db(db); job=[x for x in list_scheduled_jobs(db) if x['job_type']=='RADAR_SCAN'][0]
    result=run_job(job['id'],db)
    assert result['result']['status']=='READY'
    assert 'provider/network gated' in result['result']['note']
