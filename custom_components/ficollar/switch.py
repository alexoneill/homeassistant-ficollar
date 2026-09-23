"""Switch platform for Fi Collar integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LOGGER
from .coordinator import FiDataUpdateCoordinator
from .entity import FiEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Fi Collar switches based on config entry."""
    coordinator: FiDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        FiLostDogModeSwitch(coordinator, pet_id)
        for pet_id in coordinator.data
    ]
    async_add_entities(entities)


class FiLostDogModeSwitch(FiEntity, SwitchEntity):
    """Switch to activate or check Lost Dog Mode."""

    _attr_icon = "mdi:dog-side"

    def __init__(
        self,
        coordinator: FiDataUpdateCoordinator,
        pet_id: str,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, pet_id)
        self._attr_unique_id = f"{pet_id}_lost_mode_switch"
        self._attr_name = "Lost Dog Mode"

    @property
    def is_on(self) -> bool:
        """Return true if lost dog mode is active."""
        if self.pet_data and self.pet_data.live_state:
            return bool(self.pet_data.live_state.lost_mode)
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        if (
            self.pet_data
            and self.pet_data.live_state
            and self.pet_data.live_state.lost_mode
        ):
            return {"lost_mode_type": self.pet_data.live_state.lost_mode}
        return {}

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable lost dog mode."""
        try:
            ttl = await self.hass.async_add_executor_job(
                self.coordinator.client.enable_lost_dog_mode,
                self.pet_id,
            )
            LOGGER.info("Enabled lost dog mode for pet %s (TTL: %s seconds)", self.pet_id, ttl)
            await self.coordinator.async_request_refresh()
        except Exception as err:
            LOGGER.error("Failed to enable lost dog mode: %s", err)
            raise

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off lost dog mode.

        TryFi API automatically times out lost dog mode based on its TTL.
        """
        LOGGER.warning(
            "TryFi does not provide an immediate disable API for lost mode; it expires automatically."
        )
