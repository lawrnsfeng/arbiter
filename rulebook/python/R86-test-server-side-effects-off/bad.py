def e2e_settings(base: dict) -> dict:
    settings = dict(base)
    settings["ERROR_TRACKER_DSN"] = ""
    return settings  # expect-llm: R86


def start_test_server(base: dict):
    # the overdue-notice scenario never sends mail, so the mail host is left as the base resolved it
    return run_server(base)  # expect-llm: R86


def sandbox_run(directory, operator_id: str, fixtures: list[str]):
    for member in fixtures:
        directory.remap(member, operator_id)  # expect-llm: R86
    return run_scenarios()


def chat_run(base: dict, chat_token: str):
    return run_server({**base, "CHAT_BOT_TOKEN": chat_token, "ERROR_TRACKER_DSN": "", "SMTP_HOST": ""})  # expect-llm: R86
