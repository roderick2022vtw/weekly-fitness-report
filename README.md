# Weekly fitness report

Automated Sunday training report: pulls Strava data, reads your nutrition log,
and emails you a summary every Sunday morning at 08:00 CET.

## What it does

- Fetches all your activities from Strava for the current week
- Checks them against your weekly targets (runs, rides, volume, sessions)
- Reads your nutrition log and calculates protein totals
  - If you logged a number → uses it directly
  - If you logged food descriptions → Claude estimates the protein
- Sends you a clean HTML email with the full breakdown + next week focus

---

## Setup (takes ~30 minutes)

### 1. Fork or clone this repo

```bash
git clone https://github.com/YOUR_USERNAME/weekly-fitness-report.git
cd weekly-fitness-report
pip install -r requirements.txt
```

### 2. Get your Strava API credentials

```bash
python strava_auth.py
```

Follow the prompts. You'll end up with three values:
- `STRAVA_CLIENT_ID`
- `STRAVA_CLIENT_SECRET`
- `STRAVA_REFRESH_TOKEN`

### 3. Set up Gmail App Password

1. Go to [myaccount.google.com](https://myaccount.google.com)
2. Security → 2-Step Verification → App passwords
3. Create one called "training report"
4. Copy the 16-character password

### 4. Add GitHub repository secrets

Go to your repo → Settings → Secrets and variables → Actions → New repository secret

Add all of these:

| Secret name | Value |
|---|---|
| `STRAVA_CLIENT_ID` | From step 2 |
| `STRAVA_CLIENT_SECRET` | From step 2 |
| `STRAVA_REFRESH_TOKEN` | From step 2 |
| `GMAIL_USER` | your.email@gmail.com |
| `GMAIL_APP_PASSWORD` | From step 3 |
| `RECIPIENT_EMAIL` | Where to send the report |
| `ANTHROPIC_API_KEY` | From console.anthropic.com |

### 5. Test it

Trigger the report manually from GitHub:
Actions tab → "Weekly training report" → Run workflow

Or locally:
```bash
cp .env.example .env
# fill in your .env values
python main.py
```

---

## Daily nutrition logging

Run this every evening (30 seconds):

```bash
# Log protein directly
python log.py today 185

# Log what you ate — Claude estimates the protein on Sunday
python log.py today "4 eggs, 200g kipfilet, 300g kwark, protein shake, 2 boterhammen"

# Use a specific day
python log.py monday 175
python log.py friday "makreel op toast, kwark, proteinshake"

# See what you've logged this week
python log.py --show
```

The log auto-commits and pushes to GitHub so the Sunday report always reads the latest data.

---

## Customise your targets

Edit the `TARGETS` dict in `src/report.py`:

```python
TARGETS = {
    "min_sessions": 5,
    "min_run_sessions": 1,
    "min_ride_sessions": 1,
    "min_long_run_km": 10.0,
    "min_long_ride_km": 40.0,
    "min_total_run_km": 20.0,
    "protein_target_g": 180,
    "protein_target_days": 5,
}
```

---

## File structure

```
.
├── main.py                     # Entry point
├── log.py                      # Daily nutrition CLI
├── strava_auth.py              # One-time OAuth setup
├── nutrition_log.json          # Your weekly nutrition data (committed to repo)
├── requirements.txt
├── .env.example                # Template for local dev
├── src/
│   ├── strava.py               # Strava API client
│   ├── nutrition.py            # Log reader + Claude protein estimator
│   ├── report.py               # HTML report builder + targets
│   └── mailer.py               # Gmail sender
└── .github/
    └── workflows/
        └── weekly_report.yml   # Cron: every Sunday 08:00 CET
```
