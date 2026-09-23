"""Lightweight in-memory test doubles for Home Assistant modules.

Enables running complete unit tests for custom_components.ficollar offline
with zero mandatory external dependencies, matching pyficollar's testing design.
"""

from __future__ import annotations

from dataclasses import dataclass
import sys
import types
from typing import Any
from unittest.mock import MagicMock


def setup_mock_homeassistant() -> None:
    """Inject mock Home Assistant modules into sys.modules if not installed."""
    if "homeassistant" in sys.modules and not isinstance(sys.modules["homeassistant"], MagicMock):
        return

    # Mock voluptuous
    vol = types.ModuleType("voluptuous")

    class Schema:
        def __init__(self, schema: Any, extra: Any = None) -> None:
            self.schema = schema
            self.extra = extra

        def __call__(self, val: Any) -> Any:
            return val

    class Marker:
        def __init__(self, key: Any, default: Any = None, description: Any = None) -> None:
            self.key = key
            self.default = default
            self.description = description

    vol.Schema = Schema
    vol.Required = Marker
    vol.Optional = Marker
    vol.All = lambda *args: (lambda v: v)
    vol.Coerce = lambda t: t
    vol.Range = lambda **kwargs: (lambda v: v)
    vol.In = lambda items: (lambda v: v)
    vol.ALLOW_EXTRA = 1
    sys.modules["voluptuous"] = vol

    # Mock homeassistant core
    ha = types.ModuleType("homeassistant")
    sys.modules["homeassistant"] = ha

    # homeassistant.const
    ha_const = types.ModuleType("homeassistant.const")
    ha_const.CONF_EMAIL = "email"
    ha_const.CONF_PASSWORD = "password"
    ha_const.CONF_SCAN_INTERVAL = "scan_interval"
    ha_const.PERCENTAGE = "%"

    class Platform:
        DEVICE_TRACKER = "device_tracker"
        SENSOR = "sensor"
        BINARY_SENSOR = "binary_sensor"
        LIGHT = "light"
        SWITCH = "switch"

    class UnitOfLength:
        KILOMETERS = "km"
        MILES = "mi"
        METERS = "m"

    class UnitOfMass:
        KILOGRAMS = "kg"
        POUNDS = "lb"

    class UnitOfTime:
        HOURS = "h"
        MINUTES = "min"
        SECONDS = "s"

    ha_const.Platform = Platform
    ha_const.UnitOfLength = UnitOfLength
    ha_const.UnitOfMass = UnitOfMass
    ha_const.UnitOfTime = UnitOfTime
    sys.modules["homeassistant.const"] = ha_const

    # homeassistant.core
    ha_core = types.ModuleType("homeassistant.core")

    class HomeAssistant:
        def __init__(self) -> None:
            self.data: dict[str, Any] = {}
            self.config_entries = MagicMock()

        async def async_add_executor_job(self, target: Any, *args: Any, **kwargs: Any) -> Any:
            return target(*args, **kwargs)

    def callback(func: Any) -> Any:
        return func

    ha_core.HomeAssistant = HomeAssistant
    ha_core.callback = callback
    sys.modules["homeassistant.core"] = ha_core

    # homeassistant.exceptions
    ha_exc = types.ModuleType("homeassistant.exceptions")

    class HomeAssistantError(Exception):
        pass

    class ConfigEntryAuthFailed(HomeAssistantError):
        pass

    ha_exc.HomeAssistantError = HomeAssistantError
    ha_exc.ConfigEntryAuthFailed = ConfigEntryAuthFailed
    sys.modules["homeassistant.exceptions"] = ha_exc

    # homeassistant.config_entries
    ha_ce = types.ModuleType("homeassistant.config_entries")

    class ConfigEntry:
        def __init__(
            self,
            version: int = 1,
            domain: str = "ficollar",
            title: str = "Fi Collar",
            data: dict[str, Any] | None = None,
            options: dict[str, Any] | None = None,
            entry_id: str = "test_entry_id",
            unique_id: str = "test_unique_id",
        ) -> None:
            self.version = version
            self.domain = domain
            self.title = title
            self.data = data or {}
            self.options = options or {}
            self.entry_id = entry_id
            self.unique_id = unique_id
            self._update_listeners: list[Any] = []

        def add_update_listener(self, listener: Any) -> Any:
            self._update_listeners.append(listener)
            return lambda: self._update_listeners.remove(listener)

        def async_on_unload(self, callback_func: Any) -> None:
            pass

    class ConfigFlow:
        def __init_subclass__(cls, domain: str | None = None, **kwargs: Any) -> None:
            super().__init_subclass__(**kwargs)
            cls._domain = domain

        def __init__(self) -> None:
            self.hass: HomeAssistant = HomeAssistant()
            self.context: dict[str, Any] = {}
            self.unique_id: str | None = None
            self._abort_entries_match: bool = False

        async def async_set_unique_id(self, unique_id: str) -> None:
            self.unique_id = unique_id

        def _abort_if_unique_id_configured(self) -> None:
            if self._abort_entries_match:
                raise Exception("already_configured")

        def async_show_form(
            self,
            step_id: str,
            data_schema: Any = None,
            errors: dict[str, str] | None = None,
            description_placeholders: dict[str, str] | None = None,
        ) -> dict[str, Any]:
            return {
                "type": "form",
                "step_id": step_id,
                "data_schema": data_schema,
                "errors": errors or {},
                "description_placeholders": description_placeholders or {},
            }

        def async_create_entry(
            self,
            title: str,
            data: dict[str, Any],
            options: dict[str, Any] | None = None,
        ) -> dict[str, Any]:
            return {
                "type": "create_entry",
                "title": title,
                "data": data,
                "options": options or {},
            }

        def async_abort(self, reason: str) -> dict[str, Any]:
            return {"type": "abort", "reason": reason}

        def _get_reauth_entry(self) -> ConfigEntry:
            return ConfigEntry(
                data={"email": "test@example.com", "password": "old_password"},
                unique_id="test_user_id",
            )

    class OptionsFlow:
        def __init__(self, config_entry: ConfigEntry | None = None) -> None:
            self.config_entry = config_entry
            self.hass: HomeAssistant = HomeAssistant()

        def async_show_form(
            self,
            step_id: str,
            data_schema: Any = None,
            errors: dict[str, str] | None = None,
        ) -> dict[str, Any]:
            return {
                "type": "form",
                "step_id": step_id,
                "data_schema": data_schema,
                "errors": errors or {},
            }

        def async_create_entry(
            self,
            title: str,
            data: dict[str, Any],
        ) -> dict[str, Any]:
            return {"type": "create_entry", "title": title, "data": data}

    ha_ce.ConfigEntry = ConfigEntry
    ha_ce.ConfigFlow = ConfigFlow
    ha_ce.OptionsFlow = OptionsFlow
    sys.modules["homeassistant.config_entries"] = ha_ce

    # homeassistant.data_entry_flow
    ha_def = types.ModuleType("homeassistant.data_entry_flow")
    ha_def.FlowResult = dict[str, Any]
    sys.modules["homeassistant.data_entry_flow"] = ha_def

    # homeassistant.helpers
    ha_helpers = types.ModuleType("homeassistant.helpers")
    sys.modules["homeassistant.helpers"] = ha_helpers

    # homeassistant.helpers.config_validation
    ha_cv = types.ModuleType("homeassistant.helpers.config_validation")
    ha_cv.string = str
    ha_cv.positive_int = int
    sys.modules["homeassistant.helpers.config_validation"] = ha_cv

    # homeassistant.helpers.device_registry
    ha_dr = types.ModuleType("homeassistant.helpers.device_registry")

    class DeviceInfo(dict):
        def __init__(self, **kwargs: Any) -> None:
            super().__init__(**kwargs)
            for k, v in kwargs.items():
                setattr(self, k, v)

    ha_dr.DeviceInfo = DeviceInfo
    sys.modules["homeassistant.helpers.device_registry"] = ha_dr

    # homeassistant.helpers.entity_platform
    ha_ep = types.ModuleType("homeassistant.helpers.entity_platform")
    ha_ep.AddEntitiesCallback = Any
    sys.modules["homeassistant.helpers.entity_platform"] = ha_ep

    # homeassistant.helpers.update_coordinator
    ha_uc = types.ModuleType("homeassistant.helpers.update_coordinator")

    class UpdateFailed(HomeAssistantError):
        pass

    class DataUpdateCoordinator:
        __class_getitem__ = classmethod(lambda cls, item: cls)

        def __init__(self, hass: HomeAssistant, logger: Any, name: str, update_interval: Any = None) -> None:
            self.hass = hass
            self.logger = logger
            self.name = name
            self.update_interval = update_interval
            self.data: Any = None
            self._listeners: list[Any] = []

        def async_add_listener(self, update_callback: Any) -> Any:
            self._listeners.append(update_callback)
            return lambda: self._listeners.remove(update_callback)

        async def async_request_refresh(self) -> None:
            await self._async_update_data()

    class CoordinatorEntity:
        __class_getitem__ = classmethod(lambda cls, item: cls)

        def __init__(self, coordinator: Any, *args: Any, **kwargs: Any) -> None:
            self.coordinator = coordinator
            self.hass = getattr(coordinator, "hass", None)
            self._attr_has_entity_name = True
            self._attr_attribution = None

        @property
        def available(self) -> bool:
            return True

        def async_write_ha_state(self) -> None:
            pass

    ha_uc.UpdateFailed = UpdateFailed
    ha_uc.DataUpdateCoordinator = DataUpdateCoordinator
    ha_uc.CoordinatorEntity = CoordinatorEntity
    sys.modules["homeassistant.helpers.update_coordinator"] = ha_uc

    # homeassistant.components
    ha_comp = types.ModuleType("homeassistant.components")
    sys.modules["homeassistant.components"] = ha_comp

    # homeassistant.components.device_tracker
    ha_dt = types.ModuleType("homeassistant.components.device_tracker")

    class SourceType:
        GPS = "gps"
        ROUTER = "router"

    class TrackerEntity:
        pass

    ha_dt.SourceType = SourceType
    ha_dt.TrackerEntity = TrackerEntity
    sys.modules["homeassistant.components.device_tracker"] = ha_dt

    # homeassistant.components.sensor
    ha_sensor = types.ModuleType("homeassistant.components.sensor")

    class SensorDeviceClass:
        BATTERY = "battery"
        DURATION = "duration"
        DISTANCE = "distance"
        WEIGHT = "weight"

    class SensorStateClass:
        MEASUREMENT = "measurement"
        TOTAL_INCREASING = "total_increasing"

    @dataclass(frozen=True, kw_only=True)
    class SensorEntityDescription:
        key: str
        device_class: Any = None
        state_class: Any = None
        native_unit_of_measurement: Any = None
        suggested_display_precision: Any = None
        icon: Any = None
        name: Any = None
        entity_category: Any = None

    class SensorEntity:
        pass

    ha_sensor.SensorDeviceClass = SensorDeviceClass
    ha_sensor.SensorStateClass = SensorStateClass
    ha_sensor.SensorEntityDescription = SensorEntityDescription
    ha_sensor.SensorEntity = SensorEntity
    sys.modules["homeassistant.components.sensor"] = ha_sensor

    # homeassistant.components.binary_sensor
    ha_bs = types.ModuleType("homeassistant.components.binary_sensor")

    class BinarySensorDeviceClass:
        CONNECTIVITY = "connectivity"
        BATTERY = "battery"
        PROBLEM = "problem"
        MOVING = "moving"

    @dataclass(frozen=True, kw_only=True)
    class BinarySensorEntityDescription:
        key: str
        device_class: Any = None
        name: Any = None
        icon: Any = None
        entity_category: Any = None

    class BinarySensorEntity:
        pass

    ha_bs.BinarySensorDeviceClass = BinarySensorDeviceClass
    ha_bs.BinarySensorEntityDescription = BinarySensorEntityDescription
    ha_bs.BinarySensorEntity = BinarySensorEntity
    sys.modules["homeassistant.components.binary_sensor"] = ha_bs

    # homeassistant.components.light
    ha_light = types.ModuleType("homeassistant.components.light")

    class ColorMode:
        ONOFF = "onoff"
        RGB = "rgb"

    class LightEntity:
        pass

    ha_light.ColorMode = ColorMode
    ha_light.LightEntity = LightEntity
    sys.modules["homeassistant.components.light"] = ha_light

    # homeassistant.components.switch
    ha_switch = types.ModuleType("homeassistant.components.switch")

    class SwitchEntity:
        pass

    ha_switch.SwitchEntity = SwitchEntity
    sys.modules["homeassistant.components.switch"] = ha_switch
