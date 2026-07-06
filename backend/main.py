# -*- coding: utf-8 -*-
"""
eFootball Turnir - Backend API (FastAPI)
-----------------------------------------
Bir nechta liga (LaLiga, Premier Liga, Bundesliga, Serie A, Ligue 1) parallel
ishlaydi. Har birida sig'im bor (masalan 32 yoki 64). Telegram Mini App
frontend shu API bilan ishlaydi.

Ishga tushirish:
    pip install -r requirements.txt
    export BOT_TOKEN="..."          # BotFather bergan token (initData tekshirish uchun)
    export ADMIN_IDS="123,456"      # admin telegram ID'lari
    uvicorn main:app --host 0.0.0.0 --port 8000
"""

import hashlib
import hmac
import os
import sqlite3
from urllib.parse import parse_qsl

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

DB_PATH = os.getenv("DB_PATH", "efootball.db")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()}

app = FastAPI(title="eFootball Turnir API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# DATABASE
# ---------------------------------------------------------------------------

def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


DEFAULT_LEAGUES = [
    # key, name, capacity, color1, color2, icon
    ("laliga", "LaLiga", 32, "#ff3d54", "#3d1b7a", "⚽"),
    ("premier", "Premier Liga", 32, "#3a1c71", "#6a1b9a", "🦁"),
    ("bundesliga", "Bundesliga", 32, "#d31027", "#1a1a2e", "🦅"),
    ("seriea", "Serie A", 32, "#0f3460", "#16213e", "⭐"),
    ("ligue1", "Ligue 1", 32, "#1e3c72", "#2a5298", "🐓"),
]


def init_db() -> None:
    conn = db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS leagues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            capacity INTEGER NOT NULL DEFAULT 32,
            color1 TEXT DEFAULT '#3a1c71',
            color2 TEXT DEFAULT '#0f3460',
            icon TEXT DEFAULT '⚽',
            status TEXT NOT NULL DEFAULT 'reg',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            league_id INTEGER NOT NULL,
            telegram_id INTEGER NOT NULL,
            full_name TEXT NOT NULL,
            username TEXT,
            UNIQUE(league_id, telegram_id)
        );

        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            league_id INTEGER NOT NULL,
            round_num INTEGER NOT NULL,
            player1_id INTEGER,
            player2_id INTEGER,
            score1 INTEGER,
            score2 INTEGER,
            played INTEGER DEFAULT 0
        );
        """
    )
    for key, name, cap, c1, c2, icon in DEFAULT_LEAGUES:
        conn.execute(
            "INSERT OR IGNORE INTO leagues (key, name, capacity, color1, color2, icon) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (key, name, cap, c1, c2, icon),
        )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# TELEGRAM initData VALIDATION
# https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
# ---------------------------------------------------------------------------

def validate_init_data(init_data: str) -> dict:
    if not BOT_TOKEN:
        raise HTTPException(500, "Server BOT_TOKEN sozlanmagan")
    if not init_data:
        raise HTTPException(401, "initData yo'q")

    parsed = dict(parse_qsl(init_data, strict_parsing=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise HTTPException(401, "Noto'g'ri initData")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        raise HTTPException(401, "initData tasdiqlanmadi")

    import json
    user = json.loads(parsed.get("user", "{}"))
    return user


def get_user(init_data: str) -> dict:
    return validate_init_data(init_data)


# ---------------------------------------------------------------------------
# ROUND ROBIN + STANDINGS (bot.py bilan bir xil mantiq)
# ---------------------------------------------------------------------------

def generate_round_robin(player_ids: list) -> list:
    players = list(player_ids)
    if len(players) % 2 == 1:
        players.append(None)
    n = len(players)
    rounds = []
    for _ in range(n - 1):
        round_matches = []
        for i in range(n // 2):
            p1, p2 = players[i], players[n - 1 - i]
            if p1 is not None and p2 is not None:
                round_matches.append((p1, p2))
        rounds.append(round_matches)
        players.insert(1, players.pop())
    return rounds


def compute_standings(conn, league_id: int) -> list:
    players = {
        row["id"]: {
            "name": row["full_name"], "P": 0, "W": 0, "D": 0, "L": 0,
            "GF": 0, "GA": 0, "PTS": 0,
        }
        for row in conn.execute("SELECT * FROM players WHERE league_id=?", (league_id,))
    }
    for m in conn.execute(
        "SELECT * FROM matches WHERE league_id=? AND played=1", (league_id,)
    ):
        p1, p2, s1, s2 = m["player1_id"], m["player2_id"], m["score1"], m["score2"]
        if p1 not in players or p2 not in players:
            continue
        players[p1]["P"] += 1
        players[p2]["P"] += 1
        players[p1]["GF"] += s1
        players[p1]["GA"] += s2
        players[p2]["GF"] += s2
        players[p2]["GA"] += s1
        if s1 > s2:
            players[p1]["W"] += 1
            players[p1]["PTS"] += 3
            players[p2]["L"] += 1
        elif s1 < s2:
            players[p2]["W"] += 1
            players[p2]["PTS"] += 3
            players[p1]["L"] += 1
        else:
            players[p1]["D"] += 1
            players[p1]["PTS"] += 1
            players[p2]["D"] += 1
            players[p2]["PTS"] += 1

    table = list(players.values())
    for row in table:
        row["GD"] = row["GF"] - row["GA"]
    table.sort(key=lambda r: (-r["PTS"], -r["GD"], -r["GF"]))
    return table


# ---------------------------------------------------------------------------
# SCHEMAS
# ---------------------------------------------------------------------------

class RegisterBody(BaseModel):
    init_data: str


class ResultBody(BaseModel):
    init_data: str
    match_id: int
    score1: int
    score2: int


class AdminActionBody(BaseModel):
    init_data: str


# ---------------------------------------------------------------------------
# ENDPOINTS
# ---------------------------------------------------------------------------

@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/leagues")
def list_leagues():
    conn = db()
    leagues = conn.execute("SELECT * FROM leagues ORDER BY id").fetchall()
    result = []
    for lg in leagues:
        count = conn.execute(
            "SELECT COUNT(*) c FROM players WHERE league_id=?", (lg["id"],)
        ).fetchone()["c"]
        result.append({
            "id": lg["id"], "key": lg["key"], "name": lg["name"],
            "capacity": lg["capacity"], "count": count,
            "color1": lg["color1"], "color2": lg["color2"], "icon": lg["icon"],
            "status": lg["status"],
            "full": count >= lg["capacity"],
        })
    conn.close()
    return result


@app.get("/api/leagues/{league_id}")
def league_detail(league_id: int, init_data: str = ""):
    conn = db()
    lg = conn.execute("SELECT * FROM leagues WHERE id=?", (league_id,)).fetchone()
    if lg is None:
        conn.close()
        raise HTTPException(404, "Liga topilmadi")

    count = conn.execute(
        "SELECT COUNT(*) c FROM players WHERE league_id=?", (league_id,)
    ).fetchone()["c"]

    is_registered = False
    is_admin = False
    if init_data:
        user = get_user(init_data)
        uid = user.get("id")
        is_admin = uid in ADMIN_IDS
        row = conn.execute(
            "SELECT 1 FROM players WHERE league_id=? AND telegram_id=?", (league_id, uid)
        ).fetchone()
        is_registered = row is not None

    conn.close()
    return {
        "id": lg["id"], "key": lg["key"], "name": lg["name"],
        "capacity": lg["capacity"], "count": count,
        "color1": lg["color1"], "color2": lg["color2"], "icon": lg["icon"],
        "status": lg["status"], "full": count >= lg["capacity"],
        "is_registered": is_registered, "is_admin": is_admin,
    }


@app.post("/api/leagues/{league_id}/register")
def register(league_id: int, body: RegisterBody):
    user = get_user(body.init_data)
    conn = db()
    lg = conn.execute("SELECT * FROM leagues WHERE id=?", (league_id,)).fetchone()
    if lg is None:
        conn.close()
        raise HTTPException(404, "Liga topilmadi")
    if lg["status"] != "reg":
        conn.close()
        raise HTTPException(400, "Ro'yxatga olish yopilgan")

    count = conn.execute(
        "SELECT COUNT(*) c FROM players WHERE league_id=?", (league_id,)
    ).fetchone()["c"]
    if count >= lg["capacity"]:
        conn.close()
        raise HTTPException(400, "Liga to'lgan (TO'LIQ)")

    full_name = f'{user.get("first_name", "")} {user.get("last_name", "")}'.strip() or user.get("username", str(user.get("id")))
    try:
        conn.execute(
            "INSERT INTO players (league_id, telegram_id, full_name, username) VALUES (?, ?, ?, ?)",
            (league_id, user["id"], full_name, user.get("username")),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(400, "Siz allaqachon ro'yxatdasiz")
    conn.close()
    return {"ok": True, "message": "Ro'yxatdan muvaffaqiyatli o'tdingiz"}


@app.get("/api/leagues/{league_id}/standings")
def standings(league_id: int):
    conn = db()
    if conn.execute("SELECT 1 FROM leagues WHERE id=?", (league_id,)).fetchone() is None:
        conn.close()
        raise HTTPException(404, "Liga topilmadi")
    table = compute_standings(conn, league_id)
    conn.close()
    return table


@app.get("/api/leagues/{league_id}/fixtures")
def fixtures(league_id: int, round: int = 1):
    conn = db()
    rows = conn.execute(
        """SELECT m.id, m.round_num, m.score1, m.score2, m.played,
                  p1.full_name AS n1, p2.full_name AS n2
           FROM matches m
           JOIN players p1 ON p1.id = m.player1_id
           JOIN players p2 ON p2.id = m.player2_id
           WHERE m.league_id=? AND m.round_num=?
           ORDER BY m.id""",
        (league_id, round),
    ).fetchall()
    max_round = conn.execute(
        "SELECT COALESCE(MAX(round_num), 0) m FROM matches WHERE league_id=?", (league_id,)
    ).fetchone()["m"]
    conn.close()
    return {
        "round": round, "max_round": max_round,
        "matches": [dict(r) for r in rows],
    }


@app.post("/api/leagues/{league_id}/start")
def start_tournament(league_id: int, body: AdminActionBody):
    user = get_user(body.init_data)
    if user.get("id") not in ADMIN_IDS:
        raise HTTPException(403, "Faqat admin uchun")

    conn = db()
    lg = conn.execute("SELECT * FROM leagues WHERE id=?", (league_id,)).fetchone()
    if lg is None:
        conn.close()
        raise HTTPException(404, "Liga topilmadi")
    if lg["status"] != "reg":
        conn.close()
        raise HTTPException(400, "Bu liga allaqachon boshlangan")

    players = conn.execute(
        "SELECT id FROM players WHERE league_id=?", (league_id,)
    ).fetchall()
    player_ids = [p["id"] for p in players]
    if len(player_ids) < 2:
        conn.close()
        raise HTTPException(400, "Kamida 2 ta o'yinchi kerak")

    rounds = generate_round_robin(player_ids)
    for round_num, matches in enumerate(rounds, start=1):
        for p1, p2 in matches:
            conn.execute(
                "INSERT INTO matches (league_id, round_num, player1_id, player2_id) VALUES (?, ?, ?, ?)",
                (league_id, round_num, p1, p2),
            )
    conn.execute("UPDATE leagues SET status='started' WHERE id=?", (league_id,))
    conn.commit()
    conn.close()
    return {"ok": True, "rounds": len(rounds)}


@app.post("/api/leagues/{league_id}/result")
def enter_result(league_id: int, body: ResultBody):
    user = get_user(body.init_data)
    if user.get("id") not in ADMIN_IDS:
        raise HTTPException(403, "Faqat admin uchun")

    conn = db()
    match = conn.execute(
        "SELECT * FROM matches WHERE id=? AND league_id=?", (body.match_id, league_id)
    ).fetchone()
    if match is None:
        conn.close()
        raise HTTPException(404, "O'yin topilmadi")

    conn.execute(
        "UPDATE matches SET score1=?, score2=?, played=1 WHERE id=?",
        (body.score1, body.score2, body.match_id),
    )
    conn.commit()
    conn.close()
    return {"ok": True}

 import urllib.request
import json as _json

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


def send_telegram_message(chat_id: int, text: str, reply_markup: dict = None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    data = _json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{TELEGRAM_API}/sendMessage",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception:
        pass


@app.post("/webhook")
async def telegram_webhook(update: dict):
    message = update.get("message") or {}
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")
    if chat_id and text.startswith("/start"):
        webapp_url = os.getenv("WEBAPP_URL", "")
        if webapp_url:
            reply_markup = {
                "inline_keyboard": [[
                    {"text": "🏆 Turnirni ochish", "web_app": {"url": webapp_url}}
                ]]
            }
            send_telegram_message(
                chat_id,
                "⚽ <b>eFootball Turnir</b>ga xush kelibsiz!\n\nLiga tanlash, ro'yxatdan o'tish, jadval va reyting jadvalini ko'rish uchun quyidagi tugmani bosing 👇",
                reply_markup,
            )
    return {"ok": True}
# Static frontend fayllarni xizmat qilish (index.html shu yerdan ochiladi)
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")
