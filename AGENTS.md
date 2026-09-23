# AGENTS.md

Guidance and instructions for AI coding agents working on the `homeassistant-ficollar` codebase.

---

## 1. Project Overview

`homeassistant-ficollar` is an official HACS-compliant custom integration for Home Assistant providing real-time tracking, sensors, controls, and telemetry for the **Fi Smart Dog Collar** (Series 2 & Series 3).

The integration is powered by the [`pyficollar`](https://github.com/alexoneill/pyficollar) Python client library.

### Core Architecture & Design Principles
- **Coordinator-Centric (`DataUpdateCoordinator`)**: A single `FiDataUpdateCoordinator` handles authenticated communication and periodic polling to minimize requests to TryFi's GraphQL backend. All platforms (`device_tracker`, `sensor`, `binary_sensor`, `light`, `switch`) consume cached state from this coordinator.
- **Official Home Assistant Testing**: Tested using `pytest-homeassistant-custom-component` with the Home Assistant Core async testing engine and state registry.
- **Tag-Driven Automated Releases**: Versioning is 100% driven by Git tags (`v*`). The GitHub Actions release workflow automatically syncs the tag version into `manifest.json`, builds the `ficollar.zip` release asset, publishes the GitHub Release, and commits the version bump to `main`.
- **HACS & Hassfest Compliant**: Adheres to HACS and Home Assistant architectural standards (brand assets, English translations, options flow, reauth flow, strict manifest rules).

---

## 2. Directory Layout

```
.
├── custom_components/
│   └── ficollar/
│       ├── __init__.py           # Component setup, platform dispatching, coordinator init
│       ├── manifest.json         # Integration manifest, domain, requirements, version
│       ├── const.py              # Constants (DOMAIN, config keys, intervals, attributes)
│       ├── config_flow.py        # Config flow (user setup, reauth, options flow)
│       ├── coordinator.py        # FiDataUpdateCoordinator & PetCoordinatorData container
│       ├── entity.py             # FiEntity base class inheriting from CoordinatorEntity
│       ├── device_tracker.py     # GPS tracker platform (lat, lon, accuracy, safe place)
│       ├── sensor.py             # Sensor platform (battery, steps, goals, sleep, walks)
│       ├── binary_sensor.py      # Binary sensor platform (online, out_of_battery, walking)
│       ├── light.py              # Light platform (collar LED on/off control)
│       ├── switch.py             # Switch platform (Lost Dog Mode activation)
│       ├── strings.json          # Translation strings source
│       ├── translations/
│       │   └── en.json           # English localization
│       └── brand/                # Brand assets (icon.png, logo.png, @2x variants)
├── tests/
│   ├── __init__.py               # Tests marker
│   ├── conftest.py               # pytest-homeassistant fixtures (mock_fi_client, sample models)
│   ├── test_config_flow.py       # Config flow, reauth, options, credential validation tests
│   ├── test_coordinator.py       # Coordinator polling and error handling tests
│   ├── test_init.py              # Component setup and teardown lifecycle tests
│   ├── test_entities.py          # State registry and service call tests (light, switch, GPS)
│   └── test_manifest.py          # HACS and Hassfest metadata validation tests
├── .github/
│   └── workflows/
│       ├── test.yml              # Multi-version CI test matrix (Python 3.12, 3.13)
│       ├── validate.yml          # Hassfest & HACS validation workflows
│       └── release.yml           # Automated tag-driven HACS release workflow
├── hacs.json                     # HACS repository configuration (zip_release enabled)
├── pytest.ini                    # pytest asyncio configuration
├── README.md                     # User documentation and setup guide
└── LICENSE                       # MIT License
```

---

## 3. Key Modules & Important Gotchas

### `custom_components/ficollar/config_flow.py`
- Handles user onboarding, duplicate prevention via `user_id` unique ID, and options reconfiguration.
- **CRITICAL GOTCHA**: In `pyficollar.client.FiClient`, `current_user_id` is a Python **`@property`**, NOT a callable method:
  ```python
  # CORRECT:
  user_id = client.current_user_id or email.lower()

  # WRONG (causes TypeError: 'str' object is not callable):
  user_id = client.current_user_id()
  ```
- Always call `super().__init__()` in `FiCollarConfigFlow.__init__`.

### `custom_components/ficollar/coordinator.py`
- `PetCoordinatorData` is a typed dataclass storing:
  - `pet: Pet`
  - `live_state: PetLiveState | None`
  - `activity: ActivitySummary | None`
  - `rest: RestSummary | None`
  - `last_walk: Walk | None`
- Polling catches `FiAuthError` and raises `ConfigEntryAuthFailed` (triggering HA's reauth flow), and catches `FiNetworkError` / `FiError` and raises `UpdateFailed`.

### `custom_components/ficollar/entity.py`
- Base class `FiEntity(CoordinatorEntity[FiDataUpdateCoordinator])`.
- Automatically links entities to the pet's HA Device via `device_info`:
  - `identifiers = {(DOMAIN, pet_id)}`
  - `manufacturer = "Barking Labs (TryFi)"`
  - `model = pet.device.module_id`

---

## 4. Development & Testing Workflow

Home Assistant 2024/2025 runs on Python 3.12 or 3.13.

### Setting Up Local Environment
```bash
# Create Python 3.12 virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install test framework and pyficollar (editable or from PyPI)
pip install pytest-homeassistant-custom-component -e ../pyficollar
```

### Running Tests
Execute the complete test suite:
```bash
pytest tests
```

### Testing Guidelines
- Never make live network calls to `api.tryfi.com` in tests.
- Always use the `hass: HomeAssistant` fixture from `pytest-homeassistant-custom-component`.
- Keep `pytest.ini` configured with:
  ```ini
  [pytest]
  asyncio_mode = auto
  asyncio_default_fixture_loop_scope = function
  testpaths = tests
  ```

---

## 5. Releases & Version Management

This repository uses **Tag-Driven Releases**. Never manually edit `"version"` in `manifest.json`.

### Cutting a New Release
To publish a new HACS release:
```bash
# Tag the release (must use SemVer with a leading 'v')
git tag v0.1.1
git push origin v0.1.1

# Or using the GitHub CLI:
gh release create v0.1.1 --generate-notes
```

### What the Release Workflow (`.github/workflows/release.yml`) Does:
1. Triggers on `v*` tag push.
2. Extracts the version number (e.g. `0.1.1` from `v0.1.1`).
3. Safely updates `"version": "0.1.1"` in `custom_components/ficollar/manifest.json`.
4. Packages `ficollar.zip` containing `custom_components/ficollar/` (excluding caches and `.DS_Store`).
5. Commits and pushes the version bump to `main` with `[skip ci]`.
6. Publishes the GitHub Release with generated release notes and attaches `ficollar.zip`.
7. HACS downloads `ficollar.zip` and serves the update to Home Assistant users.

---

## 6. Continuous Integration (CI)

- **[`.github/workflows/test.yml`](.github/workflows/test.yml)**: Runs unit tests in a multi-version Python matrix (3.12, 3.13) on every push and pull request.
- **[`.github/workflows/validate.yml`](.github/workflows/validate.yml)**:
  - `Validate with Hassfest`: Official Home Assistant validation for manifest, services, and requirements.
  - `Validate with HACS`: Official HACS compliance check.
- **[`.github/workflows/release.yml`](.github/workflows/release.yml)**: Automated release pipeline on `v*` tags.
