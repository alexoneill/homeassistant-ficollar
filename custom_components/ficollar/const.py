"""Constants for the Fi Collar integration."""

from __future__ import annotations

import logging
from typing import Final

DOMAIN: Final = "ficollar"
DEFAULT_NAME: Final = "Fi Collar"
ATTRIBUTION: Final = "Data provided by TryFi"

LOGGER = logging.getLogger(__package__)

# Configuration keys
CONF_EMAIL: Final = "email"
CONF_PASSWORD: Final = "password"
CONF_SCAN_INTERVAL: Final = "scan_interval"

# Defaults
DEFAULT_SCAN_INTERVAL: Final = 60  # seconds
MIN_SCAN_INTERVAL: Final = 15  # seconds
MAX_SCAN_INTERVAL: Final = 600  # seconds

# Platforms
PLATFORMS: Final = [
    "device_tracker",
    "sensor",
    "binary_sensor",
    "light",
    "switch",
    "select",
]
