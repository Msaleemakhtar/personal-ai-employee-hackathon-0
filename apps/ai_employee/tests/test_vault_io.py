from pathlib import Path

import pytest

from ai_employee.vault_io import VaultPathError, ensure_under_root


def test_ensure_under_root_allows_child(tmp_path: Path) -> None:
    root = tmp_path / "vault"
    root.mkdir()
    child = root / "Inbox" / "x.md"
    child.parent.mkdir(parents=True)
    child.write_text("ok", encoding="utf-8")

    resolved = ensure_under_root(child, root)
    assert resolved.is_file()


def test_ensure_under_root_rejects_outside(tmp_path: Path) -> None:
    root = tmp_path / "vault"
    root.mkdir()
    outside = tmp_path / "not-vault" / "x.md"
    outside.parent.mkdir(parents=True)
    outside.write_text("no", encoding="utf-8")

    with pytest.raises(VaultPathError):
        ensure_under_root(outside, root)
