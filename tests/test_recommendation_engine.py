from recommendation_engine import recommend


def test_identifies_top_category():
    window = [
        {"category": "transport", "co2_kg": 2.0},
        {"category": "diet", "co2_kg": 5.0},
        {"category": "energy", "co2_kg": 1.0},
    ]
    today = [
        {"category": "transport", "co2_kg": 1.0},
    ]
    result = recommend(window, today)
    assert result["top_category"] == "diet"
    assert result["top_category_label"] == "Food & Diet"


def test_trend_insufficient_data():
    result = recommend([], [{"category": "transport", "co2_kg": 1.0}])
    assert result["trend"] == "insufficient_data"


def test_trend_improving():
    window = [
        {"category": "transport", "co2_kg": 5.0},
        {"category": "transport", "co2_kg": 5.0},
        {"category": "transport", "co2_kg": 2.0},
        {"category": "transport", "co2_kg": 2.0},
    ]
    result = recommend(window, [])
    assert result["trend"] == "improving"


def test_trend_worsening():
    window = [
        {"category": "transport", "co2_kg": 2.0},
        {"category": "transport", "co2_kg": 2.0},
        {"category": "transport", "co2_kg": 5.0},
        {"category": "transport", "co2_kg": 5.0},
    ]
    result = recommend(window, [])
    assert result["trend"] == "worsening"


def test_trend_steady():
    window = [
        {"category": "transport", "co2_kg": 3.0},
        {"category": "transport", "co2_kg": 3.0},
        {"category": "transport", "co2_kg": 3.1},
        {"category": "transport", "co2_kg": 2.9},
    ]
    result = recommend(window, [])
    assert result["trend"] == "steady"


def test_suggested_swaps_match_top_category():
    window = [{"category": "energy", "co2_kg": 10.0}]
    today = [{"category": "energy", "co2_kg": 5.0}]
    result = recommend(window, today)
    assert len(result["suggested_swaps"]) > 0
    for swap in result["suggested_swaps"]:
        assert "swap" in swap
        assert "est_daily_saving_kg" in swap


def test_no_suggested_swaps_for_unknown_category():
    result = recommend(
        [{"category": "unknown_cat", "co2_kg": 10.0}],
        [{"category": "unknown_cat", "co2_kg": 5.0}],
    )
    assert result["suggested_swaps"] == []
