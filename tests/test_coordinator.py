"""Tests for FiDataUpdateCoordinator."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).parent.parent.resolve()
PYFICOLLAR_ROOT = (REPO_ROOT.parent / "pyficollar").resolve()
for p in [str(REPO_ROOT), str(PYFICOLLAR_ROOT)]:
    if Path(p).exists() and p not in sys.path:
        sys.path.insert(0, p)

try:
    from tests.mock_ha import setup_mock_homeassistant
except ModuleNotFoundError:
    from mock_ha import setup_mock_homeassistant

setup_mock_homeassistant()

from pyficollar.exceptions import FiAuthError, FiNetworkError
from pyficollar.models import ActivitySummary, Device, Pet, PetLiveState, RestSummary, Walk

from custom_components.ficollar.coordinator import FiDataUpdateCoordinator
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed


def create_sample_pet(pet_id: str = "pet_123", name: str = "Luna") -> Pet:
    """Create a sample Pet model instance."""
    return Pet(
        id=pet_id,
        name=name,
        breed_name="Golden Retriever",
        gender="FEMALE",
        weight=25.0,
        device=Device(id="collar_abc_789", module_id="FC12345678", battery_percent=88),
    )


class TestCoordinator(unittest.TestCase):
    """Test FiDataUpdateCoordinator data polling and error handling."""

    def setUp(self) -> None:
        self.hass = HomeAssistant()
        self.mock_client = MagicMock()
        self.coordinator = FiDataUpdateCoordinator(
            hass=self.hass,
            client=self.mock_client,
            update_interval_seconds=60,
        )

    def test_update_data_success(self) -> None:
        """Verify successful poll populates pet data map."""
        pet = create_sample_pet()
        self.mock_client.get_pets.return_value = [pet]
        self.mock_client.get_pet_live_state.return_value = PetLiveState(
            pet_id="pet_123",
            is_online=True,
            battery_percent=88,
            location_name="Home",
        )
        self.mock_client.get_pet_activity.return_value = ActivitySummary(
            total_steps=8420,
            step_goal=10000,
        )
        self.mock_client.get_pet_rest.return_value = RestSummary(
            has_sleep_data=True,
            sleep_seconds=28800,
            nap_seconds=7200,
            rest_seconds=36000,
        )
        self.mock_client.get_last_walk.return_value = Walk(
            id="walk_1",
            start="2026-09-23T12:00:00Z",
            distance_meters=1850.0,
            total_steps=2400,
        )

        data = asyncio.run(self.coordinator._async_update_data())

        self.assertIn("pet_123", data)
        pet_data = data["pet_123"]
        self.assertEqual(pet_data.pet.name, "Luna")
        self.assertEqual(pet_data.live_state.location_name, "Home")
        self.assertEqual(pet_data.activity.total_steps, 8420)
        self.assertEqual(pet_data.rest.rest_seconds, 36000)
        self.assertEqual(pet_data.last_walk.total_steps, 2400)

    def test_update_data_auth_failure(self) -> None:
        """Verify FiAuthError raises ConfigEntryAuthFailed."""
        self.mock_client.get_pets.side_effect = FiAuthError("Expired session")

        with self.assertRaises(ConfigEntryAuthFailed):
            asyncio.run(self.coordinator._async_update_data())

    def test_update_data_network_failure(self) -> None:
        """Verify FiNetworkError raises UpdateFailed."""
        self.mock_client.get_pets.side_effect = FiNetworkError("Timeout")

        with self.assertRaises(UpdateFailed):
            asyncio.run(self.coordinator._async_update_data())


if __name__ == "__main__":
    unittest.main()
