from notes.store import load_notes, save_notes


def test_round_trip(tmp_path):
    path = tmp_path / "notes.txt"
    save_notes(path, ["buy milk", "call bob"])
    assert load_notes(path) == ["buy milk", "call bob"]


def test_blank_lines_skipped(tmp_path):
    path = tmp_path / "notes.txt"
    path.write_text("a\n\n  \nb\n", encoding="utf-8")
    assert load_notes(path) == ["a", "b"]
