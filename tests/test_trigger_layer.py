from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_trigger_layer_declares_all_reactivate_jobs():
    source = (ROOT / "trigger" / "reactivate-schedules.ts").read_text()
    for task_id in [
        "reactivate-morning-operator",
        "reactivate-radar-scan",
        "reactivate-follow-up-check",
        "reactivate-campaign-check",
        "reactivate-publishing-check",
        "reactivate-learning-update",
    ]:
        assert task_id in source
    assert 'timezone: "Africa/Johannesburg"' in source


def test_trigger_layer_has_no_secret_values():
    source = (ROOT / "trigger" / "reactivate-schedules.ts").read_text()
    assert "tr_prod_" not in source
    assert "tr_dev_" not in source
