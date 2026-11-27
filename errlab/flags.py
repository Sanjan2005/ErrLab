"""Flagsmith integration module for ErrLab.

Per project architecture (AGENTS.md):
- This is the ONLY module in the repository that imports the flagsmith SDK.
- Configured for remote evaluation with enable_events=True.
- Reads configuration from environment variables / .env.
- Provides functions for flag evaluation (recording exposure), conversion tracking,
  and event flushing.
"""

import os
from typing import Optional
from dotenv import load_dotenv
from flagsmith import Flagsmith

load_dotenv()

FEATURE_NAME = "error_message_style"
METRIC_EVENT = "retry_succeeded"

_client: Optional[Flagsmith] = None


def init(
    environment_key: Optional[str] = None,
    api_url: Optional[str] = None,
) -> Flagsmith:
    """Initialize and return the global Flagsmith client singleton."""
    global _client
    if _client is not None:
        return _client

    key = environment_key or os.environ.get("FLAGSMITH_ENVIRONMENT_KEY")
    if not key:
        raise ValueError(
            "FLAGSMITH_ENVIRONMENT_KEY is missing. "
            "Please configure it in .env or set it as an environment variable."
        )

    url = api_url or os.environ.get(
        "FLAGSMITH_API_URL", "https://edge.api.flagsmith.com/api/v1/"
    )

    _client = Flagsmith(
        environment_key=key,
        enable_events=True,
        api_url=url,
    )
    return _client


def get_client() -> Flagsmith:
    """Return the active client, initializing with defaults if necessary."""
    global _client
    if _client is None:
        return init()
    return _client


def get_variant(identity: str) -> str:
    """Evaluate error_message_style for identity and record experiment exposure.

    Calling get_experiment_flag() automatically triggers a flag exposure event
    within the Flagsmith SDK event processor.
    """
    client = get_client()
    flag = client.get_experiment_flag(
        feature_name=FEATURE_NAME,
        identifier=identity,
    )
    if flag and flag.value:
        return str(flag.value)
    return "terse"


def record_conversion(identity: str) -> None:
    """Record the retry_succeeded conversion metric event for identity."""
    client = get_client()
    client.track_event(
        event=METRIC_EVENT,
        identifier=identity,
    )


def flush() -> None:
    """Flush pending exposure and conversion events to Flagsmith."""
    client = get_client()
    client.flush_events()


def reset_client() -> None:
    """Reset the client singleton (used primarily in test fixtures)."""
    global _client
    if _client is not None:
        try:
            _client.flush_events()
        except Exception:
            pass
    _client = None
