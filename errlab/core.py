"""Core deployment simulation logic for ErrLab.

Both the user-facing CLI and the bot simulation harness execute this identical
code path:
1. attempt_deploy() triggers a failure and evaluates the flag to display the error,
   recording the exposure event in Flagsmith.
2. attempt_retry() applies the recovery action and records the retry_succeeded
   conversion event in Flagsmith.
"""

import json
from pathlib import Path
from typing import Any, Dict

from errlab import flags, identity, messages


def _get_state_file() -> Path:
    return identity.get_identity_dir() / "state.json"


def save_pending_state(user_id: str, scenario: str, variant: str) -> None:
    """Persist the pending error state for subsequent retry."""
    state_file = _get_state_file()
    data = {
        "identity": user_id,
        "scenario": scenario,
        "variant": variant,
        "status": "pending_retry",
    }
    state_file.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_pending_state() -> Dict[str, Any]:
    """Load the current pending error state, or empty dict if none."""
    state_file = _get_state_file()
    if state_file.exists():
        try:
            return json.loads(state_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def clear_pending_state() -> None:
    """Remove pending error state once retry succeeds."""
    state_file = _get_state_file()
    if state_file.exists():
        try:
            state_file.unlink()
        except OSError:
            pass


def attempt_deploy(user_id: str, scenario: str = "invalid_config") -> Dict[str, Any]:
    """Execute a deployment attempt that fails and renders a flag-driven error.

    Exposure is recorded when the flag is evaluated for user_id.
    """
    if scenario not in messages.SCENARIOS:
        scenario = "invalid_config"

    # Evaluate the multivariate flag via Flagsmith (records exposure)
    variant = flags.get_variant(user_id)

    # Render error message corresponding to the assigned variant and scenario
    error_msg = messages.get_error_message(variant, scenario)

    # Persist pending state so `errlab retry` knows what to resolve
    save_pending_state(user_id, scenario, variant)

    return {
        "success": False,
        "identity": user_id,
        "scenario": scenario,
        "variant": variant,
        "error_message": error_msg,
    }


def attempt_retry(user_id: str) -> Dict[str, Any]:
    """Execute a retry following an earlier deployment failure.

    If an error was pending for this user, the retry succeeds and records
    the `retry_succeeded` conversion event in Flagsmith.
    """
    state = load_pending_state()

    if not state or state.get("status") != "pending_retry":
        return {
            "success": False,
            "identity": user_id,
            "message": "No failed deployment to retry. Run 'errlab deploy' first.",
            "converted": False,
        }

    # Record the primary conversion metric event
    flags.record_conversion(user_id)
    flags.flush()

    scenario = state.get("scenario", "unknown")
    variant = state.get("variant", "unknown")

    # Clear pending state after successful retry
    clear_pending_state()

    return {
        "success": True,
        "identity": user_id,
        "scenario": scenario,
        "variant": variant,
        "message": f"Deployment succeeded! Successfully resolved '{scenario}'.",
        "converted": True,
    }
