"""Tests for Fi Collar entities (device tracker, sensors, binary sensors, light, switch)."""

from __future__ import annotations

import asyncio
from pathlib import Path
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock

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

from pyficollar.models import (
    ActivitySummary,
    Device,
    Location,
    Pet,
    PetLiveState,
    Place,
    Position,
    RestSummary,
    Walk,
)

from custom_components.ficollar.binary_sensor import (
    BINARY_SENSOR_DESCRIPTIONS,
    FiBinarySensor,
)
from custom_components.ficollar.coordinator import PetCoordinatorData
from custom_components.ficollar.device_tracker import FiDeviceTracker
from custom_components.ficollar.light import FiCollarLight
from custom_components.ficollar.sensor import (
    SENSOR_DESCRIPTIONS,
    FiSensor,
)
from custom_components.ficollar.switch import FiLostDogModeSwitch
from homeassistant.core import HomeAssistant


def build_mock_coordinator(pet_id: str = "pet_123") -> tuple[MagicMock, MagicMock]:
    """Build a mock coordinator with complete populated PetCoordinatorData."""
    mock_client = MagicMock()
    mock_coordinator = MagicMock()
    mock_coordinator.hass = HomeAssistant()
    mock_coordinator.client = mock_client
    mock_coordinator.async_request_refresh = AsyncMock()

    pet = Pet(
        id=pet_id,
        name="Luna",
        weight=25.0,
        device=Device(
            id="collar_abc_789",
            module_id="FC12345678",
            battery_percent=88,
            led_enabled=True,
        ),
    )
    live_state = PetLiveState(
        pet_id=pet_id,
        is_online=True,
        is_stale=False,
        out_of_battery=False,
        lost_mode="LOST",
        battery_percent=88,
        location_name="Home",
        location=Location(
            position=Position(latitude=37.7749, longitude=-122.4194),
            error_radius=12.5,
            place=Place(id="pl_1", name="Home", is_quick_zone=True),
        ),
        is_walking=True,
        ongoing_steps=450,
        module_id="FC12345678",
    )
    activity = ActivitySummary(
        total_steps=9120,
        step_goal=10000,
        streak_days=5,
    )
    rest = RestSummary(
        has_sleep_data=True,
        sleep_seconds=28800,
        nap_seconds=7200,
        rest_seconds=36000,
    )
    last_walk = Walk(
        id="walk_1",
        start="2026-09-23T12:00:00Z",
        distance_meters=2100.0,
        total_steps=2700,
    )

    pet_data = PetCoordinatorData(
        pet=pet,
        live_state=live_state,
        activity=activity,
        rest=rest,
        last_walk=last_walk,
    )
    mock_coordinator.data = {pet_id: pet_data}
    return mock_coordinator, mock_client


class TestEntities(unittest.TestCase):
    """Test entity platforms and state accessors."""

    def setUp(self) -> None:
        self.coordinator, self.client = build_mock_coordinator("pet_123")

    def test_device_tracker(self) -> None:
        """Verify device tracker GPS and safe zone properties."""
        tracker = FiDeviceTracker(self.coordinator, "pet_123")

        self.assertEqual(tracker.latitude, 37.7749)
        self.assertEqual(tracker.longitude, -122.4194)
        self.assertEqual(tracker.location_accuracy, 12)
        self.assertEqual(tracker.battery_level, 88)
        self.assertEqual(tracker.source_type, "gps")

        attrs = tracker.extra_state_attributes
        self.assertEqual(attrs["location_name"], "Home")
        self.assertTrue(attrs["is_at_home"])

    def test_sensors(self) -> None:
        """Verify values for all sensor types."""
        desc_map = {d.key: d for d in SENSOR_DESCRIPTIONS}

        battery_sensor = FiSensor(self.coordinator, "pet_123", desc_map["battery"])
        self.assertEqual(battery_sensor.native_value, 88)

        steps_sensor = FiSensor(self.coordinator, "pet_123", desc_map["steps_today"])
        self.assertEqual(steps_sensor.native_value, 9120)

        goal_progress_sensor = FiSensor(self.coordinator, "pet_123", desc_map["step_goal_progress"])
        self.assertEqual(goal_progress_sensor.native_value, 91.2)

        sleep_sensor = FiSensor(self.coordinator, "pet_123", desc_map["sleep_hours"])
        self.assertEqual(sleep_sensor.native_value, 8.0)

        walk_dist_sensor = FiSensor(self.coordinator, "pet_123", desc_map["last_walk_distance"])
        self.assertEqual(walk_dist_sensor.native_value, 2.1)

        weight_sensor = FiSensor(self.coordinator, "pet_123", desc_map["weight"])
        self.assertEqual(weight_sensor.native_value, 25.0)

    def test_binary_sensors(self) -> None:
        """Verify binary sensor state booleans."""
        desc_map = {d.key: d for d in BINARY_SENSOR_DESCRIPTIONS}

        online_sensor = FiBinarySensor(self.coordinator, "pet_123", desc_map["online"])
        self.assertTrue(online_sensor.is_on)

        out_of_batt_sensor = FiBinarySensor(self.coordinator, "pet_123", desc_map["out_of_battery"])
        self.assertFalse(out_of_batt_sensor.is_on)

        lost_sensor = FiBinarySensor(self.coordinator, "pet_123", desc_map["lost_mode"])
        self.assertTrue(lost_sensor.is_on)

        walking_sensor = FiBinarySensor(self.coordinator, "pet_123", desc_map["is_walking"])
        self.assertTrue(walking_sensor.is_on)

        stale_sensor = FiBinarySensor(self.coordinator, "pet_123", desc_map["is_stale"])
        self.assertFalse(stale_sensor.is_on)

    def test_collar_light(self) -> None:
        """Verify collar light status, turn_on, and turn_off."""
        light = FiCollarLight(self.coordinator, "pet_123", "FC12345678")
        self.assertTrue(light.is_on)

        asyncio.run(light.async_turn_off())
        self.client.set_led.assert_called_with("FC12345678", False)

        asyncio.run(light.async_turn_on())
        self.client.set_led.assert_called_with("FC12345678", True)

    def test_lost_dog_mode_switch(self) -> None:
        """Verify lost dog mode switch state and activation."""
        switch = FiLostDogModeSwitch(self.coordinator, "pet_123")
        self.assertTrue(switch.is_on)

        asyncio.run(switch.async_turn_on())
        self.client.enable_lost_dog_mode.assert_called_with("pet_123")


if __name__ == "__main__":
    unittest.main()
