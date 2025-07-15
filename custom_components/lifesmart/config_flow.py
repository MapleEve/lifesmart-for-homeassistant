import asyncio
import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import (
    CONF_TYPE,
    CONF_HOST,
    CONF_PORT,
    CONF_REGION,
    CONF_USERNAME,
    CONF_PASSWORD,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady, ConfigEntryAuthFailed
from homeassistant.helpers import selector
from homeassistant.helpers.selector import SelectSelectorMode

from . import lifesmart_protocol, LifeSmartClient
from .const import (
    CONF_AI_INCLUDE_AGTS,
    CONF_AI_INCLUDE_ITEMS,
    CONF_EXCLUDE_AGTS,
    CONF_EXCLUDE_ITEMS,
    CONF_LIFESMART_APPKEY,
    CONF_LIFESMART_APPTOKEN,
    CONF_LIFESMART_USERID,
    CONF_LIFESMART_USERTOKEN,
    CONF_LIFESMART_USERPASSWORD,
    CONF_LIFESMART_AUTH_METHOD,
    DOMAIN,
    LIFESMART_REGION_OPTIONS,
)

_LOGGER = logging.getLogger(__name__)

# 基础协议选择 Schema
PROTOCOL_SCHEMA = vol.Schema(
    {
        vol.Required(
            CONF_TYPE,
            default=config_entries.CONN_CLASS_CLOUD_PUSH,
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[
                    {
                        "label": "本地 (Local)",
                        "value": config_entries.CONN_CLASS_LOCAL_PUSH,
                    },
                    {
                        "label": "云端 (Cloud)",
                        "value": config_entries.CONN_CLASS_CLOUD_PUSH,
                    },
                ],
                translation_key="protocol_selector",
                mode=SelectSelectorMode.DROPDOWN,
                custom_value=False,  # 强制不允许自定义输入
            )
        )
    }
)


def build_region_selector(default="cn2") -> dict:
    """构建地区下拉选择器"""
    return {
        vol.Required(CONF_REGION, default=default): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=LIFESMART_REGION_OPTIONS,
                mode=SelectSelectorMode.DROPDOWN,
                custom_value=False,  # 强制不允许自定义输入
            )
        )
    }


def build_cloud_schema(config_data: dict = None) -> vol.Schema:
    """构建云端配置 Schema"""
    config_data = config_data or {}
    schema_elements = {
        vol.Required(
            CONF_LIFESMART_APPKEY, default=config_data.get(CONF_LIFESMART_APPKEY, "")
        ): str,
        vol.Required(
            CONF_LIFESMART_APPTOKEN,
            default=config_data.get(CONF_LIFESMART_APPTOKEN, ""),
        ): str,
        vol.Optional(
            CONF_LIFESMART_USERTOKEN,
            default=config_data.get(CONF_LIFESMART_USERTOKEN, ""),
        ): str,
        vol.Required(
            CONF_LIFESMART_USERPASSWORD,
            default=config_data.get(CONF_LIFESMART_USERPASSWORD, ""),
        ): str,
        vol.Required(
            CONF_LIFESMART_USERID, default=config_data.get(CONF_LIFESMART_USERID, "")
        ): str,
        **build_region_selector(config_data.get(CONF_REGION, "cn2")),
        vol.Optional(
            CONF_EXCLUDE_ITEMS, default=config_data.get(CONF_EXCLUDE_ITEMS, "")
        ): str,
        vol.Optional(
            CONF_EXCLUDE_AGTS, default=config_data.get(CONF_EXCLUDE_AGTS, "")
        ): str,
        vol.Optional(
            CONF_AI_INCLUDE_AGTS, default=config_data.get(CONF_AI_INCLUDE_AGTS, "")
        ): str,
        vol.Optional(
            CONF_AI_INCLUDE_ITEMS, default=config_data.get(CONF_AI_INCLUDE_ITEMS, "")
        ): str,
    }
    return vol.Schema(schema_elements)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]):
    """Validate the user input allows us to connect."""
    try:
        lifesmart_client = LifeSmartClient(
            hass,
            data.get(CONF_REGION),
            data.get(CONF_LIFESMART_APPKEY),
            data.get(CONF_LIFESMART_APPTOKEN),
            data.get(CONF_LIFESMART_USERTOKEN),
            data.get(CONF_LIFESMART_USERID),
            user_password=data.get(CONF_LIFESMART_USERPASSWORD),
        )

        # 如果提供了密码，则执行登录流程
        if data.get(CONF_LIFESMART_USERPASSWORD):
            _LOGGER.info("Attempting login with user password...")
            login_success = await lifesmart_client.login_async()
            if not login_success:
                _LOGGER.error("Authentication failed with provided password.")
                raise ConfigEntryAuthFailed("invalid_auth")
            _LOGGER.info("Login successful, obtained user token.")
            # 使用获取到的token更新data字典
            data[CONF_LIFESMART_USERTOKEN] = lifesmart_client._usertoken

        devices = await lifesmart_client.get_all_device_async()

        if not isinstance(devices, list):
            _LOGGER.error("API did not return a valid device list.")
            raise ConfigEntryAuthFailed("invalid_response")
        if len(devices) == 0:
            _LOGGER.warning("No devices found for this user.")

        # 如果认证方式是密码，我们现在需要保存密码
        # 但我们不应该保存临时的 token
        if data.get(CONF_LIFESMART_AUTH_METHOD) == "password":
            data.pop(CONF_LIFESMART_USERTOKEN, None)
        else:
            # 如果是token认证，则移除密码字段（即使它为空）
            data.pop(CONF_LIFESMART_USERPASSWORD, None)

        return {
            "title": f"LifeSmart ({data[CONF_LIFESMART_USERID]})",
            "data": data,
        }
    except ConfigEntryAuthFailed:
        raise
    except Exception as e:
        _LOGGER.error("Unknown error during validation: %s", str(e), exc_info=True)
        raise ConfigEntryNotReady("Unknown error during validation") from e


async def validate_local_input(
    hass: HomeAssistant, data: dict[str, Any]
) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    try:
        dev = lifesmart_protocol.LifeSmartLocalClient(
            data[CONF_HOST],
            data[CONF_PORT],
            data[CONF_USERNAME],
            data[CONF_PASSWORD],
        )
        await dev.check_login()
    except Exception as e:
        _LOGGER.error("Local input error: %s", str(e), exc_info=True)
        raise ConfigEntryNotReady("Local input error") from e
    return data


def get_unique_id(wiser_id: str):
    """Generate Unique ID for Hub."""
    return str(f"{DOMAIN}-{wiser_id}")


@config_entries.HANDLERS.register(DOMAIN)
class LifeSmartConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """处理生命周期核心配置流程"""

    VERSION = 1
    _reauth_entry: config_entries.ConfigEntry | None = None

    def __init__(self) -> None:
        """初始化配置流"""
        super().__init__()
        self.config_data = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """主入口步骤"""
        errors = {}
        if user_input is not None:
            connection_type = user_input[CONF_TYPE]
            if connection_type == config_entries.CONN_CLASS_LOCAL_PUSH:
                return await self.async_step_local()
            return await self.async_step_cloud()

        return self.async_show_form(
            step_id="user",
            data_schema=PROTOCOL_SCHEMA,
            errors=errors,
        )

    async def async_step_local(self, user_input: dict[str, Any] | None = None):
        """本地连接配置步骤"""
        errors = {}
        schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=""): str,
                vol.Required(CONF_PORT, default=8888): int,
                vol.Required(CONF_USERNAME, default="admin"): str,
                vol.Required(CONF_PASSWORD, default="admin"): str,
            }
        )

        if user_input is None:
            return self.async_show_form(step_id="local", data_schema=schema)

        try:
            await validate_local_input(self.hass, user_input)
            return self.async_create_entry(
                title=f"Local Hub ({user_input[CONF_HOST]})",
                data={**user_input, CONF_TYPE: config_entries.CONN_CLASS_LOCAL_PUSH},
            )
        except (asyncio.TimeoutError, ConnectionRefusedError) as e:
            errors["base"] = "cannot_connect"
            _LOGGER.error("Local connection error: %s", str(e))
        except asyncio.InvalidStateError as e:
            errors["base"] = "invalid_auth"
            _LOGGER.error("Local Auth error: %s", str(e))
        except Exception as e:
            errors["base"] = "unknown"
            _LOGGER.error("Unexpected error: %s", str(e), exc_info=True)

        return self.async_show_form(
            step_id="local",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_cloud(self, user_input: dict[str, Any] | None = None):
        """[第一步] 云端连接配置：基础信息和认证方式选择"""
        errors = {}

        # 如果是从 reauth 或 options 流程过来，预填充数据
        config_data = {}
        if self._reauth_entry:
            config_data = self._reauth_entry.data.copy()

        if user_input is not None:
            # 将用户输入暂存，并进入下一步
            self.config_data.update(user_input)
            auth_method = user_input.get(CONF_LIFESMART_AUTH_METHOD)
            if auth_method == "token":
                return await self.async_step_cloud_token()
            elif auth_method == "password":
                return await self.async_step_cloud_password()

        # 定义第一步的表单
        cloud_schema = vol.Schema(
            {
                vol.Required(
                    CONF_LIFESMART_APPKEY,
                    default=config_data.get(CONF_LIFESMART_APPKEY, ""),
                ): str,
                vol.Required(
                    CONF_LIFESMART_APPTOKEN,
                    default=config_data.get(CONF_LIFESMART_APPTOKEN, ""),
                ): str,
                vol.Required(
                    CONF_LIFESMART_USERID,
                    default=config_data.get(CONF_LIFESMART_USERID, ""),
                ): str,
                **build_region_selector(config_data.get(CONF_REGION, "cn2")),
                vol.Required(
                    CONF_LIFESMART_AUTH_METHOD, default="token"
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"label": "User Token", "value": "token"},
                            {"label": "User Password", "value": "password"},
                        ],
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="cloud",
            data_schema=cloud_schema,
            errors=errors,
        )

    async def async_step_cloud_token(self, user_input: dict[str, Any] | None = None):
        """[第二步 - Token] 输入 User Token"""
        errors = {}
        if user_input is not None:
            self.config_data.update(user_input)
            try:
                # 验证并创建条目
                validation_result = await validate_input(self.hass, self.config_data)
                return self.async_create_entry(
                    title=validation_result["title"], data=validation_result["data"]
                )
            except ConfigEntryAuthFailed:
                errors["base"] = "invalid_auth"
            except Exception:
                errors["base"] = "unknown"

        token_schema = vol.Schema(
            {
                vol.Required(CONF_LIFESMART_USERTOKEN): str,
            }
        )

        return self.async_show_form(
            step_id="cloud_token",
            data_schema=token_schema,
            errors=errors,
        )

    async def async_step_cloud_password(self, user_input: dict[str, Any] | None = None):
        """[第二步 - Password] 输入 User Password"""
        errors = {}
        if user_input is not None:
            self.config_data.update(user_input)
            try:
                # 验证并创建条目
                validation_result = await validate_input(self.hass, self.config_data)
                return self.async_create_entry(
                    title=validation_result["title"], data=validation_result["data"]
                )
            except ConfigEntryAuthFailed:
                errors["base"] = "invalid_auth"
            except Exception:
                errors["base"] = "unknown"

        password_schema = vol.Schema(
            {
                vol.Required(CONF_LIFESMART_USERPASSWORD): selector.TextSelector(
                    selector.TextSelectorConfig(type="password")
                ),
            }
        )

        return self.async_show_form(
            step_id="cloud_password",
            data_schema=password_schema,
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: dict[str, Any] | None = None):
        """处理重新认证流程"""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_cloud()


class LifeSmartOptionsFlowHandler(config_entries.OptionsFlow):
    """配置选项流处理"""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """初始化选项流"""
        self.config_entry = config_entry
        self.current_data = {**config_entry.data, **config_entry.options}

    async def async_step_init(self, user_input=None):
        """主选项步骤"""
        return self.async_show_menu(
            step_id="init",
            menu_options=["main_params"],
            description_placeholders={
                "current_user": self.config_entry.data.get(CONF_LIFESMART_USERID)
            },
        )

    async def async_step_main_params(self, user_input=None):
        """主要参数配置步骤"""
        schema = build_cloud_schema(self.current_data)
        return self.async_show_form(
            step_id="main_params",
            data_schema=schema,
            description="Main parameters",
        )
