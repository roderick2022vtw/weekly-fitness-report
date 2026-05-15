from datetime import datetime, timedelta


# ── Weekly targets (edit these) ────────────────────────────────────────────
TARGETS = {
    "min_sessions": 5,
    "min_run_sessions": 1,
    "min_ride_sessions": 1,
    "min_long_run_km": 10.0,    # counts as a long run
    "min_long_ride_km": 40.0,   # counts as a meaningful ride
    "min_total_run_km": 20.0,
    "protein_target_g": 180,
    "protein_target_days": 5,   # days per week hitting the target
}


def build_report(strava_summary: dict, nutrition_summary: dict) -> str:
    """
    Assemble a full HTML email report from the two summaries.
    Returns a complete HTML string ready to send.
    """
    week_label = _week_label()
    checks = _evaluate_targets(strava_summary, nutrition_summary)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Weekly training report — {week_label}</title>
<style>
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #f4f4f5;
    margin: 0; padding: 20px;
    color: #18181b;
  }}
  .container {{
    max-width: 600px;
    margin: 0 auto;
    background: #ffffff;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  }}
  .header {{
    background: #18181b;
    color: #ffffff;
    padding: 28px 32px;
  }}
  .header h1 {{
    margin: 0 0 4px 0;
    font-size: 22px;
    font-weight: 600;
    letter-spacing: -0.3px;
  }}
  .header p {{
    margin: 0;
    color: #a1a1aa;
    font-size: 14px;
  }}
  .section {{
    padding: 24px 32px;
    border-bottom: 1px solid #f0f0f0;
  }}
  .section:last-child {{ border-bottom: none; }}
  .section-title {{
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: #71717a;
    margin: 0 0 16px 0;
  }}
  .stat-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 12px;
    margin-bottom: 20px;
  }}
  .stat {{
    background: #fafafa;
    border: 1px solid #e4e4e7;
    border-radius: 8px;
    padding: 12px 14px;
  }}
  .stat-value {{
    font-size: 22px;
    font-weight: 600;
    line-height: 1;
    margin-bottom: 4px;
  }}
  .stat-label {{
    font-size: 11px;
    color: #71717a;
  }}
  .target-list {{
    list-style: none;
    margin: 0; padding: 0;
  }}
  .target-list li {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 0;
    font-size: 14px;
    border-bottom: 1px solid #f4f4f5;
  }}
  .target-list li:last-child {{ border-bottom: none; }}
  .badge {{
    width: 22px; height: 22px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 12px;
    flex-shrink: 0;
  }}
  .badge.pass {{ background: #dcfce7; color: #16a34a; }}
  .badge.warn {{ background: #fef9c3; color: #ca8a04; }}
  .badge.fail {{ background: #fee2e2; color: #dc2626; }}
  .activity-list {{
    list-style: none;
    margin: 0; padding: 0;
  }}
  .activity-list li {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 9px 0;
    font-size: 14px;
    border-bottom: 1px solid #f4f4f5;
  }}
  .activity-list li:last-child {{ border-bottom: none; }}
  .activity-type {{ color: #71717a; font-size: 12px; }}
  .protein-bar-wrap {{
    background: #f4f4f5;
    border-radius: 6px;
    height: 8px;
    overflow: hidden;
    margin-top: 4px;
  }}
  .protein-bar {{
    height: 100%;
    border-radius: 6px;
    background: #18181b;
    transition: width 0.3s;
  }}
  .protein-bar.over {{ background: #16a34a; }}
  .protein-bar.under {{ background: #f59e0b; }}
  .day-row {{
    margin-bottom: 10px;
  }}
  .day-row-header {{
    display: flex;
    justify-content: space-between;
    font-size: 13px;
    margin-bottom: 3px;
  }}
  .day-name {{ font-weight: 500; text-transform: capitalize; }}
  .day-grams {{ color: #71717a; }}
  .no-data {{ color: #a1a1aa; font-style: italic; font-size: 13px; }}
  .focus-list {{
    list-style: none;
    margin: 0; padding: 0;
  }}
  .focus-list li {{
    padding: 7px 0 7px 20px;
    font-size: 14px;
    position: relative;
    border-bottom: 1px solid #f4f4f5;
  }}
  .focus-list li:last-child {{ border-bottom: none; }}
  .focus-list li::before {{
    content: '→';
    position: absolute;
    left: 0;
    color: #71717a;
  }}
  .footer {{
    padding: 20px 32px;
    background: #fafafa;
    font-size: 12px;
    color: #a1a1aa;
    text-align: center;
  }}
</style>
</head>
<body>
<div class="container">

  <div class="header">
    <h1>Weekly training report</h1>
    <p>{week_label}</p>
  </div>

  <!-- Overview stats -->
  <div class="section">
    <p class="section-title">This week at a glance</p>
    <div class="stat-grid">
      <div class="stat">
        <div class="stat-value">{strava_summary['total_sessions']}</div>
        <div class="stat-label">sessions</div>
      </div>
      <div class="stat">
        <div class="stat-value">{strava_summary['total_run_km']} km</div>
        <div class="stat-label">total run</div>
      </div>
      <div class="stat">
        <div class="stat-value">{strava_summary['total_ride_km']} km</div>
        <div class="stat-label">total ride</div>
      </div>
    </div>
    {_render_activity_list(strava_summary)}
  </div>

  <!-- Target check -->
  <div class="section">
    <p class="section-title">Weekly targets</p>
    <ul class="target-list">
      {_render_targets(checks)}
    </ul>
  </div>

  <!-- Nutrition -->
  <div class="section">
    <p class="section-title">Nutrition — protein</p>
    {_render_nutrition(nutrition_summary)}
  </div>

  <!-- Focus next week -->
  <div class="section">
    <p class="section-title">Focus for next week</p>
    <ul class="focus-list">
      {_render_focus(checks, strava_summary, nutrition_summary)}
    </ul>
  </div>

  <div class="footer">
    Auto-generated by your training bot · Reply to this email to update any data
  </div>

</div>
</body>
</html>"""
    return html


# ── Private helpers ─────────────────────────────────────────────────────────

def _week_label() -> str:
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return f"Week {today.strftime('%W')} · {monday.strftime('%d %b')} – {sunday.strftime('%d %b %Y')}"


def _evaluate_targets(strava: dict, nutrition: dict) -> list[dict]:
    T = TARGETS
    checks = []

    # Session count
    s = strava["total_sessions"]
    checks.append({
        "label": f"Total sessions: {s} / {T['min_sessions']}",
        "status": "pass" if s >= T["min_sessions"] else "warn" if s >= T["min_sessions"] - 1 else "fail",
    })

    # Runs
    runs = len(strava["runs"])
    checks.append({
        "label": f"Run sessions: {runs} (target ≥ {T['min_run_sessions']})",
        "status": "pass" if runs >= T["min_run_sessions"] else "fail",
    })

    # Rides
    rides = len(strava["rides"])
    checks.append({
        "label": f"Ride sessions: {rides} (target ≥ {T['min_ride_sessions']})",
        "status": "pass" if rides >= T["min_ride_sessions"] else "fail",
    })

    # Long run
    longest_run = strava["longest_run_km"]
    checks.append({
        "label": f"Long run: {longest_run} km (target ≥ {T['min_long_run_km']} km)",
        "status": "pass" if longest_run >= T["min_long_run_km"] else "warn",
    })

    # Total run km
    total_run = strava["total_run_km"]
    checks.append({
        "label": f"Total running volume: {total_run} km (target ≥ {T['min_total_run_km']} km)",
        "status": "pass" if total_run >= T["min_total_run_km"] else "warn",
    })

    # Swims
    swims = len(strava.get("swims", []))
    checks.append({
        "label": f"Swim sessions: {swims} (building toward triathlon base)",
        "status": "pass" if swims >= 1 else "warn",
    })

    # Protein days
    pdays = nutrition.get("days_on_target", 0)
    checks.append({
        "label": f"Protein target days: {pdays} / {T['protein_target_days']} days ≥ {T['protein_target_g']}g",
        "status": "pass" if pdays >= T["protein_target_days"] else "warn" if pdays >= 3 else "fail",
    })

    return checks


def _render_targets(checks: list[dict]) -> str:
    icons = {"pass": "✓", "warn": "~", "fail": "✗"}
    items = []
    for c in checks:
        icon = icons[c["status"]]
        items.append(
            f'<li><span class="badge {c["status"]}">{icon}</span> {c["label"]}</li>'
        )
    return "\n".join(items)


def _render_activity_list(summary: dict) -> str:
    all_acts = summary["runs"] + summary["rides"] + summary["swims"] + summary["other"]
    if not all_acts:
        return '<p class="no-data">No activities logged this week.</p>'

    all_acts_sorted = sorted(all_acts, key=lambda a: a.get("date", ""))
    items = []
    for act in all_acts_sorted:
        pace_or_speed = act.get("pace_min_per_km") or (
            f"{act.get('avg_speed_kmh', '')} km/h" if act.get("avg_speed_kmh") else ""
        )
        hr_str = f" · {int(act['avg_hr'])} bpm avg" if act.get("avg_hr") else ""
        meta = f"{act['distance_km']} km · {act['duration_min']} min"
        if pace_or_speed:
            meta += f" · {pace_or_speed}"
        meta += hr_str

        items.append(
            f'<li>'
            f'<span><strong>{act["name"]}</strong><br>'
            f'<span class="activity-type">{act["date"]}</span></span>'
            f'<span style="text-align:right;font-size:13px;color:#52525b">{meta}</span>'
            f'</li>'
        )

    return f'<ul class="activity-list">{"".join(items)}</ul>'


def _render_nutrition(nutrition: dict) -> str:
    if nutrition["days_logged"] == 0:
        return '<p class="no-data">No nutrition data logged this week. Use <code>python log.py</code> to track.</p>'

    target = nutrition["target_protein"]
    breakdown = nutrition["daily_breakdown"]
    rows = []

    for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
        entry = breakdown.get(day)
        if not entry:
            rows.append(
                f'<div class="day-row">'
                f'<div class="day-row-header">'
                f'<span class="day-name">{day}</span>'
                f'<span class="no-data">not logged</span>'
                f'</div></div>'
            )
            continue

        protein = entry["protein"]
        pct = min(int((protein / target) * 100), 100)
        bar_class = "over" if protein >= target else "under"
        estimated_note = " (est.)" if entry.get("estimated") else ""

        rows.append(
            f'<div class="day-row">'
            f'<div class="day-row-header">'
            f'<span class="day-name">{day}</span>'
            f'<span class="day-grams">{protein}g{estimated_note}</span>'
            f'</div>'
            f'<div class="protein-bar-wrap">'
            f'<div class="protein-bar {bar_class}" style="width:{pct}%"></div>'
            f'</div>'
            f'</div>'
        )

    summary_line = (
        f'<p style="font-size:13px;color:#52525b;margin:0 0 16px 0;">'
        f'Average: <strong>{nutrition["avg_protein"]}g/day</strong> · '
        f'On target: <strong>{nutrition["days_on_target"]}/{nutrition["days_logged"]}</strong> days logged'
        f'</p>'
    )

    return summary_line + "\n".join(rows)


def _render_focus(checks: list, strava: dict, nutrition: dict) -> str:
    focuses = []

    failed = [c for c in checks if c["status"] in ("fail", "warn")]
    for f in failed[:3]:
        focuses.append(f'<li>{f["label"].split(":")[0]} — improve this</li>')

    if len(strava.get("swims", [])) == 0:
        focuses.append("<li>Book one swim session at Marnixbad or Zuiderbad</li>")

    if nutrition.get("avg_protein", 0) < nutrition.get("target_protein", 180):
        gap = nutrition["target_protein"] - nutrition.get("avg_protein", 0)
        focuses.append(f"<li>Close the {gap}g/day protein gap — add makreel or kwark at dinner</li>")

    if not focuses:
        focuses.append("<li>Strong week — maintain the consistency</li>")
        focuses.append("<li>Consider adding one extra quality session if energy allows</li>")

    return "\n".join(focuses)
