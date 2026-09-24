"""Select platform for Fi Collar integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LOGGER
from .coordinator import FiDataUpdateCoordinator
from .entity import FiEntity

DEFAULT_COLORS: list[tuple[int, str, str]] = [
    (2, "ff4242", "Red"),
    (3, "3cba0f", "Green"),
    (4, "0071ff", "Blue"),
    (5, "ff2fcc", "Purple"),
    (6, "ffff01", "Yellow"),
    (7, "00ffff", "Cyan"),
    (8, "ffffff", "White"),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Fi Collar select entities based on config entry."""
    coordinator: FiDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[FiCollarLightColorSelect] = []
    for pet_id, data in coordinator.data.items():
        module_id = None
        if data.live_state and data.live_state.module_id:
            module_id = data.live_state.module_id
        elif data.pet and data.pet.device and data.pet.device.module_id:
            module_id = data.pet.device.module_id

        if module_id:
            entities.append(FiCollarLightColorSelect(coordinator, pet_id, module_id))

    async_add_entities(entities)


class FiCollarLightColorSelect(FiEntity, SelectEntity):
    """Representing the collar LED light color selection."""

    _attr_icon = "mdi:palette"

    def __init__(
        self,
        coordinator: FiDataUpdateCoordinator,
        pet_id: str,
        module_id: str,
    ) -> None:
        """Initialize the light color select entity."""
        super().__init__(coordinator, pet_id)
        self.module_id = module_id
        self._attr_unique_id = f"{pet_id}_collar_light_color"
        self._attr_name = "Collar Light Color"

    @property
    def options(self) -> list[str]:
        """Return available color options."""
        if self.pet_data:
            live = self.pet_data.live_state
            device = self.pet_data.pet.device if self.pet_data.pet else None
            available = (live.available_led_colors if live else None) or (
                device.available_led_colors if device else None
            )
            if available:
                return [c.name for c in available]
        return [c[2] for c in DEFAULT_COLORS]

    @property
    def current_option(self) -> str | None:
        """Return the currently selected color."""
        if self.pet_data:
            live = self.pet_data.live_state
            device = self.pet_data.pet.device if self.pet_data.pet else None
            led_color = (live.led_color if live else None) or (
                device.led_color if device else None
            )
            if led_color:
                return led_color.name
        return None

    async def async_select_option(self, option: str) -> None:
        """Change the selected collar LED color."""
        # Find matching color code
        color_code: int | None = None
        if self.pet_data:
            live = self.pet_data.live_state
            device = self.pet_data.pet.device if self.pet_data.pet else None
            available = (live.available_led_colors if live else None) or (
                device.available_led_colors if device else None
            )
            if available:
                for c in available:
                    if c.name.lower() == option.lower():
                        color_code = c.led_color_code
                        break

        if color_code is None:
            for code, _, name in DEFAULT_COLORS:
                if name.lower() == option.lower():
                    color_code = code
                    break

        if color_code is None:
            LOGGER.error("Invalid LED color option requested: %s", option)
            return

        try:
            await self.hass.async_add_executor_job(
                self.coordinator.client.set_led_color,
                self.module_id,
                color_code,
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            LOGGER.error("Failed to set Fi collar LED color: %s", err)
            raise
