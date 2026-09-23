"""Device tracker platform for Fi Collar integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import FiDataUpdateCoordinator
from .entity import FiEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Fi Collar device tracker based on config entry."""
    coordinator: FiDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        FiDeviceTracker(coordinator, pet_id)
        for pet_id in coordinator.data
    ]
    async_add_entities(entities)


class FiDeviceTracker(FiEntity, TrackerEntity):
    """Representing a Fi pet collar GPS device tracker."""

    _attr_icon = "mdi:dog"

    def __init__(
        self,
        coordinator: FiDataUpdateCoordinator,
        pet_id: str,
    ) -> None:
        """Initialize the device tracker."""
        super().__init__(coordinator, pet_id)
        self._attr_unique_id = f"{pet_id}_tracker"
        self._attr_name = "Location"

    @property
    def source_type(self) -> SourceType:
        """Return the source type of the device tracker."""
        return SourceType.GPS

    @property
    def latitude(self) -> float | None:
        """Return latitude value of the collar."""
        if self.pet_data and self.pet_data.live_state:
            return self.pet_data.live_state.latitude
        return None

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the collar."""
        if self.pet_data and self.pet_data.live_state:
            return self.pet_data.live_state.longitude
        return None

    @property
    def location_accuracy(self) -> int:
        """Return the location accuracy of the collar in meters."""
        if (
            self.pet_data
            and self.pet_data.live_state
            and self.pet_data.live_state.location
            and self.pet_data.live_state.location.error_radius is not None
        ):
            return int(self.pet_data.live_state.location.error_radius)
        return 10

    @property
    def battery_level(self) -> int | None:
        """Return the battery level of the collar."""
        if self.pet_data and self.pet_data.live_state:
            return self.pet_data.live_state.battery_percent
        return None

    @property
    def entity_picture(self) -> str | None:
        """Return the pet photo URL."""
        if self.pet_data and self.pet_data.pet:
            return self.pet_data.pet.photo_url
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs: dict[str, Any] = {}
        if not self.pet_data or not self.pet_data.live_state:
            return attrs

        live = self.pet_data.live_state
        if live.location_name:
            attrs["location_name"] = live.location_name
        if live.at_safe_zone:
            attrs["safe_zone_name"] = live.at_safe_zone.name
            attrs["safe_zone_address"] = live.at_safe_zone.address
        attrs["is_at_home"] = live.is_at_home
        attrs["is_stale"] = live.is_stale
        attrs["is_walking"] = live.is_walking
        if live.last_report_timestamp:
            attrs["last_report_timestamp"] = live.last_report_timestamp
        if live.next_update_expected_by:
            attrs["next_update_expected_by"] = live.next_update_expected_by
        if live.backhaul:
            attrs["backhaul"] = live.backhaul
        if live.module_id:
            attrs["module_id"] = live.module_id

        return attrs
