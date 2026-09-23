"""Global fixtures for Fi Collar integration tests."""

from __future__ import annotations

from typing import Generator
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ficollar.const import (
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    DOMAIN,
)
from pyficollar.models import (
    ActivitySummary,
    Device,
    Location,
    Pet,
    PetLiveState,
    Place,
    Position,
    RestSummary,
    User,
    Walk,
)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> Generator[None, None, None]:
    """Enable custom integrations in Home Assistant core test instance."""
    yield


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Create a mock Fi Collar config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Fi Collar (Alex O'Neill)",
        unique_id="user_123456",
        data={
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "secret_password",
            CONF_SCAN_INTERVAL: 60,
        },
        options={
            CONF_SCAN_INTERVAL: 60,
        },
        entry_id="ficollar_test_entry_id",
    )


@pytest.fixture
def sample_pet() -> Pet:
    """Create a sample Pet fixture."""
    return Pet(
        id="pet_123",
        name="Luna",
        breed_name="Golden Retriever",
        gender="FEMALE",
        weight=25.0,
        photo_url="https://example.com/luna.jpg",
        device=Device(
            id="collar_abc_789",
            module_id="FC12345678",
            battery_percent=88,
            led_enabled=False,
        ),
    )


@pytest.fixture
def sample_live_state() -> PetLiveState:
    """Create a sample PetLiveState fixture."""
    return PetLiveState(
        pet_id="pet_123",
        is_online=True,
        is_stale=False,
        out_of_battery=False,
        lost_mode=None,
        battery_percent=88,
        location_name="Home",
        location=Location(
            position=Position(latitude=37.7749, longitude=-122.4194),
            error_radius=12.5,
            place=Place(id="pl_1", name="Home", is_quick_zone=True),
        ),
        is_walking=False,
        ongoing_steps=0,
        module_id="FC12345678",
    )


@pytest.fixture
def sample_activity() -> ActivitySummary:
    """Create a sample ActivitySummary fixture."""
    return ActivitySummary(
        total_steps=8420,
        step_goal=10000,
        streak_days=5,
    )


@pytest.fixture
def sample_rest() -> RestSummary:
    """Create a sample RestSummary fixture."""
    return RestSummary(
        has_sleep_data=True,
        sleep_seconds=28800,
        nap_seconds=7200,
        rest_seconds=36000,
    )


@pytest.fixture
def sample_walk() -> Walk:
    """Create a sample Walk fixture."""
    return Walk(
        id="walk_1",
        start="2026-09-23T12:00:00Z",
        distance_meters=1850.0,
        total_steps=2400,
    )


@pytest.fixture
def mock_fi_client(
    sample_pet: Pet,
    sample_live_state: PetLiveState,
    sample_activity: ActivitySummary,
    sample_rest: RestSummary,
    sample_walk: Walk,
) -> Generator[MagicMock, None, None]:
    """Mock the FiClient instance."""
    with patch("custom_components.ficollar.FiClient") as mock_client_cls, patch(
        "custom_components.ficollar.config_flow.FiClient", new=mock_client_cls
    ):
        mock_client = MagicMock()
        type(mock_client).current_user_id = PropertyMock(return_value="user_123456")
        mock_client.get_current_user.return_value = User(
            id="user_123456",
            email="test@example.com",
            first_name="Alex",
            last_name="O'Neill",
        )
        mock_client.get_pets.return_value = [sample_pet]
        mock_client.get_pet_live_state.return_value = sample_live_state
        mock_client.get_pet_activity.return_value = sample_activity
        mock_client.get_pet_rest.return_value = sample_rest
        mock_client.get_last_walk.return_value = sample_walk
        mock_client_cls.return_value = mock_client
        yield mock_client
