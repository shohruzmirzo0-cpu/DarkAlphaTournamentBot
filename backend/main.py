from datetime import datetime
from flask import Flask, request
from flask_cors import CORS
import json
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
import os

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return {"status": "working"}

@app.route("/users", methods=["GET"])
def get_users():
    try:
        with open("users.json", "r", encoding="utf-8") as f:
            users = json.load(f)
    except:
        users = []
    return users

@app.route("/matches", methods=["GET"])
def get_matches():
    try:
        with open("matches.json", "r", encoding="utf-8") as f:
            matches = json.load(f)
    except:
        matches = []
    return matches

@app.route("/register", methods=["POST"])
def register():
    data = request.json

    try:
        with open("users.json", "r", encoding="utf-8") as f:
            users = json.load(f)
    except:
        users = []

    for user in users:
        if user["username"] == data["username"]:
            return {
                "success": False,
                "message": "Siz allaqachon ro'yxatdan o'tgansiz"
            }

    new_user = {
        "username": data["username"],
        "league": data["league"],
        "club": data.get("club"),
        "points": 0,
        "goals": 0,
        "wins": 0,
        "draws": 0,
        "losses": 0,
        "titles": []
    }

    users.append(new_user)

    with open("users.json", "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

    return {"success": True}

@app.route("/submit-result", methods=["POST"])
def submit_result():
    data = request.json

    try:
        with open("matches.json", "r", encoding="utf-8") as f:
            matches = json.load(f)
    except:
        matches = []

    for match in matches:
        if match["id"] == data["matchId"]:
            match["homeGoals"] = data["homeGoals"]
            match["awayGoals"] = data["awayGoals"]
            match["submittedBy"] = data["username"]
            match["status"] = "waiting"
            match["submittedAt"] = datetime.now().isoformat()
            break

    with open("matches.json", "w", encoding="utf-8") as f:
        json.dump(matches, f, ensure_ascii=False, indent=4)

    return {"success": True}

@app.route("/confirm-result", methods=["POST"])
def confirm_result():
    data = request.json

    try:
        with open("matches.json", "r", encoding="utf-8") as f:
            matches = json.load(f)
    except:
        matches = []

    try:
        with open("users.json", "r", encoding="utf-8") as f:
            users = json.load(f)
    except:
        users = []

    for match in matches:
        if match["id"] == data["matchId"]:

            match["confirmedBy"] = data["username"]
            match["status"] = "completed"

            home_goals = match["homeGoals"]
            away_goals = match["awayGoals"]

            for user in users:
                if user["username"] == match["homeUser"]:
                    user["goals"] += home_goals
                if user["username"] == match["awayUser"]:
                    user["goals"] += away_goals

            if home_goals > away_goals:
                for user in users:
                    if user["username"] == match["homeUser"]:
                        user["points"] += 3
                        user["wins"] += 1
                    elif user["username"] == match["awayUser"]:
                        user["losses"] += 1

            elif away_goals > home_goals:
                for user in users:
                    if user["username"] == match["awayUser"]:
                        user["points"] += 3
                        user["wins"] += 1
                    elif user["username"] == match["homeUser"]:
                        user["losses"] += 1

            else:
                for user in users:
                    if user["username"] in [match["homeUser"], match["awayUser"]]:
                        user["points"] += 1
                        user["draws"] += 1

            break

    with open("matches.json", "w", encoding="utf-8") as f:
        json.dump(matches, f, ensure_ascii=False, indent=4)

    with open("users.json", "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

    return {"success": True}

@app.route("/complain-result", methods=["POST"])
def complain_result():
    data = request.json

    try:
        with open("matches.json", "r", encoding="utf-8") as f:
            matches = json.load(f)
    except:
        matches = []

    for match in matches:
        if match["id"] == data["matchId"]:
            match["status"] = "disputed"
            match["complainedBy"] = data["username"]
            break

    with open("matches.json", "w", encoding="utf-8") as f:
        json.dump(matches, f, ensure_ascii=False, indent=4)

    return {"success": True}

@app.route("/auto-confirm")
def auto_confirm():
    try:
        with open("matches.json", "r", encoding="utf-8") as f:
            matches = json.load(f)
    except:
        matches = []

    try:
        with open("users.json", "r", encoding="utf-8") as f:
            users = json.load(f)
    except:
        users = []

    updated = 0

    for match in matches:
        if match["status"] == "waiting":

            match["status"] = "completed"
            match["confirmedBy"] = "AUTO"

            home_goals = match["homeGoals"]
            away_goals = match["awayGoals"]

            for user in users:
                if user["username"] == match["homeUser"]:
                    user["goals"] += home_goals
                if user["username"] == match["awayUser"]:
                    user["goals"] += away_goals

            if home_goals > away_goals:
                for user in users:
                    if user["username"] == match["homeUser"]:
                        user["points"] += 3
                        user["wins"] += 1
                    elif user["username"] == match["awayUser"]:
                        user["losses"] += 1

            elif away_goals > home_goals:
                for user in users:
                    if user["username"] == match["awayUser"]:
                        user["points"] += 3
                        user["wins"] += 1
                    elif user["username"] == match["homeUser"]:
                        user["losses"] += 1

            else:
                for user in users:
                    if user["username"] in [match["homeUser"], match["awayUser"]]:
                        user["points"] += 1
                        user["draws"] += 1

            updated += 1

    with open("matches.json", "w", encoding="utf-8") as f:
        json.dump(matches, f, ensure_ascii=False, indent=4)

    with open("users.json", "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

    return {
        "success": True,
        "autoConfirmed": updated
    }

tashkent = pytz.timezone("Asia/Tashkent")

scheduler = BackgroundScheduler(timezone=tashkent)

scheduler.add_job(
    func=auto_confirm,
    trigger="cron",
    hour=0,
    minute=0
)

scheduler.start()

@app.route("/generate-fixtures")
def generate_fixtures():
    try:
        with open("users.json", "r", encoding="utf-8") as f:
            users = json.load(f)
    except:
        return {
            "success": False,
            "message": "Ishtirokchilar topilmadi"
        }

    players = [user["username"] for user in users]

    if len(players) != 20:
        return {
            "success": False,
            "message": f"20 ta ishtirokchi kerak. Hozir {len(players)} ta."
        }

    fixtures = []
    teams = players[:]
    match_id = 1

    for round_num in range(19):
        for i in range(10):
            home = teams[i]
            away = teams[-(i + 1)]

            fixtures.append({
                "id": match_id,
                "round": round_num + 1,
                "homeUser": home,
                "awayUser": away,
                "homeGoals": None,
                "awayGoals": None,
                "status": "pending"
            })

            match_id += 1

        teams = [teams[0]] + [teams[-1]] + teams[1:-1]

    first_half = fixtures[:]

    for match in first_half:
        fixtures.append({
            "id": match_id,
            "round": match["round"] + 19,
            "homeUser": match["awayUser"],
            "awayUser": match["homeUser"],
            "homeGoals": None,
            "awayGoals": None,
            "status": "pending"
        })

        match_id += 1

    with open("matches.json", "w", encoding="utf-8") as f:
        json.dump(fixtures, f, ensure_ascii=False, indent=4)

    return {
        "success": True,
        "matches": len(fixtures)
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False
             )
