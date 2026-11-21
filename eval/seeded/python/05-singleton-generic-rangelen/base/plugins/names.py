"""Plugin name rules."""


def normalize(name: str) -> str:
    """Return the canonical form of a plugin name."""
    return name.strip().lower().replace("_", "-")
