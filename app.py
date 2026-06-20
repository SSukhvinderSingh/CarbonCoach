import csv
import io
import os
import re
from datetime import date, datetime, timedelta, timezone

from dotenv import load_dotenv
from flask import Flask, jsonify, request, render_template, Response

from footprint_calculator import calculate, benchmark
from recommendation_engine import recommend
from conversational_insight_generator import extract_activities, generate_reply
from progress_tracker import (
    create_session,
    get_all_sessions,
    save_activity,
    save_message,
    get_recent_messages,
    get_activities_since,
    get_today_activities,
    get_all_activities_csv,
    clear_session_data,
)

load_dotenv()

app = Flask(__name__)


def _get_guest():
    guest = request.headers.get("X-Guest-Name", "")
    return guest.strip() or "default"


def _get_today_activities(guest):
    return get_today_activities(guest)


def _get_window_activities(guest):
    window_start = datetime.now(timezone.utc).date() - timedelta(days=7)
    return get_activities_since(guest, window_start)


def _compute_grounding(guest):
    today_acts = _get_today_activities(guest)
    window_acts = _get_window_activities(guest)
    rec = recommend(window_acts, today_acts)
    bench = benchmark(rec["today_total_kg"])
    return {**rec, "benchmark": bench}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    guest_name = data.get("guest_name", "").strip()
    if not guest_name:
        return jsonify({"error": "guest_name is required"}), 400
    create_session(guest_name)
    return jsonify({"ok": True, "guest_name": guest_name})


@app.route("/api/sessions", methods=["GET"])
def sessions():
    all_sessions = get_all_sessions()
    return jsonify({"sessions": [s["guest_name"] for s in all_sessions]})


@app.route("/api/chat", methods=["POST"])
def chat():
    guest = _get_guest()
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    location = data.get("location")

    if not message:
        return jsonify({"error": "message is required"}), 400

    save_message(guest, "user", message)

    activities = extract_activities(message)

    lat = None
    lng = None
    if location and isinstance(location, dict):
        lat = location.get("lat")
        lng = location.get("lng")

    logged_activities = []
    for act in activities:
        result = calculate(act)
        logged_activities.append({
            "category": act["category"],
            "activity_type": act["activity_type"],
            "quantity": act["quantity"],
            "co2_kg": result["co2_kg"],
            "latitude": lat,
            "longitude": lng,
        })
        save_activity(
            guest,
            act["category"],
            act["activity_type"],
            act["quantity"],
            result["co2_kg"],
            lat,
            lng,
        )

    grounding = _compute_grounding(guest)
    history = get_recent_messages(guest, 5)
    reply = generate_reply(message, grounding, history)

    save_message(guest, "assistant", reply)

    return jsonify({
        "reply": reply,
        "logged_activities": logged_activities,
        "grounding": grounding,
    })


@app.route("/api/summary", methods=["GET"])
def summary():
    guest = _get_guest()
    grounding = _compute_grounding(guest)
    return jsonify(grounding)


@app.route("/api/activities", methods=["GET"])
def activities():
    guest = _get_guest()
    today_acts = _get_today_activities(guest)
    return jsonify({"activities": today_acts})


@app.route("/api/export", methods=["GET"])
def export():
    guest = _get_guest()
    rows = get_all_activities_csv(guest)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["category", "activity_type", "quantity", "co2_kg", "logged_at", "latitude", "longitude"])
    for r in rows:
        writer.writerow([r["category"], r["activity_type"], r["quantity"], r["co2_kg"], r["logged_at"], r["latitude"] or "", r["longitude"] or ""])
    safe_name = re.sub(r"[^\w\s-]", "", guest)[:64]
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=carboncoach_{safe_name}.csv"},
    )


@app.route("/api/clear", methods=["POST"])
def clear():
    guest = _get_guest()
    clear_session_data(guest)
    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_ENV") == "development")
