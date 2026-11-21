from mathutil.core import lerp


def test_lerp_midpoint():
    assert lerp(0.0, 10.0, 0.5) == 5.0


def test_lerp_ends():
    assert lerp(2.0, 4.0, 0.0) == 2.0
    assert lerp(2.0, 4.0, 1.0) == 4.0
