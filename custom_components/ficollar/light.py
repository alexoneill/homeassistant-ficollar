"""Light platform for Fi Collar integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import ATTR_RGB_COLOR, ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LOGGER
from .coordinator import FiDataUpdateCoordinator
from .entity import FiEntity


def _hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    """Convert hex string (e.g. 'ff2fcc' or '#ff2fcc') to RGB tuple."""
    clean = hex_str.lstrip("#")
    if len(clean) == 6:
        try:
            return (
                int(clean[0:2], 16),
                int(clean[2:4], 16),
                int(clean[4:6], 16),
            )
        except ValueError:
            pass
    return (255, 255, 255)


def _closest_color_code(
    target_rgb: tuple[int, int, int],
    available_colors: list[Any],
) -> int:
    """Find the closest LED color code to the requested RGB tuple."""
    best_code = 5  # default Purple
    min_dist = float("inf")
    tr, tg, tb = target_rgb
    for color in available_colors:
        r, g, b = _hex_to_rgb(color.hex_code)
        dist = (r - tr) ** 2 + (g - tg) ** 2 + (b - tb) ** 2
        if dist < min_dist:
            min_dist = dist
            best_code = color.led_color_code
    return best_code


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
    _attr_supported_color_modes = {ColorMode.RGB}
    _attr_color_mode = ColorMode.RGB

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
    def rgb_color(self) -> tuple[int, int, int] | None:
        """Return the rgb color value."""
        if self.pet_data:
            if self.pet_data.live_state and self.pet_data.live_state.led_color:
                return _hex_to_rgb(self.pet_data.live_state.led_color.hex_code)
            if (
                self.pet_data.pet
                and self.pet_data.pet.device
                and self.pet_data.pet.device.led_color
            ):
                return _hex_to_rgb(self.pet_data.pet.device.led_color.hex_code)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs: dict[str, Any] = {"module_id": self.module_id}
        if self.pet_data:
            live = self.pet_data.live_state
            device = self.pet_data.pet.device if self.pet_data.pet else None
            led_color = (live.led_color if live else None) or (device.led_color if device else None)
            available = (live.available_led_colors if live else None) or (device.available_led_colors if device else None)

            if led_color:
                attrs["led_color"] = led_color.name
                attrs["led_color_hex"] = led_color.hex_code
                attrs["led_color_code"] = led_color.led_color_code
            if available:
                attrs["available_colors"] = [c.name for c in available]
        return attrs

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the collar light on, optionally setting color."""
        try:
            if ATTR_RGB_COLOR in kwargs:
                target_rgb = kwargs[ATTR_RGB_COLOR]
                available = []
                if self.pet_data and self.pet_data.live_state and self.pet_data.live_state.available_led_colors:
                    available = self.pet_data.live_state.available_led_colors
                elif self.pet_data and self.pet_data.pet and self.pet_data.pet.device and self.pet_data.pet.device.available_led_colors:
                    available = self.pet_data.pet.device.available_led_colors

                color_code = _closest_color_code(target_rgb, available) if available else 5
                await self.hass.async_add_executor_job(
                    self.coordinator.client.set_led_color,
                    self.module_id,
                    color_code,
                )

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
