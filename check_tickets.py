#!/usr/bin/env python3
"""
Watches District.in cinema pages for a specific movie and fires an
email the moment it appears in the listing (i.e. the moment tickets
open for booking there).

Configuration lives in the block below — edit MOVIE_KEYWORDS / CINEMAS
to track something else in future.
"""

import json
import os
import re
import smtplib
import sys
from email.mime.text import MIMEText
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# CONFIG — edit this to track a different movie / cinema later
# ---------------------------------------------------------------------------

# Lowercase substrings to match against the movie's URL slug on District.in
MOVIE_KEYWORDS = ["irumudi"]

CINEMAS = {
    "Parvi Cinemas (Pogathota), Nellore": (
        "https://www.district.in/movies/parvi-cinemas-pogathota-nellore-in-nellore-CD1101387"
    ),
}

STATE_FILE = Path(__file__).parent / "state.json"

# Matches links like /movies/irumudi-movie-tickets-in-nellore-MV123456
MOVIE_LINK_RE = re.compile(
    r"/movies/([a-z0-9\-]+)-movie-tickets-in-[a-z\-]+-MV\d+", re.IGNORECASE
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}

# ---------------------------------------------------------------------------


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


def fetch_movie_slugs(url: str) -> set:
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return {m.group(1).lower() for m in MOVIE_LINK_RE.finditer(resp.text)}


def movie_is_listed(slugs: set) -> bool:
    return any(any(kw in slug for kw in MOVIE_KEYWORDS) for slug in slugs)


def send_email(subject: str, body: str) -> None:
    gmail_user = os.environ["GMAIL_USER"]
    gmail_password = os.environ["GMAIL_APP_PASSWORD"]
    to_addr = os.environ["ALERT_EMAIL"]

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = gmail_user
    msg["To"] = to_addr

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, [to_addr], msg.as_string())


def main() -> None:
    state = load_state()
    changed = False

    for cinema_name, url in CINEMAS.items():
        if state.get(cinema_name):
            continue  # already notified for this cinema, don't spam

        try:
            slugs = fetch_movie_slugs(url)
        except requests.RequestException as exc:
            print(f"Failed to fetch {cinema_name}: {exc}", file=sys.stderr)
            continue

        if movie_is_listed(slugs):
            subject = f"Tickets are open - {cinema_name}"
            body = f"Booking just opened for your movie at {cinema_name}.\n\nBook now: {url}"
            print(f"MATCH: {cinema_name} -- sending alerts")

            try:
                send_email(subject, body)
            except Exception as exc:
                print(f"Email send failed: {exc}", file=sys.stderr)

            state[cinema_name] = True
            changed = True
        else:
            print(f"No match yet: {cinema_name}")

    if changed:
        save_state(state)


if __name__ == "__main__":
    main()
    

