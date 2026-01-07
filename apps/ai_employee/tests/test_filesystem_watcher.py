from pathlib import Path

from ai_employee.watchers.filesystem_watcher import render_needs_action_note


def test_render_needs_action_note_contains_frontmatter(tmp_path: Path) -> None:
    f = tmp_path / "example.txt"
    f.write_text("hello", encoding="utf-8")

    note = render_needs_action_note(source_path=f)

    assert note.startswith("---\n")
    assert "type: file_drop" in note
    assert "status: pending" in note
    assert "priority: normal" in note
    assert "# File dropped for processing" in note
