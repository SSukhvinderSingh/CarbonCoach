import json
import os
import re

KWD_EXTRACTION_TEMPLATES = {
    "transport": {
        r"\bcar\b.*?(?:petrol|diesel)?": "car_petrol",
        r"\bcar.*?ev\b": "car_ev",
        r"\bbike\b": "two_wheeler_petrol",
        r"\bbus\b": "bus",
        r"\bmetro\b": "metro",
        r"\bauto\b": "auto_rickshaw",
        r"\bflight\b.*?(?:domestic)?": "flight_domestic",
        r"\bflight.*?international\b": "flight_international",
        r"\btrain\b": "train",
        r"\b(?:walk|walked|walking)\b": "walk",
        r"\b(?:cycle|cycled|cycling|bicycle)\b": "bicycle",
    },
    "energy": {
        r"\bac\b": "ac_1hr",
        r"\bfan\b": "fan_1hr",
        r"\blight\b": "lighting_1hr",
        r"\btv\b": "tv_1hr",
        r"\bfridge\b": "fridge_day",
        r"\bcooking|gas\b": "cooking_gas_1hr",
        r"\bwater heater|geyser\b": "water_heater_1hr",
        r"\bwashing|laundry\b": "washing_machine_load",
    },
    "waste": {
        r"\brecycled?\b": "recycled",
        r"\bcompost\b": "composted",
        r"\blandfill|trash|garbage\b": "landfill",
        r"\bincinerat(?:ed|or)\b": "incinerated",
    },
}

MEAL_KEYWORDS = {
    "meat_heavy": r"\b(?:meat|chicken|mutton|beef|pork|fish|burger|sausage)\b",
    "meat_light": r"\b(?:egg|eggs?|paneer|dairy|milk|curd|yogurt)\b",
    "vegetarian": r"\b(?:vegetarian|veg|sabzi|dal|rice|roti|chapati|pulses|vegetables?)\b",
    "vegan": r"\b(?:vegan|tofu|soy|plant.based)\b",
}


def _keyword_extract_activities(user_message):
    msg_lower = user_message.lower()
    activities = []

    meal_type = None
    meal_quantity = 1
    for meal_key, pattern in MEAL_KEYWORDS.items():
        if re.search(pattern, msg_lower):
            meal_type = meal_key
            break

    if meal_type:
        for qty_match in re.finditer(r"(\d+)\s*(?:time|meal|plate|bowl)", msg_lower):
            meal_quantity = int(qty_match.group(1))
            break
        activities.append({
            "category": "diet",
            "activity_type": meal_type,
            "quantity": meal_quantity,
        })

    distance_match = re.search(r"(\d+\.?\d*)\s*(?:km|kms|kilometer)", msg_lower)
    distance = float(distance_match.group(1)) if distance_match else None

    if distance:
        for transport_type, patterns in KWD_EXTRACTION_TEMPLATES["transport"].items():
            for pattern in [patterns] if isinstance(patterns, str) else [patterns]:
                if re.search(pattern, msg_lower):
                    activities.append({
                        "category": "transport",
                        "activity_type": patterns if isinstance(patterns, str) else patterns[0],
                        "quantity": distance,
                    })
                    break
        if not any(a["category"] == "transport" for a in activities):
            activities.append({
                "category": "transport",
                "activity_type": "car_petrol",
                "quantity": distance,
            })

    energy_match = re.search(r"(\d+\.?\d*)\s*hr", msg_lower)
    if energy_match:
        energy_hours = float(energy_match.group(1))
        for energy_type, pattern in KWD_EXTRACTION_TEMPLATES["energy"].items():
            if re.search(pattern, msg_lower):
                activities.append({
                    "category": "energy",
                    "activity_type": energy_type if isinstance(energy_type, str) else list(energy_type.keys())[0],
                    "quantity": energy_hours,
                })

    waste_match = re.search(r"(\d+\.?\d*)\s*(?:kg|kilo)", msg_lower)
    if waste_match:
        waste_qty = float(waste_match.group(1))
        for waste_type, pattern in KWD_EXTRACTION_TEMPLATES["waste"].items():
            if re.search(pattern, msg_lower):
                activities.append({
                    "category": "waste",
                    "activity_type": waste_type if isinstance(waste_type, str) else list(waste_type.keys())[0],
                    "quantity": waste_qty,
                })

    return activities if activities else None


def _build_fallback_reply(grounding):
    top = grounding.get("top_category_label", "")
    total = grounding.get("today_total_kg", 0)
    trend = grounding.get("trend", "insufficient_data")
    swaps = grounding.get("suggested_swaps", [])
    bench = grounding.get("benchmark", {})

    lines = []
    if total > 0 and top:
        lines.append(
            f"Thanks! I've logged your activities — your estimated total is "
            f"{total:.1f} kg CO₂e today."
        )
        lines.append(
            f"Your biggest contributor is **{top}**."
        )
    else:
        lines.append("Thanks! I've logged your activities for today.")

    if trend == "improving":
        lines.append("You're improving compared to recent days — keep it up!")
    elif trend == "worsening":
        lines.append("Your emissions are trending up lately — see if a small swap helps.")
    elif trend == "steady":
        lines.append("You're staying consistent with recent days.")

    if swaps:
        lines.append(
            f"Try this: {swaps[0]['swap']} "
            f"(saves ~{swaps[0]['est_daily_saving_kg']:.1f} kg CO₂e/day)."
        )

    if bench:
        vp = bench.get("vs_india_pct", 0)
        if vp > 0:
            lines.append(
                f"That's {vp:.0f}% above the Indian daily average of "
                f"{bench.get('india_daily_avg_kg', 4.7)} kg — see where you can cut back."
            )
        elif vp < 0:
            lines.append(
                f"That's {abs(vp):.0f}% below the Indian daily average of "
                f"{bench.get('india_daily_avg_kg', 4.7)} kg — great going!"
            )

    return " ".join(lines)


def _try_gemini_extract(user_message):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None

    try:
        from google import genai

        model_name = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
        client = genai.Client(api_key=api_key)

        prompt = (
            "Extract daily activities from the user's message. "
            "Return a JSON array of objects with keys: category, activity_type, quantity. "
            "Categories: transport, diet, energy, waste. "
            "Transport types: car_petrol, car_diesel, car_ev, two_wheeler_petrol, two_wheeler_ev, "
            "bus, metro, auto_rickshaw, flight_domestic, flight_international, bicycle, walk, train. "
            "Diet types: meat_heavy, meat_light, vegetarian, vegan. "
            "Energy types: ac_1hr, fan_1hr, lighting_1hr, tv_1hr, fridge_day, cooking_gas_1hr, "
            "water_heater_1hr, washing_machine_load. "
            "Waste types: landfill, composted, recycled, incinerated. "
            "Only include activities explicitly mentioned. Never invent quantities. "
            "Respond with ONLY the JSON array, no other text.\n\n"
            f"User message: {user_message}"
        )

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config={"max_output_tokens": 400, "temperature": 0.1},
        )
        text = response.text.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        return json.loads(text)
    except Exception:
        return None


def _try_gemini_reply(user_message, grounding, history):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None

    try:
        from google import genai

        model_name = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
        client = genai.Client(api_key=api_key)

        system_prompt = (
            "You are CarbonCoach, a friendly carbon footprint assistant. "
            "You help people in India track and reduce their personal carbon emissions. "
            "CRITICAL RULE: You must NEVER invent or calculate CO2 numbers yourself. "
            "Only narrate the exact numbers provided in the grounding data below. "
            "Reply warmly in 2-4 sentences. Do not add any numbers not in the grounding data."
        )

        grounding_str = json.dumps(grounding, indent=2)
        prompt = (
            f"{system_prompt}\n\n"
            f"Grounding data (use only these numbers):\n{grounding_str}\n\n"
            f"User message: {user_message}\n\n"
            f"Reply:"
        )

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config={"max_output_tokens": 400, "temperature": 0.7},
        )
        return response.text.strip()
    except Exception:
        return None


def extract_activities(user_message):
    activities = _try_gemini_extract(user_message)
    if activities is not None:
        return activities
    fallback = _keyword_extract_activities(user_message)
    if fallback is not None:
        return fallback
    return []


def generate_reply(user_message, grounding, history=None):
    gemini_reply = _try_gemini_reply(user_message, grounding, history or [])
    if gemini_reply:
        return gemini_reply
    return _build_fallback_reply(grounding)
