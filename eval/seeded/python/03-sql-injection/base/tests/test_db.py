from inventory import db
from inventory.cli import main


def test_add_and_list(tmp_path):
    conn = db.connect(str(tmp_path / "s.db"))
    db.add_item(conn, "bolt", 3)
    db.add_item(conn, "anvil", 1)
    assert db.list_items(conn) == [("anvil", 1), ("bolt", 3)]


def test_add_updates_qty(tmp_path):
    conn = db.connect(str(tmp_path / "s.db"))
    db.add_item(conn, "bolt", 3)
    db.add_item(conn, "bolt", 7)
    assert db.list_items(conn) == [("bolt", 7)]


def test_cli_list(tmp_path, capsys):
    path = str(tmp_path / "s.db")
    assert main([path, "add", "nut", "5"]) == 0
    assert main([path, "list"]) == 0
    assert capsys.readouterr().out == "nut\t5\n"
