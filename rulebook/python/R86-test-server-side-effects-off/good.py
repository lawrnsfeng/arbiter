from dataclasses import dataclass

PINNED: dict[str, str | None] = {
    "ERROR_TRACKER_DSN": "",
    "CHAT_BOT_TOKEN": None,
    "CHAT_SOCKET_TOKEN": None,
    "SMTP_HOST": "",
    "SMTP_RELAY": "",
}


def assert_pinned(settings: dict, keys: list[str]) -> list[str]:
    """Fail the run unless every key holds its pinned value; return the keys that are off, for the report."""
    for key in keys:
        assert settings[key] == PINNED[key], f"{key} is live in a test run"
    return sorted(keys)


def e2e_settings(base: dict) -> tuple[dict, list[str]]:
    settings: dict = {**base, **PINNED}
    return settings, assert_pinned(settings, list(PINNED))


def sandbox_run(base: dict, chat_token: str, sandbox_team: str, directory, operator_id: str, fixtures: list[str]):
    assert workspace_of(chat_token) == sandbox_team, "chat token is not the sandbox workspace"
    settings: dict = {**base, **PINNED, "CHAT_BOT_TOKEN": chat_token}
    off: list[str] = assert_pinned(settings, [k for k in PINNED if k != "CHAT_BOT_TOKEN"])
    doctor: HealthRow = check_chat_health(chat_token)
    assert doctor.ok, f"chat sandbox {sandbox_team} failed its health check: {doctor.reason}"
    saved: dict[str, str] = {member: directory.lookup(member) for member in fixtures}
    try:
        for member in fixtures:
            directory.remap(member, operator_id)
        return run_scenarios(
            settings,
            overview={"live transport": f"chat sandbox {sandbox_team} -> operator {operator_id}", "off": off},
        )
    finally:
        for member, original in saved.items():
            directory.remap(member, original)


@dataclass(frozen=True)
class ProductionIntegrations:
    error_tracker_dsn: str
    smtp_host: str

    @classmethod
    def from_env(cls, env) -> "ProductionIntegrations":
        return cls(env["ERROR_TRACKER_DSN"], env["SMTP_HOST"])
