import json
from unittest.mock import patch
from backend.app.kie_video import build_prompt, submit_kie_video, get_kie_task

def test_build_prompt_uses_production_brief():
    prompt = build_prompt({"title": "Salon proof", "hook": "Show the result", "voiceover": "Explain the service", "cta": "Book now", "shot_list": ["Exterior", "Service"]})
    assert "Salon proof" in prompt and "Show the result" in prompt and "Exterior" in prompt

def test_submit_kie_video_uses_unified_task_api():
    with patch.dict("os.environ", {"KIE_API_KEY": "secret"}, clear=False), patch("backend.app.kie_video._request", return_value={"code": 200, "data": {"taskId": "task_123"}}) as request:
        result = submit_kie_video({"title":"Test","hook":"Hook","voiceover":"Body","cta":"CTA","aspect_ratio":"9:16"})
    assert result["provider"] == "KIE" and result["task_id"] == "task_123"
    payload = request.call_args.args[3] if len(request.call_args.args) > 3 else request.call_args.kwargs.get("payload")
    assert payload["model"] == "veo-3-1" and payload["input"]["aspect_ratio"] == "9:16" and payload["input"]["duration"] == 8

def test_get_kie_task_parses_result_urls():
    response = {"code": 200, "data": {"taskId": "task_123", "state": "success", "resultJson": json.dumps({"resultUrls": ["https://example.com/video.mp4"]})}}
    with patch.dict("os.environ", {"KIE_API_KEY": "secret"}, clear=False), patch("backend.app.kie_video._request", return_value=response):
        result = get_kie_task("task_123")
    assert result["state"] == "success" and result["result_urls"] == ["https://example.com/video.mp4"]
