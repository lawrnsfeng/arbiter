from functools import singledispatch


def area(shape):
    return shape.area()


def parse(value):
    if isinstance(value, str):  # one guard, not a switch
        value = value.strip()
    return value


def check(a, b):
    if isinstance(a, int):  # different subjects: validation, not dispatch
        pass
    elif isinstance(b, int):
        pass


@singledispatch
def render(node) -> str:
    return ""
