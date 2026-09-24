"""Tests for Fi Collar component initialization and teardown."""

from __future__ import annotations

from unittest.mock import MagicMock

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ficollar.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant


async def test_async_setup_and_unload_entry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_fi_client: MagicMock,
) -> None:
    """Test setting up and unloading the integration entry."""
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert DOMAIN in hass.data
    assert mock_config_entry.entry_id in hass.data[DOMAIN]

    # Verify entities were created in Home Assistant state registry
    assert hass.states.get("device_tracker.luna_location") is not None
    assert hass.states.get("sensor.luna_battery") is not None
    assert hass.states.get("sensor.luna_steps_today") is not None
    assert hass.states.get("binary_sensor.luna_online") is not None
    assert hass.states.get("light.luna_collar_led") is not None
    assert hass.states.get("switch.luna_lost_dog_mode") is not None

    # Test unloading entry
    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED
    assert mock_config_entry.entry_id not in hass.data[DOMAIN]


async def test_async_setup_entry_auth_failed(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_fi_client: MagicMock,
) -> None:
    """Test handling authentication failure during entry setup."""
    from pyficollar.exceptions import FiAuthError

    mock_fi_client.login.side_effect = FiAuthError("Unauthorized")
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR
