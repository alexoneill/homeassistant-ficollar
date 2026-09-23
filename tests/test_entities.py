"""Tests for Fi Collar entities (device tracker, sensors, binary sensors, light, switch)."""

from __future__ import annotations

from unittest.mock import MagicMock

from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant


async def test_device_tracker_state(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_fi_client: MagicMock,
) -> None:
    """Verify device tracker entity GPS coordinates and attributes in Home Assistant."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("device_tracker.luna_location")
    assert state is not None
    assert state.attributes.get("latitude") == 37.7749
    assert state.attributes.get("longitude") == -122.4194
    assert state.attributes.get("battery_level") == 88
    assert state.attributes.get("location_name") == "Home"
    assert state.attributes.get("is_at_home") is True


async def test_sensors_state(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_fi_client: MagicMock,
) -> None:
    """Verify sensors report correct values and attributes in Home Assistant."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    batt_state = hass.states.get("sensor.luna_battery")
    assert batt_state is not None
    assert batt_state.state == "88"

    steps_state = hass.states.get("sensor.luna_steps_today")
    assert steps_state is not None
    assert steps_state.state == "8420"

    goal_progress = hass.states.get("sensor.luna_step_goal_progress")
    assert goal_progress is not None
    assert goal_progress.state == "84.2"

    sleep_state = hass.states.get("sensor.luna_sleep_duration")
    assert sleep_state is not None
    assert sleep_state.state == "8.0"

    walk_dist = hass.states.get("sensor.luna_last_walk_distance")
    assert walk_dist is not None
    assert walk_dist.state == "1.85"


async def test_binary_sensors_state(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_fi_client: MagicMock,
) -> None:
    """Verify binary sensors reflect correct states."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    online_state = hass.states.get("binary_sensor.luna_online")
    assert online_state is not None
    assert online_state.state == STATE_ON

    out_of_batt_state = hass.states.get("binary_sensor.luna_out_of_battery")
    assert out_of_batt_state is not None
    assert out_of_batt_state.state == STATE_OFF


async def test_collar_light_services(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_fi_client: MagicMock,
) -> None:
    """Verify turning collar light on and off via Home Assistant services."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    light_state = hass.states.get("light.luna_collar_led")
    assert light_state is not None

    # Call light.turn_on service
    await hass.services.async_call(
        "light",
        "turn_on",
        {ATTR_ENTITY_ID: "light.luna_collar_led"},
        blocking=True,
    )
    mock_fi_client.set_led.assert_called_with("FC12345678", True)

    # Call light.turn_off service
    await hass.services.async_call(
        "light",
        "turn_off",
        {ATTR_ENTITY_ID: "light.luna_collar_led"},
        blocking=True,
    )
    mock_fi_client.set_led.assert_called_with("FC12345678", False)


async def test_lost_dog_mode_switch_service(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_fi_client: MagicMock,
) -> None:
    """Verify turning on lost dog mode via Home Assistant switch service."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    switch_state = hass.states.get("switch.luna_lost_dog_mode")
    assert switch_state is not None

    # Call switch.turn_on service
    await hass.services.async_call(
        "switch",
        "turn_on",
        {ATTR_ENTITY_ID: "switch.luna_lost_dog_mode"},
        blocking=True,
    )
    mock_fi_client.enable_lost_dog_mode.assert_called_with("pet_123")
