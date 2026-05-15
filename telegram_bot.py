#!/usr/bin/env python3
"""
Nutrition Telegram Bot
Logt dagelijks eiwit naar nutrition_log.json op GitHub.
Stuur: ontbijt 37 · lunch 48 · snack 12 · totaal · week · reset
"""

import os
import json
import base64
import logging
from datetime import datetime, date

import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN  = os.environ["TELEGRAM_TOKEN"]
ALLOWED_USER_ID = int(os.environ["ALLOWED_USER_ID"])
GITHUB_TOKEN    = os.environ["GITHUB_TOKEN"]
GITHUB_OWNER    = os.environ["GITHUB_OWNER"]
GITHUB_REPO     = os.environ["GITHUB_REPO"]
PROTEIN_TARGET  = int(os.environ.get("PROTEIN_TARGET", "190"))

FILE_PATH   = "nutrition_log.json"
API_URL     = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{FILE_PATH}"
GH_HEADERS  = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}

DAYS_EN      = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
DAYS_DISPLAY = ["Ma","Di","Wo","Do","Vr","Za","Zo"]

MEAL_ALIASES = {
    "ontbijt":"ontbijt","breakfast":"ontbijt",
    "lunch":"lunch","middag":"lunch",
    "diner":"diner","dinner":"diner","avond":"diner",
    "snack":"snack","tussendoor":"snack",
    "shake":"shake","preworkout":"shake","pre":"shake",
    "post":"shake","postworkout":"shake","workout":"shake",
}

# ── GitHub ────────────────────────────────────────────────────────────────────

def read_log():
    resp = requests.get(API_URL, headers=GH_HEADERS, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    content = base64.b64decode(data["content"]).decode("utf-8")
    return json.loads(content), data["sha"]

def write_log(log: dict, sha: str, msg: str = "bot update"):
    content = base64.b64encode(json.dumps(log, indent=2).encode()).decode()
    resp = requests.put(
        API_URL,
        headers=GH_HEADERS,
        json={"message": msg, "content": content, "sha": sha},
        timeout=10,
    )
    resp.raise_for_status()

# ── Helpers ───────────────────────────────────────────────────────────────────

def week_key():
    return datetime.now().strftime("%Y-W%W")

def day_key():
    return DAYS_EN[date.today().weekday()]

def bar(current, target):
    pct = min(current / target, 1.0)
    filled = int(pct * 10)
    return f"{'█' * filled}{'░' * (10 - filled)} {int(pct * 100)}%"

# ── Handlers ──────────────────────────────────────────────────────────────────

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER_ID:
        return

    text = update.message.text.strip().lower()

    if text == "totaal":
        await do_totaal(update)
    elif text == "week":
        await do_week(update)
    elif text in ("reset", "wis"):
        await do_reset(update)
    elif text in ("help", "?"):
        await do_help(update)
    else:
        await do_log(update, text)


async def do_log(update, text):
    parts = text.split()
    protein = None
    meal = "overig"

    if len(parts) == 1:
        try:
            protein = int(parts[0])
        except ValueError:
            await update.message.reply_text("❓ Stuur bijv: *ontbijt 37* of gewoon *37*", parse_mode="Markdown")
            return

    elif len(parts) == 2:
        try:
            protein = int(parts[1])
            meal = MEAL_ALIASES.get(parts[0], parts[0])
        except ValueError:
            try:
                protein = int(parts[0])
                meal = MEAL_ALIASES.get(parts[1], parts[1])
            except ValueError:
                await update.message.reply_text("❓ Stuur bijv: *ontbijt 37*", parse_mode="Markdown")
                return
    else:
        await update.message.reply_text("❓ Stuur bijv: *ontbijt 37*", parse_mode="Markdown")
        return

    try:
        log, sha = read_log()
        wk = week_key()
        dk = day_key()

        if wk not in log:
            log[wk] = {}

        day = log[wk].get(dk) or {"protein": 0, "food": ""}
        cur_protein = day.get("protein") or 0
        cur_food    = day.get("food") or ""

        new_protein = cur_protein + protein
        new_food    = f"{cur_food}, {meal}:{protein}g".lstrip(", ")

        log[wk][dk] = {"protein": new_protein, "food": new_food}

        for d in DAYS_EN:
            if d not in log[wk]:
                log[wk][d] = None

        write_log(log, sha, f"bot: {dk} +{protein}g {meal}")

        remaining = max(PROTEIN_TARGET - new_protein, 0)
        msg = (
            f"✅ *{meal.capitalize()}* gelogd — {protein}g\n\n"
            f"{bar(new_protein, PROTEIN_TARGET)}\n"
            f"Vandaag: *{new_protein}g* / {PROTEIN_TARGET}g\n"
        )
        msg += "🎯 Doel gehaald!" if new_protein >= PROTEIN_TARGET else f"Nog *{remaining}g* te gaan"
        await update.message.reply_text(msg, parse_mode="Markdown")

    except Exception as e:
        logger.error(e)
        await update.message.reply_text("❌ Er ging iets mis. Probeer opnieuw.")


async def do_totaal(update):
    try:
        log, _ = read_log()
        day = log.get(week_key(), {}).get(day_key())

        if not day or not day.get("protein"):
            await update.message.reply_text("📊 Nog niets gelogd vandaag.\nStuur bijv: *ontbijt 37*", parse_mode="Markdown")
            return

        protein = day["protein"]
        food    = day.get("food", "")
        remaining = max(PROTEIN_TARGET - protein, 0)

        msg = f"📊 *Vandaag*\n\n{bar(protein, PROTEIN_TARGET)}\n*{protein}g* / {PROTEIN_TARGET}g\n"
        if food:
            msg += f"\n_{food}_\n"
        msg += "\n🎯 Doel gehaald!" if protein >= PROTEIN_TARGET else f"\nNog *{remaining}g* te gaan"
        await update.message.reply_text(msg, parse_mode="Markdown")

    except Exception as e:
        logger.error(e)
        await update.message.reply_text("❌ Er ging iets mis.")


async def do_week(update):
    try:
        log, _ = read_log()
        week = log.get(week_key(), {})

        msg = "📅 *Deze week*\n\n"
        total = 0
        logged = 0

        for i, dk in enumerate(DAYS_EN):
            day = week.get(dk)
            label = DAYS_DISPLAY[i]
            if day and day.get("protein"):
                p = day["protein"]
                total += p
                logged += 1
                icon = "✅" if p >= PROTEIN_TARGET else "⚠️"
                msg += f"{icon} {label}: *{p}g*\n"
            else:
                msg += f"⬜ {label}: —\n"

        if logged:
            msg += f"\nGemiddeld: *{round(total/logged)}g/dag*"

        await update.message.reply_text(msg, parse_mode="Markdown")

    except Exception as e:
        logger.error(e)
        await update.message.reply_text("❌ Er ging iets mis.")


async def do_reset(update):
    try:
        log, sha = read_log()
        wk = week_key()
        dk = day_key()
        if wk in log:
            log[wk][dk] = None
            write_log(log, sha, f"bot: reset {dk}")
        await update.message.reply_text("🔄 Vandaag gewist. Begin opnieuw!")
    except Exception as e:
        logger.error(e)
        await update.message.reply_text("❌ Er ging iets mis.")


async def do_help(update):
    msg = (
        "🤖 *Nutrition Bot*\n\n"
        "*Loggen:*\n"
        "ontbijt 37\n"
        "lunch 48\n"
        "snack 12\n"
        "diner 44\n"
        "shake 44\n"
        "37 _(alleen getal = overig)_\n\n"
        "*Overzicht:*\n"
        "totaal — vandaag\n"
        "week — hele week\n\n"
        "*Overig:*\n"
        "reset — wis vandaag\n"
        "help — dit menu"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


# ── Start ─────────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    logger.info("Bot gestart")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
