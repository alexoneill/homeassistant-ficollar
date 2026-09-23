"""Tests for FiDataUpdateCoordinator using pytest-homeassistant-custom-component."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed
from pyficollar.exceptions import FiAuthError, FiNetworkError
from pyficollar.models import ActivitySummary, Pet, PetLiveState, RestSummary, Walk

from custom_components.ficollar.coordinator import FiDataUpdateCoordinator


async def test_coordinator_update_success(
    hass: HomeAssistant,
    mock_fi_client: MagicMock,
    sample_pet: Pet,
    sample_live_state: PetLiveState,
    sample_activity: ActivitySummary,
    sample_rest: RestSummary,
    sample_walk: Walk,
) -> None:
    """Test successful data polling and parsing by coordinator."""
    coordinator = FiDataUpdateCoordinator(
        hass=hass,
        client=mock_fi_client,
        update_interval_seconds=60,
    )

    data = await coordinator._async_update_data()

    assert "pet_123" in data
    pet_data = data["pet_123"]
    assert pet_data.pet.name == "Luna"
    assert pet_data.live_state.battery_percent == 88
    assert pet_data.activity.total_steps == 8420
    assert pet_data.rest.sleep_hours == 8.0
    assert pet_data.last_walk.distance_km == 1.85


async def test_coordinator_auth_failure(
    hass: HomeAssistant,
    mock_fi_client: MagicMock,
) -> None:
    """Test FiAuthError raises ConfigEntryAuthFailed."""
    mock_fi_client.get_pets.side_effect = FiAuthError("Session expired")
    coordinator = FiDataUpdateCoordinator(
        hass=hass,
        client=mock_fi_client,
        update_interval_seconds=60,
    )

    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_update_data()


async def test_coordinator_network_failure(
    hass: HomeAssistant,
    mock_fi_client: MagicMock,
) -> None:
    """Test FiNetworkError raises UpdateFailed."""
    mock_fi_client.get_pets.side_effect = FiNetworkError("Cannot reach api.tryfi.com")
    coordinator = FiDataUpdateCoordinator(
        hass=hass,
        client=mock_fi_client,
        update_interval_seconds=60,
    )

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()
