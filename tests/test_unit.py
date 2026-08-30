from app import celsius_to_fahrenheit


def test_freezing():
    assert celsius_to_fahrenheit(0) == 32.0


def test_boiling():
    assert celsius_to_fahrenheit(100) == 212.0


def test_body_temperature():
    assert celsius_to_fahrenheit(37) == 98.6


def test_negative_forty_is_equal():
    assert celsius_to_fahrenheit(-40) == -40.0
