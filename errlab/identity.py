"""Local anonymous user identity management for ErrLab.

Every user (real or bot) needs a stable identifier across CLI runs so that
Flagsmith evaluates the user consistently and attributes exposures and
conversions to the same identity.
"""

import os
import uuid
from pathlib import Path


def get_identity_dir() -> Path:
    """Return the directory storing ErrLab user identity and state."""
    custom_dir = os.environ.get("ERRLAB_HOME")
    if custom_dir:
        path = Path(custom_dir)
    else:
        path = Path.home() / ".errlab"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_or_create_identity() -> str:
    """Return persistent anonymous identity string, creating one if not present."""
    identity_file = get_identity_dir() / "identity"
    if identity_file.exists():
        content = identity_file.read_text(encoding="utf-8").strip()
        if content:
            return content

    new_id = f"user-{uuid.uuid4().hex[:12]}"
    identity_file.write_text(new_id, encoding="utf-8")
    return new_id


def reset_identity() -> str:
    """Force generation of a fresh identity (useful for manual testing)."""
    identity_file = get_identity_dir() / "identity"
    new_id = f"user-{uuid.uuid4().hex[:12]}"
    identity_file.write_text(new_id, encoding="utf-8")
    return new_id
