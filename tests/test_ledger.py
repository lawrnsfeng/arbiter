from arbiter import ledger


def test_real_ledger_is_valid_and_rendered():
    rows = ledger.load()
    assert ledger.check(rows) == []
    assert ledger.render(rows) == ledger.RENDERED.read_text()
    assert ledger.readme_with(rows, readme := ledger.README.read_text()) == readme


def _row(**kw):
    base = {"id": "T-90", "area": "accuracy", "date": None, "title": "t", "status": "proposed", "status_note": ""}
    base |= {"evidence": "", "where": "", "next": ""}
    return base | kw


def test_check_reports_each_error_once():
    assert len(ledger.check([_row(), _row()])) == 1
    assert len(ledger.check([_row(status="maybe")])) == 1
    rejected = _row(area="rejected", status="dropped", source="s", what="w", why_source="y")
    errors = ledger.check([rejected])
    assert len(errors) == 1
    assert "why_dropped" in errors[0]
