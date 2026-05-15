#!/usr/bin/env python3
"""
Nutrition logger — run this to log your daily protein.

Usage:
  python log.py today 185
  python log.py monday 185
  python log.py today "4 eggs, 200g kipfilet, 300g kwark, protein shake"
  python log.py --show

The entry is saved to nutrition_log.json and auto-committed + pushed to GitHub.
"""

import json
import sys
import subprocess
from datetime import datetime, date

NUTRITION_LOG_PATH = "nutrition_log.json"
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def main():
    if len(sys.argv) < 2:
        _print_help()
        return

    if sys.argv[1] == "--show":
        _show_week()
        return

    if len(sys.argv) < 3:
        _print_help()
        return

    day_input = sys.argv[1].lower().strip()
    entry = sys.argv[2].strip()

    # Resolve day name
    if day_input == "today":
        day = date.today().strftime("%A").lower()
    elif day_input in DAYS:
        day = day_input
    else:
        print(f"❌ Unknown day: '{day_input}'. Use: today, monday, tuesday, etc.")
        sys.exit(1)

    # Load existing log
    full_log = _load_log()
    week_key = _current_week_key()
    if week_key not in full_log:
        full_log[week_key] = {}

    # Parse entry: number = direct protein, text = food description
    try:
        protein_grams = int(entry)
        full_log[week_key][day] = {"protein": protein_grams, "food": None}
        print(f"✅ {day.capitalize()}: {protein_grams}g protein logged")
    except ValueError:
        full_log[week_key][day] = {"protein": None, "food": entry}
        print(f"✅ {day.capitalize()}: food logged → \"{entry}\"")
        print("   Protein will be estimated by Claude when the report runs on Sunday.")

    # Save
    _save_log(full_log)
    print(f"   Saved to {NUTRITION_LOG_PATH}")

    # Auto git commit + push
    _git_push(day)


def _show_week():
    """Print this week's logged nutrition to the terminal."""
    full_log = _load_log()
    week_key = _current_week_key()
    week = full_log.get(week_key, {})

    print(f"\n📋 Nutrition log — {week_key}\n")
    if not week:
        print("  Nothing logged yet this week.")
        print(f"  Run: python log.py today <protein_grams_or_food_description>\n")
        return

    for day in DAYS:
        entry = week.get(day)
        if not entry:
            print(f"  {day.capitalize():<12} — not logged")
        elif entry.get("protein") is not None:
            print(f"  {day.capitalize():<12} {entry['protein']}g protein")
        else:
            print(f"  {day.capitalize():<12} \"{entry['food']}\" (protein TBD)")
    print()


def _load_log() -> dict:
    try:
        with open(NUTRITION_LOG_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def _save_log(log: dict):
    with open(NUTRITION_LOG_PATH, "w") as f:
        json.dump(log, f, indent=2)


def _git_push(day: str):
    try:
        subprocess.run(["git", "add", NUTRITION_LOG_PATH], check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", f"nutrition: log {day} {_current_week_key()}"],
            check=True, capture_output=True,
        )
        subprocess.run(["git", "push"], check=True, capture_output=True)
        print("   Pushed to GitHub ✅")
    except subprocess.CalledProcessError:
        print("   ⚠️  Could not auto-push to GitHub. Run 'git push' manually.")


def _current_week_key() -> str:
    return datetime.now().strftime("%Y-W%W")


def _print_help():
    print(__doc__)


if __name__ == "__main__":
    main()
