#!/usr/bin/env python3
"""
Run this ONCE to get your Strava refresh token.
After that, add it to your GitHub secrets and never run this again.

Steps:
  1. Go to https://www.strava.com/settings/api
  2. Create an app (name anything, callback URL: http://localhost)
  3. Copy your Client ID and Client Secret
  4. Run: python strava_auth.py
  5. Follow the instructions printed below
"""

import os
import sys
import webbrowser
import requests
from urllib.parse import urlparse, parse_qs


def main():
    client_id = input("Enter your Strava Client ID: ").strip()
    client_secret = input("Enter your Strava Client Secret: ").strip()

    auth_url = (
        f"https://www.strava.com/oauth/authorize"
        f"?client_id={client_id}"
        f"&response_type=code"
        f"&redirect_uri=http://localhost"
        f"&approval_prompt=force"
        f"&scope=activity:read_all"
    )

    print("\n── Step 1 ──────────────────────────────────────────────────────")
    print("Opening Strava in your browser. Log in and click 'Authorize'.")
    print("You'll be redirected to a localhost URL (the page won't load — that's fine).")
    print(f"\nIf your browser doesn't open: {auth_url}\n")

    webbrowser.open(auth_url)

    print("── Step 2 ──────────────────────────────────────────────────────")
    redirect = input("Paste the full URL from your browser's address bar:\n> ").strip()

    # Extract code from URL
    parsed = urlparse(redirect)
    params = parse_qs(parsed.query)
    if "code" not in params:
        print("❌ Could not find 'code' in the URL. Try again.")
        sys.exit(1)

    code = params["code"][0]

    # Exchange for tokens
    resp = requests.post(
        "https://www.strava.com/oauth/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
        },
    )
    resp.raise_for_status()
    data = resp.json()

    print("\n── Your tokens ─────────────────────────────────────────────────")
    print(f"STRAVA_CLIENT_ID:     {client_id}")
    print(f"STRAVA_CLIENT_SECRET: {client_secret}")
    print(f"STRAVA_REFRESH_TOKEN: {data['refresh_token']}")
    print("\n→ Add all three as GitHub repository secrets (see README.md)")
    print("→ Never commit these values to your repo\n")


if __name__ == "__main__":
    main()
