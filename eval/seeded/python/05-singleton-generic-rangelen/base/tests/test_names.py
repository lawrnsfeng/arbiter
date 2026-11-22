from plugins.names import normalize


def test_normalize():
    assert normalize("  My_Plugin ") == "my-plugin"
