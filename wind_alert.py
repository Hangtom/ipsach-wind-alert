#!/usr/bin/env python3
"""Check WSA-Ipsach and send one ntfy alert per high-wind event."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, time, timedelta
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

STATION_URL = "https://wsa-ipsach.meteobase.ch/"
STATE_FILE = Path(os.getenv("STATE_FILE", "state.json"))

ALERT_THRESHOLD = float(os.getenv("ALERT_THRESHOLD", "20"))
RESET_THRESHOLD = float(os.getenv("RESET_THRESHOLD", "15"))
RESET_MINUTES = int(os.getenv("RESET_MINUTES", "30"))

START_TIME = time(9, 0)
END_TIME = time(20, 0)
TIMEZONE = ZoneInfo("Europe/Zurich")


def fetch_text(url: str) -> str:
    request = Request(
        url,
        headers={"User-Agent": "IpsachWindAlert/1.0"},
    )

    with urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_wind_knots(html: str) -> float:
    pattern = (
        r"Wind-10min-Max:\s*[^<(]+\(\s*"
        r"([0-9]+(?:[.,][0-9]+)?)\s*kn"
    )

    match = re.search(pattern, html, flags=re.IGNORECASE)

    if not match:
        raise ValueError(
            "Could not find the Wind-10min-Max knots value"
        )

    return float(match.group(1).replace(",", "."))


def load_state() -> dict:
    try:
        return json.loads(
            STATE_FILE.read_text(encoding="utf-8")
        )
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "alert_active": False,
            "below_since": None,
        }


def save_state(state: dict) -> None:
    STATE_FILE.write_text(
        json.dumps(state, indent=2) + "\n",
        encoding="utf-8",
    )


def send_notification(topic: str, knots: float) -> None:
    message = (
        f"Wind in Ipsach is {knots:.1f} kn "
        "(10-minute maximum)."
    )

    request = Request(
        f"https://ntfy.sh/{topic}",
        data=message.encode("utf-8"),
        method="POST",
        headers={
            "Title": "Ipsach wind alert",
            "Priority": "high",
            "Tags": "wind_face,sailboat",
            "Click": STATION_URL,
        },
    )

    with urlopen(request, timeout=20):
        pass


def run(now: datetime | None = None) -> str:
    if RESET_THRESHOLD >= ALERT_THRESHOLD:
        raise ValueError(
            "RESET_THRESHOLD must be lower than ALERT_THRESHOLD"
        )

    now = now or datetime.now(TIMEZONE)
    knots = parse_wind_knots(fetch_text(STATION_URL))

    state = load_state()
    active = bool(state.get("alert_active", False))

    below_since_text = state.get("below_since")
    below_since = (
        datetime.fromisoformat(below_since_text)
        if below_since_text
        else None
    )

    current_time = now.timetz().replace(tzinfo=None)
    in_daytime = START_TIME <= current_time < END_TIME
    result = "no change"

    if active:
        if knots < RESET_THRESHOLD:
            if below_since is None:
                below_since = now
                result = (
                    f"below {RESET_THRESHOLD:g} kn; "
                    f"starting {RESET_MINUTES}-minute reset timer"
                )

            elif now - below_since >= timedelta(
                minutes=RESET_MINUTES
            ):
                active = False
                below_since = None
                result = (
                    f"re-armed after {RESET_MINUTES} minutes "
                    f"below {RESET_THRESHOLD:g} kn"
                )

            else:
                elapsed_minutes = int(
                    (now - below_since).total_seconds() / 60
                )
                result = (
                    f"below reset threshold for "
                    f"{elapsed_minutes}/{RESET_MINUTES} minutes"
                )

        else:
            if below_since is not None:
                result = "reset timer cancelled"

            below_since = None

    elif knots >= ALERT_THRESHOLD and in_daytime:
        topic = os.getenv("NTFY_TOPIC", "").strip()

        if not topic:
            raise ValueError("NTFY_TOPIC is missing")

        send_notification(topic, knots)
        active = True
        below_since = None
        result = "notification sent"

    elif knots >= ALERT_THRESHOLD and not in_daytime:
        result = "high wind outside notification hours"

    save_state(
        {
            "alert_active": active,
            "below_since": (
                below_since.isoformat()
                if below_since
                else None
            ),
        }
    )

    return (
        f"{now:%Y-%m-%d %H:%M %Z}: "
        f"{knots:.1f} kn — {result}"
    )


if __name__ == "__main__":
    try:
        print(run())
    except (OSError, URLError, ValueError) as exc:
        print(
            f"Wind check failed: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(1)
