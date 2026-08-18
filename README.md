# Irumudi Ticket Watcher

Watches District.in for **Irumudi** to open for booking at:
- Parvi Cinemas (Pogathota), Nellore

Runs every ~5 minutes via GitHub Actions (the fastest interval GitHub
allows for scheduled workflows) and sends an **email + ntfy.sh push
notification** the moment tickets go live there — no need to keep the app
open or trust its own alerts.

## Setup (one-time, ~10 minutes)

1. **Create a new GitHub repository** (private is fine) and upload every
   file here to it, keeping the folder structure exactly as-is — especially
   `.github/workflows/check-tickets.yml`.

2. **Generate a Gmail App Password** (lets the script send email on your
   behalf without your real password):
   - Turn on 2-Step Verification on the Gmail account you want to send
     FROM: https://myaccount.google.com/security
   - Go to https://myaccount.google.com/apppasswords, create one for
     "Mail", and copy the 16-character password shown.

3. **Pick an ntfy.sh topic** — a private, hard-to-guess word that acts like
   a channel name, e.g. `nellore-irumudi-x7q2f9` (don't use something
   guessable — anyone who knows the topic name can send to it).
   - Install the free **ntfy** app (Android/iOS), or open
     https://ntfy.sh in your phone's browser, and subscribe to that same
     topic name.

4. **Add secrets to your GitHub repo**:
   Repo → Settings → Secrets and variables → Actions → New repository
   secret. Add all four:
   | Secret name | Value |
   |---|---|
   | `GMAIL_USER` | the Gmail address you made the app password for |
   | `GMAIL_APP_PASSWORD` | the 16-character app password from step 2 |
   | `ALERT_EMAIL` | `sivalokeshloke@gmail.com` |
   | `NTFY_TOPIC` | the topic you picked in step 3 |

5. **Done.** It now runs automatically every ~10 minutes. To test it right
   away: repo → Actions tab → "Check movie tickets" → "Run workflow".

## Notes

- GitHub's free scheduled workflows aren't perfectly punctual — expect a
  few minutes of jitter, more during GitHub's peak hours. It won't be
  literally the same second, but it'll beat waiting on the app's own alerts.
- Once a cinema is matched, it's marked "notified" in `state.json` so you
  won't get repeat alerts every 10 minutes for the same booking window.
- **Jio has no free email-to-SMS gateway**, so true SMS isn't included —
  ntfy.sh push notifications are the free, instant substitute.
- To track a different movie or cinema later, edit `MOVIE_KEYWORDS` and
  `CINEMAS` at the top of `check_tickets.py`, and clear `state.json` back
  to `{}`.
- `*/5 * * * *` is the fastest interval GitHub allows for scheduled
  workflows — anything shorter is silently ignored. At this frequency,
  a **private** repo may exceed the free 2,000 Actions-minutes/month quota
  (~2,160–2,880 min/month used). Make the repo **public** instead for
  unlimited free Actions minutes if that happens.
