import json
import os
from datetime import datetime
from anthropic import Anthropic

NUTRITION_LOG_PATH = "nutrition_log.json"
DAYS_OF_WEEK = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def load_current_week_log() -> dict:
    """Load this week's nutrition entries from nutrition_log.json."""
    week_key = _current_week_key()

    try:
        with open(NUTRITION_LOG_PATH, "r") as f:
            full_log = json.load(f)
    except FileNotFoundError:
        return {}

    return full_log.get(week_key, {})


def resolve_protein(week_log: dict) -> dict:
    """
    For each day in the log:
    - If protein is already a number, use it directly.
    - If only a food description is present, call Claude to estimate grams of protein.
    Returns: {day: {"protein": int, "food": str, "estimated": bool}}
    """
    client = Anthropic()
    resolved = {}

    for day in DAYS_OF_WEEK:
        entry = week_log.get(day)
        if not entry:
            resolved[day] = None
            continue

        protein = entry.get("protein")
        food = entry.get("food")

        if protein is not None:
            resolved[day] = {"protein": int(protein), "food": food, "estimated": False}

        elif food:
            estimated = _estimate_protein_from_food(client, food)
            resolved[day] = {"protein": estimated, "food": food, "estimated": True}

        else:
            resolved[day] = None

    return resolved


def compute_nutrition_summary(resolved: dict, target_protein: int = 180) -> dict:
    """
    Calculate weekly nutrition stats from resolved protein data.
    """
    logged_days = [v for v in resolved.values() if v is not None]
    total_days_logged = len(logged_days)

    if total_days_logged == 0:
        return {
            "days_logged": 0,
            "days_on_target": 0,
            "avg_protein": 0,
            "target_protein": target_protein,
            "daily_breakdown": resolved,
        }

    proteins = [v["protein"] for v in logged_days]
    avg_protein = round(sum(proteins) / total_days_logged)
    days_on_target = sum(1 for p in proteins if p >= target_protein)

    return {
        "days_logged": total_days_logged,
        "days_on_target": days_on_target,
        "avg_protein": avg_protein,
        "target_protein": target_protein,
        "daily_breakdown": resolved,
    }


def _estimate_protein_from_food(client: Anthropic, food_description: str) -> int:
    """
    Ask Claude to estimate total protein in grams from a natural language food description.
    """
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=200,
        system=(
            "You are a precise sports nutritionist. "
            "The user will describe what they ate in a day. "
            "Respond ONLY with a single integer representing the total estimated grams of protein. "
            "No explanation, no units, just the number. "
            "Be conservative — do not overestimate. "
            "Assume Dutch/European portion sizes."
        ),
        messages=[{"role": "user", "content": food_description}],
    )
    raw = message.content[0].text.strip()
    try:
        return int(raw)
    except ValueError:
        # Fallback: extract first number found
        import re
        nums = re.findall(r"\d+", raw)
        return int(nums[0]) if nums else 0


def _current_week_key() -> str:
    now = datetime.now()
    return now.strftime("%Y-W%W")
