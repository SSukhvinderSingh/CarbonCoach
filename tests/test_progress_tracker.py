from datetime import date, timedelta

from progress_tracker import (
    create_session,
    save_activity,
    save_message,
    get_recent_messages,
    get_activities_since,
    get_today_activities,
    get_all_activity_summary,
    get_all_activities_csv,
    get_all_sessions,
    session_exists,
    clear_session_data,
)

TEST_USER = "testuser"


def setup_function():
    import progress_tracker
    conn = progress_tracker._get_connection()
    conn.execute("DELETE FROM activities")
    conn.execute("DELETE FROM messages")
    conn.execute("DELETE FROM sessions")
    conn.commit()
    conn.close()
    create_session(TEST_USER)


def test_save_and_get_messages():
    save_message(TEST_USER, "user", "hello")
    save_message(TEST_USER, "assistant", "hi there")
    msgs = get_recent_messages(TEST_USER, 5)
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    assert msgs[0]["content"] == "hello"
    assert msgs[1]["role"] == "assistant"
    assert msgs[1]["content"] == "hi there"


def test_save_and_get_activities():
    save_activity(TEST_USER, "transport", "car_petrol", 10, 1.92)
    today_acts = get_today_activities(TEST_USER)
    assert len(today_acts) == 1
    assert today_acts[0]["category"] == "transport"
    assert today_acts[0]["co2_kg"] == 1.92


def test_get_activities_since():
    save_activity(TEST_USER, "diet", "vegetarian", 2, 3.0)
    since = date.today() - timedelta(days=1)
    acts = get_activities_since(TEST_USER, since)
    assert len(acts) == 1


def test_get_activities_since_old_date():
    save_activity(TEST_USER, "diet", "vegetarian", 2, 3.0)
    since = date.today() - timedelta(days=10)
    acts = get_activities_since(TEST_USER, since)
    assert len(acts) >= 1


def test_get_all_activity_summary():
    save_activity(TEST_USER, "transport", "car_petrol", 10, 1.92)
    save_activity(TEST_USER, "diet", "vegetarian", 1, 1.5)
    summary = get_all_activity_summary(TEST_USER)
    assert "transport" in summary
    assert "diet" in summary


def test_get_all_activities_csv():
    save_activity(TEST_USER, "transport", "car_petrol", 10, 1.92)
    rows = get_all_activities_csv(TEST_USER)
    assert len(rows) == 1
    assert rows[0]["category"] == "transport"


def test_session_exists():
    assert session_exists(TEST_USER) == True
    assert session_exists("nonexistent") == False


def test_clear_session_data():
    save_activity(TEST_USER, "transport", "car_petrol", 10, 1.92)
    save_message(TEST_USER, "user", "hello")
    clear_session_data(TEST_USER)
    assert len(get_today_activities(TEST_USER)) == 0
    assert len(get_recent_messages(TEST_USER, 10)) == 0
    assert session_exists(TEST_USER) == False


def test_save_activity_with_location():
    save_activity(TEST_USER, "transport", "car_petrol", 10, 1.92, lat=12.34, lng=56.78)
    today_acts = get_today_activities(TEST_USER)
    assert len(today_acts) == 1
    assert today_acts[0]["latitude"] == 12.34
    assert today_acts[0]["longitude"] == 56.78


def test_get_all_sessions():
    create_session("user_a")
    create_session("user_b")
    all_sessions = get_all_sessions()
    names = [s["guest_name"] for s in all_sessions]
    assert "testuser" in names
    assert "user_a" in names
    assert "user_b" in names


def test_user_scoping():
    save_activity("user_a", "transport", "car_petrol", 10, 1.92)
    save_activity("user_b", "diet", "vegetarian", 2, 3.0)
    a_acts = get_today_activities("user_a")
    b_acts = get_today_activities("user_b")
    assert len(a_acts) == 1
    assert a_acts[0]["category"] == "transport"
    assert len(b_acts) == 1
    assert b_acts[0]["category"] == "diet"
