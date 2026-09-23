"""Tests for the Fi Collar config flow using pytest-homeassistant-custom-component."""

from __future__ import annotations

from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ficollar.config_flow import _validate_credentials
from custom_components.ficollar.const import (
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pyficollar.exceptions import FiAuthError, FiNetworkError
from pyficollar.models import User


async def test_validate_credentials_accesses_property() -> None:
    """Verify _validate_credentials accesses current_user_id property without calling it."""
    with patch("custom_components.ficollar.config_flow.FiClient") as mock_client_cls:
        mock_client = MagicMock()
        # current_user_id is a property returning a string, not a callable!
        type(mock_client).current_user_id = PropertyMock(return_value="user_abc_123")
        mock_client.get_current_user.return_value = User(
            id="user_abc_123",
            email="test@example.com",
            first_name="Alex",
            last_name="O'Neill",
        )
        mock_client_cls.return_value = mock_client

        user_id, display_name = _validate_credentials("test@example.com", "secret")

        assert user_id == "user_abc_123"
        assert display_name == "Alex O'Neill"
        mock_client.login.assert_called_once_with(
            email="test@example.com", password="secret", save_session=False
        )


async def test_form_user_step_initial(hass: HomeAssistant) -> None:
    """Test initial user step displays the configuration form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}


async def test_form_user_step_success(hass: HomeAssistant, mock_fi_client: MagicMock) -> None:
    """Test successful configuration flow creates an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "secret_password",
            CONF_SCAN_INTERVAL: 45,
        },
    )

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Fi Collar (Alex O'Neill)"
    assert result2["data"] == {
        CONF_EMAIL: "test@example.com",
        CONF_PASSWORD: "secret_password",
        CONF_SCAN_INTERVAL: 45,
    }
    assert result2["options"] == {
        CONF_SCAN_INTERVAL: 45,
    }


async def test_form_user_step_invalid_auth(hass: HomeAssistant, mock_fi_client: MagicMock) -> None:
    """Test invalid credentials error in config flow."""
    mock_fi_client.login.side_effect = FiAuthError("Bad credentials")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "wrong_password",
            CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
        },
    )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_form_user_step_cannot_connect(
    hass: HomeAssistant, mock_fi_client: MagicMock
) -> None:
    """Test network error during config flow."""
    mock_fi_client.login.side_effect = FiNetworkError("Network unreachable")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "secret_password",
            CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
        },
    )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_user_step_already_configured(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_fi_client: MagicMock
) -> None:
    """Test abort when account is already configured."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "secret_password",
            CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
        },
    )

    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "already_configured"


async def test_options_flow(hass: HomeAssistant, mock_config_entry: MockConfigEntry) -> None:
    """Test modifying scan interval via options flow."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_SCAN_INTERVAL: 120},
    )

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["data"] == {CONF_SCAN_INTERVAL: 120}
