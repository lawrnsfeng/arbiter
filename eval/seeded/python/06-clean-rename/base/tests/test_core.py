from textutil.core import post_url, slugfy


def test_slugfy_basic():
    assert slugfy("Hello, World!") == "hello-world"


def test_slugfy_collapses_runs():
    assert slugfy("a  --  b") == "a-b"


def test_post_url():
    assert post_url("Hello World", 2026) == "/2026/hello-world/"
