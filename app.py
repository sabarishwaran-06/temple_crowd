from flask import Flask, render_template, request, jsonify
from datetime import datetime
import os

app = Flask(__name__)

# ---------------------------------------------------
# Temple base data
# ---------------------------------------------------
TEMPLES = {
    "Somnath": {"base_footfall": 8000, "location": "Gir Somnath, Gujarat"},
    "Dwarka": {"base_footfall": 7000, "location": "Devbhoomi Dwarka, Gujarat"},
    "Ambaji": {"base_footfall": 6000, "location": "Banaskantha, Gujarat"},
    "Pavagadh": {"base_footfall": 5000, "location": "Panchmahal, Gujarat"},
}

FESTIVAL_DATES = {
    "Ambaji": ["2026-09-27", "2026-09-28", "2026-09-29", "2026-09-30"],
    "Somnath": ["2026-08-17"],
    "Dwarka": ["2026-08-15"],
    "Pavagadh": ["2026-09-27", "2026-09-28"],
}

BEST_TIME_SLOTS = [
    "6:00 AM - 8:00 AM",
    "5:00 PM - 7:00 PM"
]


def predict_crowd(temple, date_str):
    if temple not in TEMPLES:
        return None

    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None

    base = TEMPLES[temple]["base_footfall"]
    weekday = date_obj.weekday()

    is_weekend = weekday in (5, 6)
    is_festival = date_str in FESTIVAL_DATES.get(temple, [])

    multiplier = 1.0

    if is_weekend:
        multiplier += 0.4

    if is_festival:
        multiplier += 1.5

    predicted_footfall = int(base * multiplier)

    if predicted_footfall < base * 1.1:
        level = "Low"
        color = "green"
    elif predicted_footfall < base * 1.6:
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
        "crowd_level": level,
        "color": color,
        "best_time_slots": BEST_TIME_SLOTS,
    }


@app.route("/")
def index():
    return render_template("index.html", temples=list(TEMPLES.keys()))


@app.route("/predict", methods=["GET"])
def predict():
    temple = request.args.get("temple")
    date_str = request.args.get("date")

    if not temple or not date_str:
        return jsonify({"error": "temple and date are required"}), 400

    result = predict_crowd(temple, date_str)

    if result is None:
        return jsonify({"error": "Invalid temple or date"}), 400

    return jsonify(result)


@app.route("/predict_all", methods=["GET"])
def predict_all():
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
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )