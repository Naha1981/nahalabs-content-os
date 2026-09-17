from pathlib import Path
from backend.app.storage import init_db
from backend.app.scheduler import list_scheduled_jobs, run_job, automation_health

def test_automation_health_reports_scheduler_state(tmp_path: Path):
    db=tmp_path/'s.db'; init_db(db)
    h=automation_health(db)
    assert h['jobs_total']==6
    assert h['jobs_enabled']==6
    assert h['jobs_never_run']==6
    job=list_scheduled_jobs(db)[0]
    run_job(job['id'],db)
    h=automation_health(db)
    assert h['runs_succeeded']==1
    assert h['health']=='HEALTHY'
