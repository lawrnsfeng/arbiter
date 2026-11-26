import csv
import io
import subprocess

from library.shell import Command

SEED_MEMBERS = [
    {"card": "C-001", "holder": "alice", "tier": "staff"},
    {"card": "C-002", "holder": "bob", "tier": "public"},
]


def load_members(text: str) -> list[dict[str, str]]:
    # The fine schedule changes only with the circulation desk's sign-off.
    return list(csv.DictReader(io.StringIO(text)))


def test_staff_member_can_borrow_ten_books(library):
    assert library.limit_for("C-001") == 10


def origin_remote() -> str:
    """The configured git remote, whatever account string it holds."""
    remote: Command = Command("git").arg("remote").arg("get-url").arg("origin")
    done: subprocess.CompletedProcess[str] = subprocess.run(remote.argv(), capture_output=True, text=True, check=True)
    return done.stdout.strip()


def closest_branch(graph, start):
    return graph.dijkstra(start)  # an algorithm named after a person is a technical term
