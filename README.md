# Fi Smart Dog Collar for Home Assistant

[![Validate Integration](https://github.com/alexoneill/homeassistant-ficollar/actions/workflows/validate.yml/badge.svg)](https://github.com/alexoneill/homeassistant-ficollar/actions/workflows/validate.yml)
[![Tests](https://github.com/alexoneill/homeassistant-ficollar/actions/workflows/test.yml/badge.svg)](https://github.com/alexoneill/homeassistant-ficollar/actions/workflows/test.yml)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/default)
[![GitHub Release](https://img.shields.io/github/v/release/alexoneill/homeassistant-ficollar?style=for-the-badge)](https://github.com/alexoneill/homeassistant-ficollar/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

A Home Assistant custom integration for the **Fi Smart Dog Collar** (Series 2 & Series 3), powered by [`pyficollar`](https://github.com/alexoneill/pyficollar).

Track your dog's live GPS coordinates, battery level, daily steps, sleep patterns, walks, and control the collar LED directly from Home Assistant.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=alexoneill&repository=homeassistant-ficollar&category=integration)

---

## Features

- 📍 **GPS Tracking (`device_tracker`)**: Real-time latitude, longitude, accuracy radius, and safe zone awareness on Home Assistant maps.
- 🔋 **Battery Monitoring (`sensor`)**: Accurate battery percentage and low-battery alerts.
- 🏃 **Activity & Fitness (`sensor`)**: Daily steps, step goals, progress percentage, strain score, and goal streak tracking.
- 💤 **Rest & Sleep Monitoring (`sensor`)**: Overnight sleep hours, nap duration, and total rest time.
- 🦮 **Walk Tracking (`sensor`)**: Distance (km), walk steps, walker name, and link to route maps.
- 💡 **Collar LED Control (`light`)**: Turn the collar LED on/off and view collar color settings.
- 🚨 **Lost Dog Mode (`switch`)**: Trigger emergency high-frequency GPS tracking mode directly from Home Assistant automations or dashboards.
- 📶 **Status & Connectivity (`binary_sensor`)**: Online status, stale connection detection, and walking state.
- ⚙️ **Configurable Polling Interval**: Requested upon initial setup and adjustable at any time via Integration Options.

---

## Installation

### Method 1: HACS (Recommended)

1. Ensure [HACS](https://hacs.xyz/) is installed in your Home Assistant instance.
2. Click the badge above or navigate to **HACS** > **Integrations** > **Custom repositories** (three dots in top right).
3. Add repository URL: `https://github.com/alexoneill/homeassistant-ficollar` with Category: **Integration**.
4. Click **Download**, then restart Home Assistant.

### Method 2: Manual Installation

1. Download the latest release from the [Releases](https://github.com/alexoneill/homeassistant-ficollar/releases) page.
2. Copy the `custom_components/ficollar` directory to your Home Assistant configuration directory under `<config>/custom_components/ficollar`.
3. Restart Home Assistant.

---

## Configuration

1. In Home Assistant, go to **Settings** > **Devices & Services**.
2. Click **Add Integration** and search for **Fi Collar**.
3. Enter your TryFi credentials:
   - **Email Address**: Your TryFi account email.
   - **Password**: Your TryFi account password.
   - **Update Interval (seconds)**: Desired polling frequency (default: 60s, min: 15s, max: 600s).
4. Click **Submit**. All dogs associated with your account will be automatically discovered and added as individual devices.

### Options

You can adjust the polling interval anytime:
1. Go to **Settings** > **Devices & Services** > **Fi Collar**.
2. Click **Configure** and update the interval in seconds.

---

## Entities Provided

Each registered pet creates a dedicated Device in Home Assistant with the following entities:

| Platform | Entity | Description |
| :--- | :--- | :--- |
| `device_tracker` | `Location` | Real-time GPS coordinates, accuracy, and safe zone |
| `sensor` | `Battery` | Collar battery level (%) |
| `sensor` | `Steps Today` | Current day step count (total increasing) |
| `sensor` | `Step Goal` | Daily target step count |
| `sensor` | `Step Goal Progress` | Percentage of daily step goal reached (%) |
| `sensor` | `Goal Streak` | Consecutive days reaching step goal |
| `sensor` | `Sleep Duration` | Overnight sleep duration (hours) |
| `sensor` | `Nap Duration` | Daytime nap duration (hours) |
| `sensor` | `Total Rest` | Total resting duration (hours) |
| `sensor` | `Last Walk Distance` | Distance covered during the last walk (km) |
| `sensor` | `Last Walk Steps` | Step count for the last recorded walk |
| `sensor` | `Ongoing Walk Steps` | Steps in an ongoing active walk |
| `sensor` | `Weight` | Dog's recorded weight |
| `binary_sensor` | `Online` | True when collar is communicating with Fi cloud |
| `binary_sensor` | `Out of Battery` | True if collar battery has depleted |
| `binary_sensor` | `Lost Mode` | True if Lost Dog Mode is currently activated |
| `binary_sensor` | `Walking` | True when an active walk is detected |
| `binary_sensor` | `Stale Connection` | True if collar telemetry is delayed or stale |
| `light` | `Collar LED` | Toggle collar LED on/off |
| `switch` | `Lost Dog Mode` | Activate emergency lost dog mode |

---

## Example Automation

### Flash Collar LED if Dog Leaves Safe Zone at Night

```yaml
alias: "Dog left home at night - Turn on Collar LED"
trigger:
  - platform: state
    entity_id: device_tracker.milo_location
    from: "home"
condition:
  - condition: state
    entity_id: sun.sun
    state: "below_horizon"
action:
  - service: light.turn_on
    target:
      entity_id: light.milo_collar_led
  - service: notify.notify
    data:
      title: "Milo Alert"
      message: "Milo left home! Collar light has been turned on."
```

---

## Development & Testing

This integration uses `pytest-homeassistant-custom-component` for testing against the official Home Assistant Core async environment.

### Local Setup
```bash
# Create and activate a Python 3.12 virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install test runner and dependencies
pip install pytest-homeassistant-custom-component "pyficollar>=0.1.1"

# Run tests
pytest tests
```

---

## Releasing

Releases are 100% tag-driven. When a `v*` tag is pushed:
1. GitHub Actions extracts the tag version.
2. Injects the version into `custom_components/ficollar/manifest.json`.
3. Packages `ficollar.zip` and attaches it to the release.
4. Publishes a GitHub Release with auto-generated release notes.

To cut a new release:
```bash
git tag v0.1.1
git push origin v0.1.1
```

---

## Disclaimer

This integration is an independent open-source project and is not affiliated, sponsored, or endorsed by Barking Labs Corp. (TryFi). All product and company names are trademarks™ or registered® trademarks of their respective holders.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
