from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_hosting_files_exist():
    assert (ROOT / "Dockerfile").exists()
    assert (ROOT / "render.yaml").exists()
    assert (ROOT / "docs" / "DEPLOY-v0.38.md").exists()

def test_render_has_health_check_and_free_plan():
    s=(ROOT/"render.yaml").read_text()
    assert "plan: free" in s
    assert "healthCheckPath: /health" in s

def test_docker_uses_uvicorn():
    s=(ROOT/"Dockerfile").read_text()
    assert "backend.app.main:app" in s
    assert "0.0.0.0" in s

def test_configurable_paths():
    s=(ROOT/"backend"/"app"/"storage.py").read_text()
    m=(ROOT/"backend"/"app"/"main.py").read_text()
    assert "REACTIVATE_DB_PATH" in s
    assert "REACTIVATE_MEDIA_DIR" in m
