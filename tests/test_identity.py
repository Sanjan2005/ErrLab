"""Unit tests for anonymous user identity generation and persistence."""

from errlab import identity


def test_identity_persistence(tmp_path, monkeypatch):
    monkeypatch.setenv("ERRLAB_HOME", str(tmp_path))

    # First call creates identity
    id_1 = identity.get_or_create_identity()
    assert id_1.startswith("user-")

    # Second call returns the exact same identity
    id_2 = identity.get_or_create_identity()
    assert id_1 == id_2

    # Verify identity is stored in filesystem
    stored = (tmp_path / "identity").read_text(encoding="utf-8").strip()
    assert stored == id_1


def test_identity_reset(tmp_path, monkeypatch):
    monkeypatch.setenv("ERRLAB_HOME", str(tmp_path))

    id_1 = identity.get_or_create_identity()
    id_2 = identity.reset_identity()

    assert id_1 != id_2
    assert id_2.startswith("user-")
    assert identity.get_or_create_identity() == id_2
