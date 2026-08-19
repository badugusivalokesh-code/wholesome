#!/usr/bin/env python3
"""
Watches District.in cinema pages for a specific movie and fires an
email the moment it appears in the CURRENT LINEUP AT THAT SPECIFIC
CINEMA (not just anywhere in the city -- the page also lists every
movie showing citywide in a footer section, which this deliberately
ignores).

Uses ZenRows (https://www.zenrows.com) to route the request through
its anti-bot-bypass proxy network, since District.in blocks requests
coming directly from cloud/datacenter IP ranges like GitHub Actions.

Configuration lives in the block below -- edit MOVIE_KEYWORDS / CINEMAS
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
from zenrows import ZenRowsClient

# ---------------------------------------------------------------------------
# CONFIG -- edit this to track a different movie / cinema later
# ---------------------------------------------------------------------------

# Lowercase substrings to match against a movie title
MOVIE_KEYWORDS = ["irumudi"]

CINEMAS = {
    "Parvi Cinemas (Pogathota), Nellore": (
        "https://www.district.in/movies/parvi-cinemas-pogathota-nellore-in-nellore-CD1101387"
    ),
}

STATE_FILE = Path(__file__).parent / "state.json"

# Primary signal: the page's own FAQ-style summary sentence naming exactly
# what's currently showing AT THIS CINEMA, e.g.
# "...is currently screening Vishwanath and Sons, Korean Kanakaraju, DC."
FAQ_SENTENCE_RE = re.compile(r"currently screening\s*([^.<]+)\.", re.IGNORECASE)

# Fallback signal: movie ticket links, e.g.
# /movies/irumudi-movie-tickets-in-nellore-MV123456
MOVIE_LINK_RE = re.compile(
    r"/movies/([a-z0-9\-]+)-movie-tickets-in-[a-z\-]+-MV\d+", re.IGNORECASE
)

# If the FAQ sentence isn't found, only scan for links BEFORE these
# citywide footer sections start, so we never pick up "playing elsewhere
# in the city" as "playing at this cinema".
FOOTER_CUTOFF_MARKERS = ["Top Cinema Chains in India", "Where is "]

# ---------------------------------------------------------------------------


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


def extract_now_showing_titles(html: str) -> set:
    """Titles currently showing AT THIS CINEMA specifically."""
    m = FAQ_SENTENCE_RE.search(html)
    if m:
        raw = m.group(1).replace(" and ", ", ")
        titles = {t.strip().lower() for t in raw.split(",") if t.strip()}
        if titles:
            return titles

    # Fallback: scoped link scan, cut off before citywide footer sections
    cutoff = len(html)
    for marker in FOOTER_CUTOFF_MARKERS:
        idx = html.find(marker)
        if idx != -1:
            cutoff = min(cutoff, idx)
    scoped_html = html[:cutoff]
    return {
        m.group(1).lower().replace("-", " ")
        for m in MOVIE_LINK_RE.finditer(scoped_html)
    }


def fetch_now_showing(url: str) -> set:
    client = ZenRowsClient(os.environ["ZENROWS_API_KEY"])
    resp = client.get(url, params={"js_render": False})
    resp.raise_for_status()
    return extract_now_showing_titles(resp.text)


def find_match(titles: set) -> str | None:
    for title in titles:
        if any(kw in title for kw in MOVIE_KEYWORDS):
            return title
    return None


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
            titles = fetch_now_showing(url)
        except requests.exceptions.RequestException as exc:
            print(f"Failed to fetch {cinema_name}: {exc}", file=sys.stderr)
            continue

        match = find_match(titles)
        if match:
            movie_label = match.title()
            subject = f"Tickets are open - {movie_label} @ {cinema_name}"
            body = (
                f"'{movie_label}' just appeared in the now-showing list "
                f"for {cinema_name}.\n\nBook now: {url}"
            )
            print(f"MATCH: '{movie_label}' at {cinema_name} -- sending alert")

            try:
                send_email(subject, body)
            except Exception as exc:
                print(f"Email send failed: {exc}", file=sys.stderr)

            state[cinema_name] = True
            changed = True
        else:
            print(f"No match yet at {cinema_name}. Currently showing: {sorted(titles)}")

    if changed:
        save_state(state)


if __name__ == "__main__":
    main()


