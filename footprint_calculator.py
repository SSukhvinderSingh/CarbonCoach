import os

TRANSPORT_FACTORS_KG_PER_KM = {
    "car_petrol": 0.192,
    "car_diesel": 0.171,
    "car_ev": 0.060,
    "two_wheeler_petrol": 0.065,
    "two_wheeler_ev": 0.020,
    "bus": 0.030,
    "metro": 0.020,
    "auto_rickshaw": 0.070,
    "flight_domestic": 0.150,
    "flight_international": 0.255,
    "bicycle": 0.0,
    "walk": 0.0,
    "train": 0.022,
}

DIET_FACTORS_KG_PER_MEAL = {
    "meat_heavy": 5.0,
    "meat_light": 2.5,
    "vegetarian": 1.5,
    "vegan": 1.0,
}

ENERGY_PER_ACTIVITY_KWH = {
    "ac_1hr": 1.5,
    "fan_1hr": 0.075,
    "lighting_1hr": 0.060,
    "tv_1hr": 0.120,
    "fridge_day": 1.2,
    "cooking_gas_1hr": 0.5,
    "water_heater_1hr": 2.0,
    "washing_machine_load": 0.8,
}

WASTE_FACTORS_KG_PER_KG = {
    "landfill": 0.6,
    "composted": -0.05,
    "recycled": -0.2,
    "incinerated": 0.4,
}

INDIA_DAILY_AVG_KG = 4.7
WORLD_DAILY_AVG_KG = 6.3


def _get_grid_factor():
    return float(os.environ.get("GRID_FACTOR_KG_CO2_PER_KWH", "0.71"))


def calculate(entry):
    category = entry["category"]
    activity_type = entry["activity_type"]
    quantity = entry["quantity"]

    if category == "transport":
        factor = TRANSPORT_FACTORS_KG_PER_KM.get(activity_type)
        if factor is None:
            raise ValueError(f"Unknown transport type: {activity_type}")
        co2_kg = round(factor * quantity, 4)

    elif category == "diet":
        factor = DIET_FACTORS_KG_PER_MEAL.get(activity_type)
        if factor is None:
            raise ValueError(f"Unknown diet type: {activity_type}")
        co2_kg = round(factor * quantity, 4)

    elif category == "energy":
        kwh = ENERGY_PER_ACTIVITY_KWH.get(activity_type)
        if kwh is None:
            raise ValueError(f"Unknown energy activity: {activity_type}")
        grid_factor = _get_grid_factor()
        co2_kg = round(grid_factor * kwh * quantity, 4)
        factor = grid_factor

    elif category == "waste":
        factor = WASTE_FACTORS_KG_PER_KG.get(activity_type)
        if factor is None:
            raise ValueError(f"Unknown waste type: {activity_type}")
        co2_kg = round(factor * quantity, 4)

    else:
        raise ValueError(f"Unknown category: {category}")

    return {"co2_kg": co2_kg, "factor_used": factor}


def benchmark(daily_total_kg):
    vs_india_pct = round(
        ((daily_total_kg - INDIA_DAILY_AVG_KG) / INDIA_DAILY_AVG_KG) * 100, 1
    ) if INDIA_DAILY_AVG_KG else 0.0
    return {
        "daily_total_kg": daily_total_kg,
        "india_daily_avg_kg": INDIA_DAILY_AVG_KG,
        "world_daily_avg_kg": WORLD_DAILY_AVG_KG,
        "vs_india_pct": vs_india_pct,
    }
