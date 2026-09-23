"""Light platform for Fi Collar integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import ColorMode, LightEntity
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
    """Set up Fi Collar lights based on config entry."""
    coordinator: FiDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[FiCollarLight] = []
    for pet_id, data in coordinator.data.items():
        module_id = None
        if data.live_state and data.live_state.module_id:
            module_id = data.live_state.module_id
        elif data.pet and data.pet.device and data.pet.device.module_id:
            module_id = data.pet.device.module_id

        if module_id:
            entities.append(FiCollarLight(coordinator, pet_id, module_id))

    async_add_entities(entities)


class FiCollarLight(FiEntity, LightEntity):
    """Representing a Fi collar LED light."""

    _attr_icon = "mdi:led-on"
    _attr_supported_color_modes = {ColorMode.ONOFF}
    _attr_color_mode = ColorMode.ONOFF

    def __init__(
        self,
        coordinator: FiDataUpdateCoordinator,
        pet_id: str,
        module_id: str,
    ) -> None:
        """Initialize the collar light."""
        super().__init__(coordinator, pet_id)
        self.module_id = module_id
        self._attr_unique_id = f"{pet_id}_collar_led"
        self._attr_name = "Collar LED"
        self._assumed_state: bool | None = None

    @property
    def is_on(self) -> bool:
        """Return true if collar light is on."""
        if self._assumed_state is not None:
            return self._assumed_state
        if (
            self.pet_data
            and self.pet_data.pet
            and self.pet_data.pet.device
        ):
            return self.pet_data.pet.device.led_enabled
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs: dict[str, Any] = {"module_id": self.module_id}
        if self.pet_data and self.pet_data.live_state:
            live = self.pet_data.live_state
            if live.led_color:
                attrs["led_color"] = live.led_color.name
                attrs["led_color_hex"] = live.led_color.hex_code
            if live.available_led_colors:
                attrs["available_colors"] = [
                    c.name for c in live.available_led_colors
                ]
        return attrs

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the collar light on."""
        try:
            await self.hass.async_add_executor_job(
                self.coordinator.client.set_led,
                self.module_id,
                True,
            )
            self._assumed_state = True
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
        except Exception as err:
            LOGGER.error("Failed to turn on Fi collar LED: %s", err)
            raise

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the collar light off."""
        try:
            await self.hass.async_add_executor_job(
                self.coordinator.client.set_led,
                self.module_id,
                False,
            )
            self._assumed_state = False
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
        except Exception as err:
            LOGGER.error("Failed to turn off Fi collar LED: %s", err)
            raise
