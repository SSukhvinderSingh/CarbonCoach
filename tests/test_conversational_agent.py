from conversational_insight_generator import _keyword_extract_activities, _build_fallback_reply


def test_keyword_extract_diet():
    result = _keyword_extract_activities("I ate chicken for lunch today")
    assert result is not None
    assert any(a["category"] == "diet" and a["activity_type"] == "meat_heavy" for a in result)


def test_keyword_extract_transport():
    result = _keyword_extract_activities("drove 15 km to work")
    assert result is not None
    transport = [a for a in result if a["category"] == "transport"]
    assert len(transport) > 0
    assert transport[0]["quantity"] == 15.0


def test_keyword_extract_metro():
    result = _keyword_extract_activities("took the metro 5 km")
    assert result is not None
    transport = [a for a in result if a["category"] == "transport"]
    assert len(transport) > 0
    assert transport[0]["quantity"] == 5.0


def test_keyword_extract_empty():
    result = _keyword_extract_activities("hello how are you")
    assert result is None


def test_fallback_reply_contains_numbers():
    grounding = {
        "top_category": "Transport",
        "top_category_label": "Transport",
        "today_total_kg": 4.5,
        "category_totals_kg": {"transport": 3.0, "diet": 1.5},
        "trend": "worsening",
        "suggested_swaps": [
            {"swap": "Switch from car to metro", "est_daily_saving_kg": 3.0}
        ],
        "benchmark": {
            "daily_total_kg": 4.5,
            "india_daily_avg_kg": 4.7,
            "world_daily_avg_kg": 6.3,
            "vs_india_pct": -4.3,
        },
    }
    reply = _build_fallback_reply(grounding)
    assert "4.5" in reply
    assert "Transport" in reply
    assert "3.0" in reply


def test_fallback_reply_empty_activities():
    grounding = {
        "top_category": None,
        "top_category_label": None,
        "today_total_kg": 0,
        "category_totals_kg": {},
        "trend": "insufficient_data",
        "suggested_swaps": [],
        "benchmark": None,
    }
    reply = _build_fallback_reply(grounding)
    assert len(reply) > 0
