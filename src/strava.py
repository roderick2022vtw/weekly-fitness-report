import requests
from datetime import datetime, timedelta, timezone


def get_access_token(client_id: str, client_secret: str, refresh_token: str) -> str:
    resp = requests.post(
        "https://www.strava.com/oauth/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def get_week_activities(access_token: str) -> list[dict]:
    """
    Fetch activities from Monday through Sunday of the current week.
    Runs Sunday morning, so we capture Mon–Sat completed + any early Sunday session.
    """
    today = datetime.now(timezone.utc)
    monday = today - timedelta(days=today.weekday())
    monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)

    resp = requests.get(
        "https://www.strava.com/api/v3/athlete/activities",
        headers={"Authorization": f"Bearer {access_token}"},
        params={
            "after": int(monday.timestamp()),
            "before": int(today.timestamp()),
            "per_page": 50,
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def summarise_activities(activities: list[dict]) -> dict:
    """
    Distil raw Strava activities into the metrics the report needs.
    Returns a structured summary dict.
    """
    summary = {
        "total_sessions": len(activities),
        "runs": [],
        "rides": [],
        "swims": [],
        "other": [],
        "total_run_km": 0.0,
        "total_ride_km": 0.0,
        "total_run_minutes": 0,
        "total_ride_minutes": 0,
        "longest_run_km": 0.0,
        "longest_ride_km": 0.0,
        "avg_run_pace": None,
        "avg_ride_speed": None,
    }

    run_paces = []

    for act in activities:
        sport = act.get("sport_type", act.get("type", "Other"))
        distance_km = round(act.get("distance", 0) / 1000, 1)
        duration_min = round(act.get("moving_time", 0) / 60)
        avg_hr = act.get("average_heartrate")
        name = act.get("name", "Activity")

        entry = {
            "name": name,
            "distance_km": distance_km,
            "duration_min": duration_min,
            "avg_hr": avg_hr,
            "date": act.get("start_date_local", "")[:10],
        }

        if sport in ("Run", "TrailRun", "VirtualRun"):
            if distance_km > 0 and duration_min > 0:
                pace_sec_per_km = (duration_min * 60) / distance_km
                entry["pace_min_per_km"] = _format_pace(pace_sec_per_km)
                run_paces.append(pace_sec_per_km)
            summary["runs"].append(entry)
            summary["total_run_km"] += distance_km
            summary["total_run_minutes"] += duration_min
            summary["longest_run_km"] = max(summary["longest_run_km"], distance_km)

        elif sport in ("Ride", "VirtualRide", "EBikeRide", "GravelRide"):
            if duration_min > 0:
                entry["avg_speed_kmh"] = round((distance_km / duration_min) * 60, 1)
            summary["rides"].append(entry)
            summary["total_ride_km"] += distance_km
            summary["total_ride_minutes"] += duration_min
            summary["longest_ride_km"] = max(summary["longest_ride_km"], distance_km)

        elif sport == "Swim":
            summary["swims"].append(entry)

        else:
            summary["other"].append(entry)

    if run_paces:
        avg_pace = sum(run_paces) / len(run_paces)
        summary["avg_run_pace"] = _format_pace(avg_pace)

    summary["total_run_km"] = round(summary["total_run_km"], 1)
    summary["total_ride_km"] = round(summary["total_ride_km"], 1)

    return summary


def _format_pace(seconds_per_km: float) -> str:
    minutes = int(seconds_per_km // 60)
    seconds = int(seconds_per_km % 60)
    return f"{minutes}:{seconds:02d} /km"
