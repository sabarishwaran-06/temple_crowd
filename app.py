from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import os

app = Flask(__name__)
app.secret_key = "temple_crowd_secret_key_2026"  # needed for login sessions

from datetime import datetime

# ---------------------------------------------------
# Demo login credentials (hardcoded for mini-project scope)
# ---------------------------------------------------
USERS = {
    "admin": "admin123",
    "student": "student123",
}

# ---------------------------------------------------
# Temple base data (synthetic — replace with real data if available)
# base_footfall = normal day footfall, capacity = max devotees site can safely hold
# ---------------------------------------------------
TEMPLES = {
    "Somnath": {"base_footfall": 8000, "capacity": 15000, "location": "Gir Somnath, Gujarat"},
    "Dwarka": {"base_footfall": 7000, "capacity": 13000, "location": "Devbhoomi Dwarka, Gujarat"},
    "Ambaji": {"base_footfall": 6000, "capacity": 20000, "location": "Banaskantha, Gujarat"},
    "Pavagadh": {"base_footfall": 5000, "capacity": 10000, "location": "Panchmahal, Gujarat"},
}

# Festival dates that cause huge crowd spikes (sample — extend as needed)
FESTIVAL_DATES = {
    "Ambaji": ["2026-09-27", "2026-09-28", "2026-09-29", "2026-09-30"],  # Navratri
    "Somnath": ["2026-08-17"],   # Shravan Somvar
    "Dwarka": ["2026-08-15"],    # Janmashtami
    "Pavagadh": ["2026-09-27", "2026-09-28"],  # Navratri
}

BEST_TIME_SLOTS = ["6:00 AM - 8:00 AM", "5:00 PM - 7:00 PM"]


# ---------------------------------------------------
# Simple rule-based crowd prediction logic
# (mini-project scope — can be swapped with an ML model later)
# ---------------------------------------------------
def predict_crowd(temple, date_str):
    if temple not in TEMPLES:
        return None

    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None

    base = TEMPLES[temple]["base_footfall"]
    weekday = date_obj.weekday()  # Monday=0 ... Sunday=6
    is_weekend = weekday in (5, 6)
    is_festival = date_str in FESTIVAL_DATES.get(temple, [])

    multiplier = 1.0
    if is_weekend:
        multiplier += 0.4
    if is_festival:
        multiplier += 1.5

    predicted_footfall = int(base * multiplier)
    capacity = TEMPLES[temple]["capacity"]

    # crowd percentage = how full the site is vs its safe capacity
    crowd_percentage = round(min((predicted_footfall / capacity) * 100, 100), 1)

    # crowd level thresholds (based on percentage of capacity)
    if crowd_percentage < 40:
        level = "Low"
        color = "green"
    elif crowd_percentage < 75:
        level = "Medium"
        color = "yellow"
    else:
        level = "High"
        color = "red"

    return {
        "temple": temple,
        "location": TEMPLES[temple]["location"],
        "date": date_str,
        "is_festival": is_festival,
        "is_weekend": is_weekend,
        "predicted_footfall": predicted_footfall,
        "capacity": capacity,
        "crowd_percentage": crowd_percentage,
        "crowd_level": level,
        "color": color,
        "best_time_slots": BEST_TIME_SLOTS,
    }


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username in USERS and USERS[username] == password:
            session["user"] = username
            return redirect(url_for("index"))
        else:
            error = "Invalid username or password"
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


@app.route("/")
def index():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("index.html", temples=list(TEMPLES.keys()), user=session["user"])


@app.route("/predict", methods=["GET"])
def predict():
    if "user" not in session:
        return jsonify({"error": "unauthorized"}), 401
    temple = request.args.get("temple")
    date_str = request.args.get("date")

    if not temple or not date_str:
        return jsonify({"error": "temple and date are required"}), 400

    result = predict_crowd(temple, date_str)
    if result is None:
        return jsonify({"error": "invalid temple name or date format (use YYYY-MM-DD)"}), 400

    return jsonify(result)


@app.route("/predict_all", methods=["GET"])
def predict_all():
    if "user" not in session:
        return jsonify({"error": "unauthorized"}), 401
    date_str = request.args.get("date")
    if not date_str:
        return jsonify({"error": "date is required"}), 400

    results = []
    for temple in TEMPLES:
        r = predict_crowd(temple, date_str)
        if r:
            results.append(r)

    return jsonify(results)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
