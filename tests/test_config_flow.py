"""Tests for Fi Collar config flow and credential validation."""

from __future__ import annotations

import asyncio
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, PropertyMock, patch

REPO_ROOT = Path(__file__).parent.parent.resolve()
PYFICOLLAR_ROOT = (REPO_ROOT.parent / "pyficollar").resolve()
for p in [str(REPO_ROOT), str(PYFICOLLAR_ROOT)]:
    if Path(p).exists() and p not in sys.path:
        sys.path.insert(0, p)

try:
    from tests.mock_ha import setup_mock_homeassistant
except ModuleNotFoundError:
    from mock_ha import setup_mock_homeassistant

setup_mock_homeassistant()

from pyficollar.exceptions import FiAuthError, FiNetworkError
from pyficollar.models import User

from custom_components.ficollar.config_flow import (
    FiCollarConfigFlow,
    FiCollarOptionsFlow,
    _validate_credentials,
)
from custom_components.ficollar.const import (
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
)
from homeassistant.config_entries import ConfigEntry


class TestConfigFlow(unittest.TestCase):
    """Test Fi Collar config flow and credential validation."""

    def test_validate_credentials_success(self) -> None:
        """Verify _validate_credentials accesses current_user_id property without error."""
        with patch("custom_components.ficollar.config_flow.FiClient") as mock_client_cls:
            mock_client = MagicMock()
            type(mock_client).current_user_id = PropertyMock(return_value="user_abc_123")
            mock_client.get_current_user.return_value = User(
                id="user_abc_123",
                email="test@example.com",
                first_name="Alex",
                last_name="O'Neill",
            )
            mock_client_cls.return_value = mock_client

            user_id, display_name = _validate_credentials("test@example.com", "valid_pass")

            self.assertEqual(user_id, "user_abc_123")
            self.assertEqual(display_name, "Alex O'Neill")
            mock_client.login.assert_called_once_with(
                email="test@example.com", password="valid_pass", save_session=False
            )

    def test_validate_credentials_auth_error(self) -> None:
        """Verify _validate_credentials raises FiAuthError on bad credentials."""
        with patch("custom_components.ficollar.config_flow.FiClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.login.side_effect = FiAuthError("Invalid credentials")
            mock_client_cls.return_value = mock_client

            with self.assertRaises(FiAuthError):
                _validate_credentials("test@example.com", "wrong_pass")

    def test_validate_credentials_fallback_display_name(self) -> None:
        """Verify _validate_credentials falls back to email if user details fail."""
        with patch("custom_components.ficollar.config_flow.FiClient") as mock_client_cls:
            mock_client = MagicMock()
            type(mock_client).current_user_id = PropertyMock(return_value=None)
            mock_client.get_current_user.side_effect = Exception("User info unavailable")
            mock_client_cls.return_value = mock_client

            user_id, display_name = _validate_credentials("test@example.com", "pass")

            self.assertEqual(user_id, "test@example.com")
            self.assertEqual(display_name, "test@example.com")

    def test_async_step_user_show_form(self) -> None:
        """Verify initial form is shown when user_input is None."""
        flow = FiCollarConfigFlow()
        result = asyncio.run(flow.async_step_user(user_input=None))

        self.assertEqual(result["type"], "form")
        self.assertEqual(result["step_id"], "user")
        self.assertEqual(result["errors"], {})

    def test_async_step_user_success(self) -> None:
        """Verify successful entry creation from user input."""
        flow = FiCollarConfigFlow()
        user_input = {
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "secret_password",
            CONF_SCAN_INTERVAL: 45,
        }

        with patch(
            "custom_components.ficollar.config_flow._validate_credentials",
            return_value=("user_abc_123", "Alex O'Neill"),
        ):
            result = asyncio.run(flow.async_step_user(user_input=user_input))

            self.assertEqual(result["type"], "create_entry")
            self.assertEqual(result["title"], "Fi Collar (Alex O'Neill)")
            self.assertEqual(result["data"][CONF_EMAIL], "test@example.com")
            self.assertEqual(result["data"][CONF_PASSWORD], "secret_password")
            self.assertEqual(result["data"][CONF_SCAN_INTERVAL], 45)
            self.assertEqual(result["options"][CONF_SCAN_INTERVAL], 45)

    def test_async_step_user_invalid_auth(self) -> None:
        """Verify form is re-shown with invalid_auth error on FiAuthError."""
        flow = FiCollarConfigFlow()
        user_input = {
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "bad_password",
            CONF_SCAN_INTERVAL: 60,
        }

        with patch(
            "custom_components.ficollar.config_flow._validate_credentials",
            side_effect=FiAuthError("Unauthorized"),
        ):
            result = asyncio.run(flow.async_step_user(user_input=user_input))

            self.assertEqual(result["type"], "form")
            self.assertEqual(result["errors"], {"base": "invalid_auth"})

    def test_async_step_user_cannot_connect(self) -> None:
        """Verify form is re-shown with cannot_connect error on FiNetworkError."""
        flow = FiCollarConfigFlow()
        user_input = {
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "secret_password",
            CONF_SCAN_INTERVAL: 60,
        }

        with patch(
            "custom_components.ficollar.config_flow._validate_credentials",
            side_effect=FiNetworkError("Connection refused"),
        ):
            result = asyncio.run(flow.async_step_user(user_input=user_input))

            self.assertEqual(result["type"], "form")
            self.assertEqual(result["errors"], {"base": "cannot_connect"})

    def test_async_step_user_unknown_exception(self) -> None:
        """Verify form is re-shown with unknown error on unexpected exception."""
        flow = FiCollarConfigFlow()
        user_input = {
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "secret_password",
            CONF_SCAN_INTERVAL: 60,
        }

        with patch(
            "custom_components.ficollar.config_flow._validate_credentials",
            side_effect=RuntimeError("Something broke"),
        ):
            result = asyncio.run(flow.async_step_user(user_input=user_input))

            self.assertEqual(result["type"], "form")
            self.assertEqual(result["errors"], {"base": "unknown"})

    def test_options_flow(self) -> None:
        """Verify options flow displays form and updates scan interval."""
        entry = ConfigEntry(
            data={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "pass", CONF_SCAN_INTERVAL: 60},
            options={CONF_SCAN_INTERVAL: 60},
        )
        flow = FiCollarOptionsFlow(entry)

        form_result = asyncio.run(flow.async_step_init(user_input=None))
        self.assertEqual(form_result["type"], "form")
        self.assertEqual(form_result["step_id"], "init")

        create_result = asyncio.run(flow.async_step_init(user_input={CONF_SCAN_INTERVAL: 120}))
        self.assertEqual(create_result["type"], "create_entry")
        self.assertEqual(create_result["data"][CONF_SCAN_INTERVAL], 120)


if __name__ == "__main__":
    unittest.main()
