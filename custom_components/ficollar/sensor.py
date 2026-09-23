"""Sensor platform for Fi Collar integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfLength, UnitOfMass, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import FiDataUpdateCoordinator, PetCoordinatorData
from .entity import FiEntity


@dataclass(frozen=True, kw_only=True)
class FiSensorEntityDescription(SensorEntityDescription):
    """Describes Fi sensor entity."""

    value_fn: Callable[[PetCoordinatorData], Any]
    extra_attrs_fn: Callable[[PetCoordinatorData], dict[str, Any]] | None = None


SENSOR_DESCRIPTIONS: tuple[FiSensorEntityDescription, ...] = (
    FiSensorEntityDescription(
        key="battery",
        name="Battery",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.live_state.battery_percent if d.live_state else None,
    ),
    FiSensorEntityDescription(
        key="steps_today",
        name="Steps Today",
        icon="mdi:walk",
        native_unit_of_measurement="steps",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: d.activity.total_steps if d.activity else None,
    ),
    FiSensorEntityDescription(
        key="step_goal",
        name="Step Goal",
        icon="mdi:bullseye-arrow",
        native_unit_of_measurement="steps",
        value_fn=lambda d: d.activity.step_goal if d.activity else None,
    ),
    FiSensorEntityDescription(
        key="step_goal_progress",
        name="Step Goal Progress",
        icon="mdi:progress-check",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.activity.goal_percent if d.activity else None,
    ),
    FiSensorEntityDescription(
        key="streak_days",
        name="Goal Streak",
        icon="mdi:fire",
        native_unit_of_measurement="days",
        value_fn=lambda d: d.activity.streak_days if d.activity else None,
    ),
    FiSensorEntityDescription(
        key="sleep_hours",
        name="Sleep Duration",
        icon="mdi:sleep",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.rest.sleep_hours if d.rest else None,
    ),
    FiSensorEntityDescription(
        key="nap_hours",
        name="Nap Duration",
        icon="mdi:power-sleep",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.rest.nap_hours if d.rest else None,
    ),
    FiSensorEntityDescription(
        key="rest_hours",
        name="Total Rest",
        icon="mdi:bed-clock",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.rest.rest_hours if d.rest else None,
    ),
    FiSensorEntityDescription(
        key="last_walk_distance",
        name="Last Walk Distance",
        icon="mdi:map-marker-distance",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.last_walk.distance_km if d.last_walk else None,
        extra_attrs_fn=lambda d: {
            "start": d.last_walk.start,
            "end": d.last_walk.end,
            "walker": d.last_walk.present_user_name,
            "steps": d.last_walk.total_steps,
            "map_url": d.last_walk.map_url,
        }
        if d.last_walk
        else {},
    ),
    FiSensorEntityDescription(
        key="last_walk_steps",
        name="Last Walk Steps",
        icon="mdi:shoe-print",
        native_unit_of_measurement="steps",
        value_fn=lambda d: d.last_walk.total_steps if d.last_walk else None,
    ),
    FiSensorEntityDescription(
        key="ongoing_steps",
        name="Ongoing Walk Steps",
        icon="mdi:walk",
        native_unit_of_measurement="steps",
        value_fn=lambda d: d.live_state.ongoing_steps if d.live_state else None,
    ),
    FiSensorEntityDescription(
        key="weight",
        name="Weight",
        icon="mdi:scale",
        device_class=SensorDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.pet.weight if (d.pet and d.pet.weight) else None,
        extra_attrs_fn=lambda d: {
            "weight_lbs": d.pet.weight_lbs,
            "breed": d.pet.breed_name,
            "gender": d.pet.gender,
        }
        if d.pet
        else {},
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Fi Collar sensors based on config entry."""
    coordinator: FiDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        FiSensor(coordinator, pet_id, description)
        for pet_id in coordinator.data
        for description in SENSOR_DESCRIPTIONS
    ]
    async_add_entities(entities)


class FiSensor(FiEntity, SensorEntity):
    """Representing a Fi collar sensor."""

    entity_description: FiSensorEntityDescription

    def __init__(
        self,
        coordinator: FiDataUpdateCoordinator,
        pet_id: str,
        description: FiSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, pet_id)
        self.entity_description = description
        self._attr_unique_id = f"{pet_id}_{description.key}"

    @property
    def native_value(self) -> Any:
        """Return the native value of the sensor."""
        if not self.pet_data:
            return None
        return self.entity_description.value_fn(self.pet_data)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        if not self.pet_data or not self.entity_description.extra_attrs_fn:
            return {}
        return self.entity_description.extra_attrs_fn(self.pet_data)
