from footprint_calculator import calculate, benchmark


def test_transport_car_petrol():
    result = calculate({"category": "transport", "activity_type": "car_petrol", "quantity": 10})
    assert result["co2_kg"] == 1.92
    assert result["factor_used"] == 0.192


def test_transport_metro():
    result = calculate({"category": "transport", "activity_type": "metro", "quantity": 5})
    assert result["co2_kg"] == 0.10
    assert result["factor_used"] == 0.020


def test_transport_bicycle():
    result = calculate({"category": "transport", "activity_type": "bicycle", "quantity": 5})
    assert result["co2_kg"] == 0.0
    assert result["factor_used"] == 0.0


def test_diet_meat_heavy():
    result = calculate({"category": "diet", "activity_type": "meat_heavy", "quantity": 1})
    assert result["co2_kg"] == 5.0
    assert result["factor_used"] == 5.0


def test_diet_vegan():
    result = calculate({"category": "diet", "activity_type": "vegan", "quantity": 2})
    assert result["co2_kg"] == 2.0
    assert result["factor_used"] == 1.0


def test_energy_ac():
    result = calculate({"category": "energy", "activity_type": "ac_1hr", "quantity": 3})
    expected = round(0.71 * 1.5 * 3, 4)
    assert result["co2_kg"] == expected
    assert result["factor_used"] == 0.71


def test_waste_landfill():
    result = calculate({"category": "waste", "activity_type": "landfill", "quantity": 2})
    assert result["co2_kg"] == 1.2
    assert result["factor_used"] == 0.6


def test_waste_recycled():
    result = calculate({"category": "waste", "activity_type": "recycled", "quantity": 1})
    assert result["co2_kg"] == -0.2
    assert result["factor_used"] == -0.2


def test_unknown_category():
    import pytest
    with pytest.raises(ValueError, match="Unknown category"):
        calculate({"category": "invalid", "activity_type": "x", "quantity": 1})


def test_benchmark():
    result = benchmark(2.35)
    assert result["daily_total_kg"] == 2.35
    assert result["india_daily_avg_kg"] == 4.7
    assert result["world_daily_avg_kg"] == 6.3
    assert result["vs_india_pct"] == -50.0
