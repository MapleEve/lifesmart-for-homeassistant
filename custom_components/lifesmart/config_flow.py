import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME, CONF_REGION
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import selector

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
    LIFESMART_REGION_OPTIONS,
)
from .lifesmart_client import LifeSmartClient

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_LIFESMART_APPKEY): str,
        vol.Required(CONF_LIFESMART_APPTOKEN): str,
        vol.Required(CONF_LIFESMART_USERTOKEN): str,
        vol.Required(CONF_LIFESMART_USERID): str,
        vol.Required(CONF_REGION): selector(LIFESMART_REGION_OPTIONS),
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
    region = data[CONF_REGION]
    # exclude_devices = data[CONF_EXCLUDE_ITEMS]
    # exclude_hubs = data[CONF_EXCLUDE_AGTS]
    # ai_include_hubs = data[CONF_AI_INCLUDE_AGTS]
    # ai_include_items = data[CONF_AI_INCLUDE_ITEMS]

    lifesmart_client = LifeSmartClient(
        region,
        app_key,
        app_token,
        user_token,
        user_id,
    )

    await lifesmart_client.get_all_device_async()

    return {"title": f"User Id {user_id}", "unique_id": app_key}


def get_unique_id(wiser_id: str):
    """Generate a unique id."""
    return str(f"{DOMAIN}-{wiser_id}")


@config_entries.HANDLERS.register(DOMAIN)
class LifeSmartConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow"""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_PUSH

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.discovery_info = {}

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return LifeSmartOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle a flow initiated by the user."""
        errors = {}
        if user_input is not None:
            try:
                validated = await validate_input(self.hass, user_input)
            except Exception:
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

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle a config flow."""
        errors = {}
        if user_input is not None:
            try:
                validated = await validate_input(self.hass, user_input)
            except Exception:
                _LOGGER.warning("Input validation error")

            if "base" not in errors:
                # Add hub name to config
                user_input[CONF_NAME] = validated["title"]

                return self.async_create_entry(
                    title=validated["title"], data=user_input
                )
        schema = {
            vol.Required(
                CONF_LIFESMART_APPKEY,
                default=self.config_entry.data.get(CONF_LIFESMART_APPKEY),
            ): str,
            vol.Required(
                CONF_LIFESMART_APPTOKEN,
                default=self.config_entry.data.get(CONF_LIFESMART_APPTOKEN),
            ): str,
            vol.Required(
                CONF_LIFESMART_USERID,
                default=self.config_entry.data.get(CONF_LIFESMART_USERID),
            ): str,
            vol.Required(
                CONF_LIFESMART_USERTOKEN,
                default=self.config_entry.data.get(CONF_LIFESMART_USERTOKEN),
            ): str,
            vol.Required(
                CONF_REGION,
                default=self.config_entry.data.get(CONF_REGION),
            ): selector(LIFESMART_REGION_OPTIONS),
            vol.Optional(
                CONF_EXCLUDE_ITEMS,
                default=self.config_entry.data.get(CONF_EXCLUDE_ITEMS, ""),
            ): str,
            vol.Optional(
                CONF_EXCLUDE_AGTS,
                default=self.config_entry.data.get(CONF_EXCLUDE_AGTS, ""),
            ): str,
            vol.Optional(
                CONF_AI_INCLUDE_AGTS,
                default=self.config_entry.data.get(CONF_AI_INCLUDE_AGTS, ""),
            ): str,
            vol.Optional(
                CONF_AI_INCLUDE_ITEMS,
                default=self.config_entry.data.get(CONF_AI_INCLUDE_ITEMS, ""),
            ): str,
        }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(schema),
            errors=errors,
        )

    async def async_step_init(self, user_input=None):
        """Handle options flow."""
        if user_input is not None:
            options = self.config_entry.options | user_input
            return self.async_create_entry(title="", data=options)

        schema = {
            vol.Required(
                CONF_LIFESMART_APPKEY,
                default=self.config_entry.data.get(CONF_LIFESMART_APPKEY),
            ): str,
            vol.Required(
                CONF_LIFESMART_APPTOKEN,
                default=self.config_entry.data.get(CONF_LIFESMART_APPTOKEN),
            ): str,
            vol.Required(
                CONF_LIFESMART_USERID,
                default=self.config_entry.data.get(CONF_LIFESMART_USERID),
            ): str,
            vol.Required(
                CONF_LIFESMART_USERTOKEN,
                default=self.config_entry.data.get(CONF_LIFESMART_USERTOKEN),
            ): str,
            vol.Required(
                CONF_REGION,
                default=self.config_entry.data.get(CONF_REGION),
            ): selector(LIFESMART_REGION_OPTIONS),
            vol.Optional(
                CONF_EXCLUDE_ITEMS,
                default=self.config_entry.data.get(CONF_EXCLUDE_ITEMS, ""),
            ): str,
            vol.Optional(
                CONF_EXCLUDE_AGTS,
                default=self.config_entry.data.get(CONF_EXCLUDE_AGTS, ""),
            ): str,
            vol.Optional(
                CONF_AI_INCLUDE_AGTS,
                default=self.config_entry.data.get(CONF_AI_INCLUDE_AGTS, ""),
            ): str,
            vol.Optional(
                CONF_AI_INCLUDE_ITEMS,
                default=self.config_entry.data.get(CONF_AI_INCLUDE_ITEMS, ""),
            ): str,
        }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(schema),
        )
