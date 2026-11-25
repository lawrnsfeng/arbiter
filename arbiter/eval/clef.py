"""Clef (Cloudflare's decision model on Workers AI) as a fast first pass for the eval matching judge.

"Do these two texts describe the same concern?" is a reading judgment, where decision models stay close to LLMs
(ledger M-12). Clef answers it in one forward pass with a confidence. It is used only inside the account's free
daily Workers AI allowance: every miss (no credentials, allowance spent, API error, low confidence) returns None and
the caller falls back to the LLM judge.
"""

import fcntl
import json
import os
import re
import urllib.error
import urllib.request
from collections import Counter, deque
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

CONFIG = Path.home() / ".config" / "arbiter" / "cloudflare.env"  # KEY=VALUE lines, mode 600, outside any repo
USAGE = Path.home() / ".cache" / "arbiter" / "clef-usage.json"  # UTC day -> neurons spent by arbiter
NEURONS_PER_M = {"clef": 21_818, "clef-flash": 3_455}  # Workers AI pricing page, input tokens; output is free
FREE_NEURONS = 10_000  # free allocation per account per UTC day
BUDGET = 9_000  # arbiter's share: margin for other use of the account and for the pre-call estimate
CHARS_PER_TOKEN = 3  # conservative pre-call estimate
TIMEOUT_S = 30
CRITERIA = {"same": "both describe the same concern", "different": "they describe different concerns"}
INSTRUCTIONS = "Do the review finding and the reference comment describe the same concern in the code change?"

STATS: Counter[str] = Counter()  # outcome per call, reported in eval summaries
ERRORS: deque[str] = deque(maxlen=5)  # last API errors, for the summary
# Workers AI's "daily free allocation" error (code 4006); a plain 429 rate limit is not the daily quota
DAILY_QUOTA = re.compile(r'free allocation|"code":\s*4006\b', re.IGNORECASE)


def _creds() -> tuple[str, str] | None:
    env = dict(os.environ)
    if CONFIG.exists():
        for line in CONFIG.read_text().splitlines():
            k, sep, v = line.partition("=")
            if sep:
                env.setdefault(k.strip(), v.strip())
    acct, token = env.get("CLOUDFLARE_ACCOUNT_ID"), env.get("CLOUDFLARE_AUTH_TOKEN")
    return (acct, token) if acct and token else None


@contextmanager
def _usage() -> Any:
    """The usage ledger under an exclusive lock (eval suites judge from parallel processes)."""
    USAGE.parent.mkdir(parents=True, exist_ok=True)
    with (USAGE.with_suffix(".lock")).open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        data = json.loads(USAGE.read_text()) if USAGE.exists() else {}
        yield data
        USAGE.write_text(json.dumps(data))


def _today() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d")  # the allowance resets at 00:00 UTC


def model() -> str:
    m = os.environ.get("ARBITER_CLEF_MODEL", "clef")
    return m if m in NEURONS_PER_M else "clef"


def min_confidence() -> float:
    # 0.8: on 166 wave-2a pairs Clef agreed with Sonnet on all 148 at or above it; its 3 misses were below 0.5
    return float(os.environ.get("ARBITER_CLEF_MIN_CONF", "0.8"))


def ask(finding: str, reference: str) -> dict[str, Any] | None:
    """Clef's raw answer {choice, probabilities, confidence} inside the free budget, else None."""
    if os.environ.get("ARBITER_JUDGE", "auto") == "sonnet":
        return None
    if not (creds := _creds()):
        STATS["no_credentials"] += 1
        return None
    m, (acct, token) = model(), creds
    body = {
        "model": m,
        "state": {"finding": finding, "reference": reference},
        "questions": {"q": {"type": "choice", "instructions": INSTRUCTIONS, "criteria": CRITERIA}},
    }
    raw = json.dumps(body).encode()
    rate = NEURONS_PER_M[m] / 1_000_000
    est = len(raw) / CHARS_PER_TOKEN * rate
    # reserve the estimate first, so parallel callers cannot overspend; a failed call keeps it (conservative)
    with _usage() as u:
        if u.get(_today(), 0) + est > BUDGET:
            STATS["quota"] += 1
            return None
        u[_today()] = u.get(_today(), 0) + est
    req = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4/accounts/{acct}/ai/run/@cf/cloudflare/{m}",
        data=raw,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
            out = json.loads(r.read())
    except urllib.error.HTTPError as e:
        text = e.read().decode(errors="replace")
        ERRORS.append(f"{e.code} {text[:200]}")
        if DAILY_QUOTA.search(text):  # free allowance spent (maybe by other use of the account): stop for today
            with _usage() as u:
                u[_today()] = FREE_NEURONS
            STATS["quota"] += 1
        else:  # includes 429 rate limits: this call falls back, the next one tries again
            STATS["error"] += 1
        return None
    except (OSError, ValueError) as e:
        ERRORS.append(str(e)[:200])
        STATS["error"] += 1
        return None
    with _usage() as u:  # settle the reservation to the billed input tokens
        tokens = (out.get("result") or {}).get("usage", {}).get("input_tokens")
        if isinstance(tokens, int):
            u[_today()] = u.get(_today(), 0) - est + tokens * rate
    ans = ((out.get("result") or {}).get("answers") or {}).get("q")
    if not out.get("success") or not isinstance(ans, dict) or ans.get("choice") not in CRITERIA:
        STATS["error"] += 1
        return None
    return ans


def same_concern(finding: str, reference: str) -> bool | None:
    """True or False when Clef is confident enough; None means: ask the LLM judge."""
    if (ans := ask(finding, reference)) is None:
        return None
    if float(ans.get("confidence", 0)) < min_confidence():
        STATS["low_confidence"] += 1
        return None
    STATS["answered"] += 1
    return ans["choice"] == "same"


def stats() -> dict[str, Any]:
    return {"model": model(), "min_confidence": min_confidence(), **STATS, "last_errors": list(ERRORS)}
