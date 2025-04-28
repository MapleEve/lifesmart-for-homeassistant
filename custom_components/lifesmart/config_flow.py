import asyncio
import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import (
    CONF_NAME,
    CONF_URL,
    CONF_TYPE,
    CONF_HOST,
    CONF_PORT,
    CONF_USERNAME,
    CONF_PASSWORD,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady, ConfigEntryAuthFailed
from homeassistant.helpers import selector
from homeassistant.util import aiohttp

from . import lifesmart_protocol, LifeSmartClient
from .const import (
    CONF_AI_INCLUDE_AGTS,
    CONF_AI_INCLUDE_ITEMS,
    CONF_EXCLUDE_AGTS,
    CONF_EXCLUDE_ITEMS,
    CONF_LIFESMART_APPTOKEN,
    CONF_LIFESMART_USERID,
    CONF_LIFESMART_USERTOKEN,
    DOMAIN,
    CONF_LIFESMART_APPKEY,
)

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(
            CONF_TYPE, default=config_entries.CONN_CLASS_CLOUD_PUSH
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[
                    {"label": "Local", "value": config_entries.CONN_CLASS_LOCAL_PUSH},
                    {"label": "Cloud", "value": config_entries.CONN_CLASS_CLOUD_PUSH},
                ],
                translation_key="protocol_selector",  # 多语言支持
                mode=selector.SelectSelectorMode.DROPDOWN,  # 明确指定下拉模式
            )
        )
    }
)


async def validate_input(hass, data):
    """Validate the user input allows us to connect."""

    try:
        lifesmart_client = LifeSmartClient(
            data[CONF_URL],
            data[CONF_LIFESMART_APPKEY],
            data[CONF_LIFESMART_APPTOKEN],
            data[CONF_LIFESMART_USERTOKEN],
            data[CONF_LIFESMART_USERID],
        )

        devices = await lifesmart_client.get_all_device_async()

        # 添加设备列表验证
        if not isinstance(devices, list):
            raise ValueError(f"Invalid API return: {type(devices)}")
        if len(devices) == 0:
            _LOGGER.warning("No devices found")

        return {
            "title": f"User Id {data[CONF_LIFESMART_USERID]}",
            "unique_id": data[CONF_LIFESMART_APPKEY],
        }

    except aiohttp.ClientError as e:
        _LOGGER.error("Network error: %s", str(e))
        raise ConfigEntryAuthFailed("Cannot connect to the server")
    except ValueError as e:
        _LOGGER.error("API Value validate error: %s", str(e))
        raise ConfigEntryNotReady("Invalid API return")
    except Exception as e:
        _LOGGER.error("Unknown error: %s", str(e), exc_info=True)
        raise ConfigEntryNotReady("Unknown error") from e


async def validate_local_input(
    hass: HomeAssistant, data: dict[str, Any]
) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    try:
        dev = lifesmart_protocol.LifeSmartLocalClient(
            data[CONF_HOST], data[CONF_PORT], data[CONF_USERNAME], data[CONF_PASSWORD]
        )
        await dev.check_login()
    except Exception as e:
        raise e
    return data


def get_unique_id(wiser_id: str):
    return str(f"{DOMAIN}-{wiser_id}")


@config_entries.HANDLERS.register(DOMAIN)
class LifeSmartConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """
    LifeSmartConfigFlowHandler configuration method.
    """

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_PUSH

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.discovery_info = {}

    async def async_step_user(self, user_input=None):
        """
        Handle a config flow.
        """
        errors = {}
        if user_input is not None:
            if user_input[CONF_TYPE] == config_entries.CONN_CLASS_LOCAL_PUSH:
                return await self.async_step_local(None)
            else:
                return await self.async_step_cloud(None)

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_local(self, user_input=None):
        STEP_USER_DATA_SCHEMA = vol.Schema(
            {
                vol.Required(CONF_HOST, default=""): str,
                vol.Required(CONF_PORT, default=8888): int,
                vol.Required(CONF_USERNAME, default="admin"): str,
                vol.Required(CONF_PASSWORD, default="admin"): str,
            }
        )
        if user_input is None:
            return self.async_show_form(
                step_id="local", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            data = await validate_local_input(self.hass, user_input)
        except (asyncio.TimeoutError, ConnectionRefusedError) as e:
            errors["base"] = "cannot_connect"
            _LOGGER.error("Local Connection error: %s", str(e))
        except asyncio.InvalidStateError as e:
            errors["base"] = "invalid_auth"
            _LOGGER.error("Local Auth error: %s", str(e))
        except Exception as e:
            errors["base"] = "unknown"
            _LOGGER.error("Local Unexpected exception: %s", str(e), exc_info=True)
        else:
            user_input[CONF_TYPE] = config_entries.CONN_CLASS_LOCAL_PUSH
            return self.async_create_entry(title=data[CONF_HOST], data=user_input)

        return self.async_show_form(
            step_id="local", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_cloud(self, user_input=None):
        # 获取动态设备列表
        errors = {}
        if user_input is not None:
            try:
                validated = await validate_input(self.hass, user_input)
            except ConfigEntryAuthFailed as e:
                errors["base"] = "invalid_auth"
                _LOGGER.error("Cloud Auth error: %s", str(e))
            except (asyncio.TimeoutError, ConnectionRefusedError) as e:
                errors["base"] = "cannot_connect"
                _LOGGER.error("Cloud Connection error: %s", str(e))
            except Exception as e:
                errors["base"] = "unknown"
                _LOGGER.error("Cloud Unexpected exception: %s", str(e), exc_info=True)

            if "base" not in errors:
                await self.async_set_unique_id(validated["unique_id"])
                self._abort_if_unique_id_configured()

                # Add hub name to config
                user_input[CONF_NAME] = validated["title"]

                user_input[CONF_TYPE] = config_entries.CONN_CLASS_CLOUD_PUSH
                return self.async_create_entry(
                    title=validated["title"], data=user_input
                )

        return self.async_show_form(
            step_id="cloud",
            data_schema=self.discovery_info
            or vol.Schema(
                {
                    vol.Optional(CONF_LIFESMART_APPKEY): str,
                    vol.Optional(CONF_LIFESMART_APPTOKEN): str,
                    vol.Optional(CONF_LIFESMART_USERTOKEN): str,
                    vol.Optional(CONF_LIFESMART_USERID): str,
                    vol.Required(CONF_URL): str,
                    vol.Optional(CONF_EXCLUDE_ITEMS): str,
                    vol.Optional(CONF_EXCLUDE_AGTS): str,
                    vol.Optional(CONF_AI_INCLUDE_AGTS): str,
                    vol.Optional(CONF_AI_INCLUDE_AGTS): str,
                    vol.Optional(CONF_AI_INCLUDE_ITEMS): str,
                }
            ),
        )


class LifeSmartOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle an option flow."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_main_params(self, user_input=None):
        """Handle options flow."""
        """
        if user_input is not None:
            if user_input[CONF_HOST]:
                data = {
                    CONF_HOST: user_input[CONF_HOST],
                    CONF_PASSWORD: self.config_entry.data[CONF_PASSWORD],
                    CONF_NAME: self.config_entry.data[CONF_NAME],
                }
                user_input.pop(CONF_HOST)
                self.hass.config_entries.async_update_entry(
                    self.config_entry, data=data
                )
            options = self.config_entry.options | user_input
            return self.async_create_entry(title="", data=options)
        """

        data_schema = {
            vol.Required(CONF_LIFESMART_APPKEY): str,
            vol.Required(CONF_LIFESMART_APPTOKEN): str,
            vol.Required(CONF_LIFESMART_USERTOKEN): str,
            vol.Required(CONF_LIFESMART_USERID): str,
            vol.Required(CONF_URL): str,
            vol.Optional(CONF_EXCLUDE_ITEMS): str,
            vol.Optional(CONF_EXCLUDE_AGTS): str,
            vol.Optional(CONF_AI_INCLUDE_AGTS): str,
            vol.Optional(CONF_AI_INCLUDE_ITEMS): str,
        }
        return self.async_show_form(
            step_id="main_params", data_schema=vol.Schema(data_schema)
        )

    async def async_step_init(self, user_input=None):
        """Handle options flow."""
        return self.async_show_menu(step_id="init", menu_options=["main_params"])
