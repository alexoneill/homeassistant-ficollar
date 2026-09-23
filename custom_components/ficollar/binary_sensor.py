"""Binary sensor platform for Fi Collar integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import FiDataUpdateCoordinator, PetCoordinatorData
from .entity import FiEntity


@dataclass(frozen=True, kw_only=True)
class FiBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes Fi binary sensor entity."""

    is_on_fn: Callable[[PetCoordinatorData], bool | None]


BINARY_SENSOR_DESCRIPTIONS: tuple[FiBinarySensorEntityDescription, ...] = (
    FiBinarySensorEntityDescription(
        key="online",
        name="Online",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        is_on_fn=lambda d: d.live_state.is_online if d.live_state else None,
    ),
    FiBinarySensorEntityDescription(
        key="out_of_battery",
        name="Out of Battery",
        device_class=BinarySensorDeviceClass.BATTERY,
        is_on_fn=lambda d: d.live_state.out_of_battery if d.live_state else None,
    ),
    FiBinarySensorEntityDescription(
        key="lost_mode",
        name="Lost Mode",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:alert-decagram",
        is_on_fn=lambda d: bool(d.live_state.lost_mode) if d.live_state else None,
    ),
    FiBinarySensorEntityDescription(
        key="is_walking",
        name="Walking",
        device_class=BinarySensorDeviceClass.MOVING,
        icon="mdi:walk",
        is_on_fn=lambda d: d.live_state.is_walking if d.live_state else None,
    ),
    FiBinarySensorEntityDescription(
        key="is_stale",
        name="Stale Connection",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:wifi-alert",
        is_on_fn=lambda d: d.live_state.is_stale if d.live_state else None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Fi Collar binary sensors based on config entry."""
    coordinator: FiDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        FiBinarySensor(coordinator, pet_id, description)
        for pet_id in coordinator.data
        for description in BINARY_SENSOR_DESCRIPTIONS
    ]
    async_add_entities(entities)


class FiBinarySensor(FiEntity, BinarySensorEntity):
    """Representing a Fi collar binary sensor."""

    entity_description: FiBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: FiDataUpdateCoordinator,
        pet_id: str,
        description: FiBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, pet_id)
        self.entity_description = description
        self._attr_unique_id = f"{pet_id}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if not self.pet_data:
            return None
        return self.entity_description.is_on_fn(self.pet_data)
