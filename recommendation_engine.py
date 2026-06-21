SWAP_LIBRARY = {
    "transport": [
        {"swap": "Switch from car to metro for your commute", "est_daily_saving_kg": 3.0},
        {"swap": "Try taking a bus instead of driving", "est_daily_saving_kg": 2.5},
        {"swap": "Consider an EV or two-wheeler for short trips", "est_daily_saving_kg": 1.8},
        {"swap": "Walk or cycle for trips under 2 km", "est_daily_saving_kg": 1.2},
    ],
    "diet": [
        {"swap": "Try one vegetarian meal per day", "est_daily_saving_kg": 2.5},
        {"swap": "Swap red meat for plant-based protein once a week", "est_daily_saving_kg": 3.0},
        {"swap": "Go vegan for one meal a day", "est_daily_saving_kg": 4.0},
    ],
    "energy": [
        {"swap": "Set AC to 24°C instead of 18°C", "est_daily_saving_kg": 1.5},
        {"swap": "Switch to LED bulbs throughout your home", "est_daily_saving_kg": 0.3},
        {"swap": "Use a fan instead of AC when possible", "est_daily_saving_kg": 2.0},
        {"swap": "Unplug electronics when not in use", "est_daily_saving_kg": 0.2},
    ],
    "waste": [
        {"swap": "Start composting kitchen waste", "est_daily_saving_kg": 0.5},
        {"swap": "Separate recyclables from general waste", "est_daily_saving_kg": 0.4},
        {"swap": "Reduce food waste by meal planning", "est_daily_saving_kg": 0.8},
    ],
}

CATEGORY_LABELS = {
    "transport": "Transport",
    "diet": "Food & Diet",
    "energy": "Home Energy",
    "waste": "Waste",
}


def _classify_trend(activities_window):
    if not activities_window:
        return {"trend": "insufficient_data", "trend_details": None}

    has_time = all("logged_at" in a and a["logged_at"] for a in activities_window)

    if not has_time:
        if len(activities_window) < 2:
            return {"trend": "insufficient_data", "trend_details": None}
        mid = len(activities_window) // 2
        first_half = activities_window[:mid]
        second_half = activities_window[mid:]
        if not first_half or not second_half:
            return {"trend": "insufficient_data", "trend_details": None}
        first_total = sum(a["co2_kg"] for a in first_half)
        second_total = sum(a["co2_kg"] for a in second_half)
        if first_total == 0:
            return {"trend": "insufficient_data", "trend_details": None}
        change_pct = ((second_total - first_total) / first_total) * 100
        if change_pct <= -5:
            trend = "improving"
        elif change_pct >= 5:
            trend = "worsening"
        else:
            trend = "steady"
        return {"trend": trend, "trend_details": None}

    try:
        from datetime import datetime
        daily_totals = {}
        for a in activities_window:
            dt = datetime.fromisoformat(a["logged_at"])
            d = dt.date()
            daily_totals[d] = daily_totals.get(d, 0) + a["co2_kg"]
    except (ValueError, TypeError):
        return {"trend": "insufficient_data", "trend_details": None}

    sorted_days = sorted(daily_totals.items())

    if len(sorted_days) < 2:
        return {"trend": "insufficient_data", "trend_details": None}

    first_date = sorted_days[0][0]
    last_date = sorted_days[-1][0]
    mid_point = first_date + (last_date - first_date) / 2

    first_days = [(d, v) for d, v in sorted_days if d < mid_point]
    second_days = [(d, v) for d, v in sorted_days if d >= mid_point]

    if not first_days or not second_days:
        return {"trend": "insufficient_data", "trend_details": None}

    first_avg = sum(v for _, v in first_days) / len(first_days)
    second_avg = sum(v for _, v in second_days) / len(second_days)

    if first_avg == 0:
        return {"trend": "insufficient_data", "trend_details": None}

    change_pct = ((second_avg - first_avg) / first_avg) * 100

    if change_pct <= -5:
        trend = "improving"
    elif change_pct >= 5:
        trend = "worsening"
    else:
        trend = "steady"

    return {
        "trend": trend,
        "trend_details": {
            "first_avg": round(first_avg, 2),
            "second_avg": round(second_avg, 2),
            "days_count": len(sorted_days),
        },
    }


def _classify_daily_trend(today_activities):
    if not today_activities or len(today_activities) < 2:
        return {"trend": "insufficient_data", "trend_details": None}

    has_time = all("logged_at" in a and a["logged_at"] for a in today_activities)
    if not has_time:
        return {"trend": "insufficient_data", "trend_details": None}

    try:
        from datetime import datetime
        sorted_acts = sorted(today_activities, key=lambda a: a["logged_at"])
        dt0 = datetime.fromisoformat(sorted_acts[0]["logged_at"])
        dtN = datetime.fromisoformat(sorted_acts[-1]["logged_at"])
        mid_point = dt0 + (dtN - dt0) / 2
        first_half = [a for a in sorted_acts if datetime.fromisoformat(a["logged_at"]) < mid_point]
        second_half = [a for a in sorted_acts if datetime.fromisoformat(a["logged_at"]) >= mid_point]
    except (ValueError, TypeError):
        return {"trend": "insufficient_data", "trend_details": None}

    if not first_half or not second_half:
        return {"trend": "insufficient_data", "trend_details": None}

    first_avg = sum(a["co2_kg"] for a in first_half) / len(first_half)
    second_avg = sum(a["co2_kg"] for a in second_half) / len(second_half)

    if first_avg == 0:
        return {"trend": "insufficient_data", "trend_details": None}

    change_pct = ((second_avg - first_avg) / first_avg) * 100

    if change_pct <= -5:
        trend = "improving"
    elif change_pct >= 5:
        trend = "worsening"
    else:
        trend = "steady"

    return {
        "trend": trend,
        "trend_details": {
            "first_avg": round(first_avg, 2),
            "second_avg": round(second_avg, 2),
            "entries_count": len(sorted_acts),
        },
    }


def recommend(activities_window, today_activities, trend_mode="7day"):
    all_activities = activities_window + today_activities

    category_totals_kg = {}
    for a in all_activities:
        cat = a["category"]
        category_totals_kg[cat] = category_totals_kg.get(cat, 0) + a["co2_kg"]

    for cat in category_totals_kg:
        category_totals_kg[cat] = round(category_totals_kg[cat], 4)

    today_total_kg = round(sum(a["co2_kg"] for a in today_activities), 4)

    top_category = None
    top_category_label = None
    if category_totals_kg:
        top_category = max(category_totals_kg, key=category_totals_kg.get)
        top_category_label = CATEGORY_LABELS.get(top_category, top_category)

    if trend_mode == "daily":
        trend_result = _classify_daily_trend(today_activities)
    else:
        trend_result = _classify_trend(activities_window)
    trend = trend_result["trend"]
    trend_details = trend_result["trend_details"]

    suggested_swaps = []
    if top_category and top_category in SWAP_LIBRARY:
        suggested_swaps = SWAP_LIBRARY[top_category][:2]

    return {
        "top_category": top_category,
        "top_category_label": top_category_label,
        "category_totals_kg": category_totals_kg,
        "today_total_kg": today_total_kg,
        "trend": trend,
        "trend_details": trend_details,
        "trend_mode": trend_mode,
        "suggested_swaps": suggested_swaps,
    }
