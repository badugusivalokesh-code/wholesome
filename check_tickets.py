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
        "https://www.district.in/mov

