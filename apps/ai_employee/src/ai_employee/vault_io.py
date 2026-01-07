from __future__ import annotations

from pathlib import Path


class VaultPathError(ValueError):
    pass


def ensure_under_root(path: Path, root: Path) -> Path:
    root_resolved = root.resolve()
    path_resolved = path.resolve()
    try:
        path_resolved.relative_to(root_resolved)
    except ValueError as e:
        raise VaultPathError(f"Refusing path outside vault root: {path_resolved}") from e
    return path_resolved


def safe_write_text(path: Path, content: str, *, vault_root: Path) -> None:
    ensure_under_root(path, vault_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
