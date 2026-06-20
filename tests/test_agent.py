import json

from footprint_calculator import calculate

TEST_USER = "testagent"


def _setup():
    from progress_tracker import create_session, clear_session_data
    import progress_tracker
    conn = progress_tracker._get_connection()
    conn.execute("DELETE FROM activities")
    conn.execute("DELETE FROM messages")
    conn.execute("DELETE FROM sessions")
    conn.commit()
    conn.close()
    create_session(TEST_USER)


def test_logged_activities_match_footprint_calculator():
    entries = [
        {"category": "transport", "activity_type": "car_petrol", "quantity": 10},
        {"category": "diet", "activity_type": "meat_heavy", "quantity": 1},
        {"category": "energy", "activity_type": "ac_1hr", "quantity": 3},
    ]
    for entry in entries:
        result = calculate(entry)
        assert "co2_kg" in result
        assert "factor_used" in result
        assert isinstance(result["co2_kg"], float)


def test_grounding_top_category_matches_max():
    from recommendation_engine import recommend

    window = [
        {"category": "transport", "co2_kg": 3.0},
        {"category": "diet", "co2_kg": 7.0},
        {"category": "energy", "co2_kg": 1.5},
    ]
    today = [{"category": "diet", "co2_kg": 2.0}]

    result = recommend(window, today)
    category_totals = result["category_totals_kg"]
    expected_top = max(category_totals, key=category_totals.get)
    assert result["top_category"] == expected_top


def test_chat_endpoint():
    _setup()
    from app import app
    client = app.test_client()

    response = client.post(
        "/api/chat",
        data=json.dumps({"message": "drove 10 km and had chicken for lunch"}),
        content_type="application/json",
        headers={"X-Guest-Name": TEST_USER},
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "reply" in data
    assert "logged_activities" in data
    assert len(data["logged_activities"]) > 0
    assert "co2_kg" in data["logged_activities"][0]
    assert data["grounding"]["today_total_kg"] >= 0


def test_chat_empty_message():
    from app import app
    client = app.test_client()
    response = client.post(
        "/api/chat",
        data=json.dumps({"message": ""}),
        content_type="application/json",
    )
    assert response.status_code == 400


def test_summary_endpoint():
    from app import app
    client = app.test_client()
    response = client.get("/api/summary", headers={"X-Guest-Name": TEST_USER})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "today_total_kg" in data
    assert "trend" in data


def test_login_endpoint():
    from app import app
    client = app.test_client()
    response = client.post(
        "/api/login",
        data=json.dumps({"guest_name": "newuser"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["ok"] == True
    assert data["guest_name"] == "newuser"


def test_chat_with_location():
    _setup()
    from app import app
    client = app.test_client()
    response = client.post(
        "/api/chat",
        data=json.dumps({"message": "drove 10 km", "location": {"lat": 12.34, "lng": 56.78}}),
        content_type="application/json",
        headers={"X-Guest-Name": TEST_USER},
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data["logged_activities"]) > 0
    assert data["logged_activities"][0]["latitude"] == 12.34
    assert data["logged_activities"][0]["longitude"] == 56.78


def test_sessions_endpoint():
    from app import app
    client = app.test_client()
    response = client.get("/api/sessions")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "sessions" in data
    assert isinstance(data["sessions"], list)


def test_login_empty_name():
    from app import app
    client = app.test_client()
    response = client.post(
        "/api/login",
        data=json.dumps({"guest_name": ""}),
        content_type="application/json",
    )
    assert response.status_code == 400


def test_clear_endpoint():
    _setup()
    from app import app
    client = app.test_client()
    response = client.post("/api/clear", headers={"X-Guest-Name": TEST_USER})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["ok"] == True


def test_activities_endpoint():
    _setup()
    from app import app
    client = app.test_client()
    response = client.get("/api/activities", headers={"X-Guest-Name": TEST_USER})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "activities" in data


def test_export_endpoint():
    _setup()
    from app import app
    client = app.test_client()
    from progress_tracker import save_activity
    save_activity(TEST_USER, "transport", "car_petrol", 10, 1.92)
    response = client.get("/api/export", headers={"X-Guest-Name": TEST_USER})
    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert b"car_petrol" in response.data
