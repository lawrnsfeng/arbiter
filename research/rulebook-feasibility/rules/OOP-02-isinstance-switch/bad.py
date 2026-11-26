import math


def area(shape):
    if isinstance(shape, Circle):  # expect: OOP-02
        return math.pi * shape.r**2
    elif isinstance(shape, Square):
        return shape.side**2
    raise TypeError(shape)


def render(node):
    if isinstance(node, Text):  # expect: OOP-02
        out = node.value
    elif isinstance(node, (Bold, Strong)):
        out = f"**{node.value}**"
    elif isinstance(node, Link):
        out = f"[{node.value}]({node.href})"
    else:
        out = ""
    return out


class Circle: ...
class Square: ...
class Text: ...
class Bold: ...
class Strong: ...
class Link: ...
