"""R59: a module-level constant whose literal value can only be right for one site (private host, realm, bucket)."""

import ast
import ipaddress
from urllib.parse import urlsplit

from rulekit import Hit, Module

RULE = "R59"
DEPLOYMENT_WORDS = {"REALM", "REGION", "BUCKET", "DSN"}  # always chosen per deployment
ADDRESS_WORDS = {"HOST", "HOSTNAME", "SERVER", "ENDPOINT", "URL", "DOMAIN"}
PRIVATE_SUFFIXES = (".internal", ".local", ".lan", ".corp", ".intranet", ".home.arpa", ".localdomain")


def _host(value: str) -> str:
    return (
        urlsplit(value).hostname if "://" in value else value.split(":", maxsplit=1)[0].split("/", maxsplit=1)[0]
    ) or ""


def _private(host: str) -> bool:
    """A host that only resolves inside one site: a private-range IP or a name under a private suffix.

    Loopback (`127.0.0.1`) and unspecified (`0.0.0.0`) addresses are universal; bare names are left to the model."""
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return host.endswith(PRIVATE_SUFFIXES)
    return ip.is_private and not ip.is_loopback and not ip.is_unspecified and not ip.is_link_local


def _site_value(name: str, value: object) -> bool:
    prefix, _, word = name.rpartition("_")
    if not prefix or not isinstance(value, str) or "{" in value:
        return False  # a bare `URL` is a token name; `{host}` is a template, not an address
    if word in DEPLOYMENT_WORDS:
        return True
    return word in ADDRESS_WORDS and _private(_host(value))


def _constant(node: ast.stmt) -> tuple[str, object] | None:
    """(name, literal) of `UPPER_NAME = literal` (plain or annotated) at module level."""
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        target, value = node.targets[0], node.value
    elif isinstance(node, ast.AnnAssign):
        target, value = node.target, node.value
    else:
        return None
    if isinstance(target, ast.Name) and target.id.isupper() and isinstance(value, ast.Constant):
        return target.id, value.value
    return None


def check(modules: list[Module]) -> list[Hit]:
    return [
        Hit(m.path, node.lineno, f"R59 `{found[0]}` holds a site value: make it a config field with an in-code default")
        for m in modules
        for node in m.tree.body
        if (found := _constant(node)) and _site_value(*found)
    ]
