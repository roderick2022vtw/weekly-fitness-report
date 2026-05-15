open .envimport os
import sys
from dotenv import load_dotenv

load_dotenv()

from src.strava import get_access_token, get_week_activities, summarise_activities
from src.nutrition import load_current_week_log, resolve_protein, compute_nutrition_summary
from src.report import build_report
from src.mailer import send_report


def main():
    print("🚴 Weekly fitness report starting...\n")

    # ── 1. Strava ──────────────────────────────────────────────────────────
    print("Fetching Strava activities...")
    token = get_access_token(
        client_id=os.environ["STRAVA_CLIENT_ID"],
        client_secret=os.environ["STRAVA_CLIENT_SECRET"],
        refresh_token=os.environ["STRAVA_REFRESH_TOKEN"],
    )
    activities = get_week_activities(token)
    strava_summary = summarise_activities(activities)
    print(f"  Found {len(activities)} activities this week")

    # ── 2. Nutrition ───────────────────────────────────────────────────────
    print("\nProcessing nutrition log...")
    week_log = load_current_week_log()
    resolved = resolve_protein(week_log)
    nutrition_summary = compute_nutrition_summary(
        resolved,
        target_protein=int(os.environ.get("PROTEIN_TARGET", "180")),
    )
    print(f"  Logged days: {nutrition_summary['days_logged']}")
    print(f"  Days on target: {nutrition_summary['days_on_target']}")

    # ── 3. Build report ────────────────────────────────────────────────────
    print("\nBuilding HTML report...")
    html = build_report(strava_summary, nutrition_summary)

    # ── 4. Send ────────────────────────────────────────────────────────────
    print("\nSending email...")
    send_report(
        html_body=html,
        gmail_user=os.environ["GMAIL_USER"],
        gmail_app_password=os.environ["GMAIL_APP_PASSWORD"],
        recipient=os.environ["RECIPIENT_EMAIL"],
    )

    print("\n✅ Done.")


if __name__ == "__main__":
    main()
