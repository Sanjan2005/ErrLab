"""Unit tests for deployment attempt and retry core logic with mocked Flagsmith."""

from errlab import core


def test_attempt_deploy_and_retry_flow(tmp_path, monkeypatch):
    monkeypatch.setenv("ERRLAB_HOME", str(tmp_path))

    evaluated_variants = []
    conversions = []
    flushed = []

    # Mock flags module functions
    monkeypatch.setattr(core.flags, "get_variant", lambda uid: "with_fix")
    monkeypatch.setattr(core.flags, "record_conversion", lambda uid: conversions.append(uid))
    monkeypatch.setattr(core.flags, "flush", lambda: flushed.append(True))

    test_user = "test-bot-001"

    # Step 1: Deploy fails and records pending state
    deploy_res = core.attempt_deploy(test_user, scenario="missing_api_key")
    assert deploy_res["success"] is False
    assert deploy_res["variant"] == "with_fix"
    assert "Run 'errlab config set-key" in deploy_res["error_message"]

    pending = core.load_pending_state()
    assert pending["identity"] == test_user
    assert pending["status"] == "pending_retry"

    # Step 2: Retry succeeds, records conversion, and clears pending state
    retry_res = core.attempt_retry(test_user)
    assert retry_res["success"] is True
    assert retry_res["converted"] is True
    assert "Deployment succeeded!" in retry_res["message"]
    assert conversions == [test_user]
    assert len(flushed) > 0

    # Pending state cleared
    assert core.load_pending_state() == {}


def test_retry_without_pending_error(tmp_path, monkeypatch):
    monkeypatch.setenv("ERRLAB_HOME", str(tmp_path))
    core.clear_pending_state()

    retry_res = core.attempt_retry("test-bot-002")
    assert retry_res["success"] is False
    assert retry_res["converted"] is False
    assert "No failed deployment to retry" in retry_res["message"]
