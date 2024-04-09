from typing import Any
import voluptuous as vol
from .lifesmart_client import LifeSmartClient
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from homeassistant import config_entries, exceptions
from homeassistant.const import (
    CONF_NAME,
    CONF_URL,
)

import logging

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
)


async def validate_input(hass, data):
    """Validate the user input allows us to connect."""

    app_key = data[CONF_LIFESMART_APPKEY]
    app_token = data[CONF_LIFESMART_APPTOKEN]
    user_token = data[CONF_LIFESMART_USERTOKEN]
    user_id = data[CONF_LIFESMART_USERID]
    baseurl = data[CONF_URL]
    # exclude_devices = data[CONF_EXCLUDE_ITEMS]
    # exclude_hubs = data[CONF_EXCLUDE_AGTS]
    # ai_include_hubs = data[CONF_AI_INCLUDE_AGTS]
    # ai_include_items = data[CONF_AI_INCLUDE_ITEMS]

    lifesmart_client = LifeSmartClient(
        baseurl,
        app_key,
        app_token,
        user_token,
        user_id,
    )

    devices = await lifesmart_client.get_all_device_async()

    return {"title": f"User Id {user_id}", "unique_id": app_key}


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
            try:
                validated = await validate_input(self.hass, user_input)
            except:
                _LOGGER.warning("Input validation error")

            if "base" not in errors:
                await self.async_set_unique_id(validated["unique_id"])
                self._abort_if_unique_id_configured()

                # Add hub name to config
                user_input[CONF_NAME] = validated["title"]

                return self.async_create_entry(
                    title=validated["title"], data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self.discovery_info or DATA_SCHEMA,
            errors=errors,
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
