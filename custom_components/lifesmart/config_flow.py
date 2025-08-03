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
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult, AbortFlow
from homeassistant.exceptions import ConfigEntryNotReady, ConfigEntryAuthFailed
from homeassistant.helpers import selector
from homeassistant.helpers.selector import SelectSelectorMode

import custom_components.lifesmart.core.local_tcp_client
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
from .core.openapi_client import LifeSmartOAPIClient
from .diagnostics import get_error_advice
from .exceptions import LifeSmartAuthError
from .helpers import safe_get

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]):
    """Validate the user input allows us to connect."""
    # 注意：这个函数现在只在成功时返回值，失败时直接抛出异常
    # 错误处理逻辑移至调用方 (各个 step 中)
    try:
        client = LifeSmartOAPIClient(
            hass,
            data.get(CONF_REGION),
            data.get(CONF_LIFESMART_APPKEY),
            data.get(CONF_LIFESMART_APPTOKEN),
            data.get(CONF_LIFESMART_USERTOKEN),
            data.get(CONF_LIFESMART_USERID),
            user_password=data.get(CONF_LIFESMART_USERPASSWORD),
        )

        if data.get(CONF_LIFESMART_USERPASSWORD):
            _LOGGER.info("Attempting login with user password...")
            login_response = await client.login_async()
            if not login_response:
                _LOGGER.error("Authentication failed with provided password.")
                raise ConfigEntryAuthFailed("invalid_auth")
            _LOGGER.info("Login successful, obtained user token.")
            data[CONF_LIFESMART_USERTOKEN] = login_response.get(
                "usertoken", data.get(CONF_LIFESMART_USERTOKEN, "")
            )
            data[CONF_REGION] = login_response.get(
                "region", data.get(CONF_REGION, "cn2")
            )
            # 同时更新 userid，以防 API 返回的是规范化的 userid
            if "userid" in login_response:
                data[CONF_LIFESMART_USERID] = login_response.get(
                    "userid", data.get(CONF_LIFESMART_USERID, "")
                )

        devices = await client.async_get_all_devices()

        if not isinstance(devices, list):
            _LOGGER.error("API did not return a valid device list: %s", devices)
            raise ConfigEntryAuthFailed("invalid_response")
        if len(devices) == 0:
            _LOGGER.warning("No devices found for this user.")

        return {
            "title": f"LifeSmart ({data.get(CONF_LIFESMART_USERID)})",
            "data": data,
        }
    except LifeSmartAuthError as e:
        _LOGGER.error("认证失败: %s", e)
        raise ConfigEntryAuthFailed(str(e)) from e
    except Exception as e:
        _LOGGER.error("Unknown error during validation: %s", str(e), exc_info=True)
        raise ConfigEntryNotReady("Unknown error during validation") from e


async def validate_local_input(
    hass: HomeAssistant, data: dict[str, Any]
) -> dict[str, Any]:
    """Validate the user input for local connection."""
    try:
        dev = custom_components.lifesmart.core.local_tcp_client.LifeSmartLocalTCPClient(
            data[CONF_HOST],
            data[CONF_PORT],
            data[CONF_USERNAME],
            data[CONF_PASSWORD],
        )
        await dev.check_login()
    except (ConnectionResetError, asyncio.InvalidStateError) as e:
        _LOGGER.error(
            "Local connection failed, likely due to invalid credentials: %s", e
        )
        raise ConfigEntryAuthFailed("invalid_auth") from e
    except (asyncio.TimeoutError, OSError) as e:
        _LOGGER.error("Local connection error: %s", e)
        raise ConfigEntryNotReady("cannot_connect") from e
    except Exception as e:
        _LOGGER.error(
            "Local input validation encountered an unknown error: %s",
            str(e),
            exc_info=True,
        )
        raise ConfigEntryNotReady("unknown") from e
    return data


@config_entries.HANDLERS.register(DOMAIN)
class LifeSmartConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handles the LifeSmart configuration flow."""

    VERSION = 1
    _reauth_entry: config_entries.ConfigEntry | None = None

    def __init__(self) -> None:
        """Initialize the config flow."""
        super().__init__()
        self.config_data = {}

    # 统一的流程结束处理函数
    async def _async_finish_flow(self, validation_result: dict[str, Any]) -> FlowResult:
        """统一处理配置流程的最后一步，区分首次设置和重新认证。"""
        # 检查是否处于重新认证流程
        if self._reauth_entry:
            _LOGGER.info("重新认证成功，正在更新配置条目...")
            data = safe_get(validation_result, "data", default={})
            self.hass.config_entries.async_update_entry(self._reauth_entry, data=data)
            # 更新后需要重新加载集成以使新凭据生效
            await self.hass.config_entries.async_reload(self._reauth_entry.entry_id)
            # 中止流程，并向用户显示成功消息
            return self.async_abort(reason="reauth_successful")

        # 检查此用户是否已配置
        userid = safe_get(validation_result, "data", CONF_LIFESMART_USERID, default="")
        if userid:
            await self.async_set_unique_id(userid)
        self._abort_if_unique_id_configured()

        # 首次设置，创建新的配置条目
        _LOGGER.info("首次设置成功，正在创建新的配置条目...")
        return self.async_create_entry(
            title=validation_result["title"], data=validation_result["data"]
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            if user_input[CONF_TYPE] == config_entries.CONN_CLASS_LOCAL_PUSH:
                return await self.async_step_local()
            return await self.async_step_cloud()

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_TYPE, default=config_entries.CONN_CLASS_CLOUD_PUSH
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            config_entries.CONN_CLASS_LOCAL_PUSH,
                            config_entries.CONN_CLASS_CLOUD_PUSH,
                        ],
                        mode=SelectSelectorMode.DROPDOWN,
                        translation_key="connection_type",
                    )
                )
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_local(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the local connection setup."""
        errors = {}
        if user_input is not None:
            try:
                await validate_local_input(self.hass, user_input)
                return self.async_create_entry(
                    title=f"Local Hub ({user_input[CONF_HOST]})",
                    data={
                        **user_input,
                        CONF_TYPE: config_entries.CONN_CLASS_LOCAL_PUSH,
                    },
                )
            except (asyncio.TimeoutError, ConnectionRefusedError, ConfigEntryNotReady):
                errors["base"] = "cannot_connect"
            except ConfigEntryAuthFailed:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("本地连接流程发生未知错误")
                errors["base"] = "unknown"

        local_schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=""): str,
                vol.Required(CONF_PORT, default=3000): int,
                vol.Required(CONF_USERNAME, default="admin"): str,
                vol.Required(CONF_PASSWORD, default="admin"): selector.TextSelector(
                    selector.TextSelectorConfig(type="password")
                ),
            }
        )
        return self.async_show_form(
            step_id="local", data_schema=local_schema, errors=errors
        )

    async def async_step_cloud(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle cloud setup: Step 1 - Basic info and auth method."""
        try:

            if not hasattr(self, "config_data"):
                self.config_data = {}

            if self._reauth_entry:
                self.config_data.update(self._reauth_entry.data)

            if user_input is not None:
                self.config_data.update(user_input)
                if user_input[CONF_LIFESMART_AUTH_METHOD] == "token":
                    return await self.async_step_cloud_token()
                return await self.async_step_cloud_password()

            cloud_schema = vol.Schema(
                {
                    vol.Required(
                        CONF_LIFESMART_APPKEY,
                        default=self.config_data.get(CONF_LIFESMART_APPKEY, ""),
                    ): str,
                    vol.Required(
                        CONF_LIFESMART_APPTOKEN,
                        default=self.config_data.get(CONF_LIFESMART_APPTOKEN, ""),
                    ): str,
                    vol.Required(
                        CONF_LIFESMART_USERID,
                        default=self.config_data.get(CONF_LIFESMART_USERID, ""),
                    ): str,
                    vol.Required(
                        CONF_REGION, default=self.config_data.get(CONF_REGION, "cn2")
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=LIFESMART_REGION_OPTIONS,
                            mode=SelectSelectorMode.DROPDOWN,
                            translation_key="region",
                        )
                    ),
                    vol.Required(
                        CONF_LIFESMART_AUTH_METHOD,
                        default=self.config_data.get(
                            CONF_LIFESMART_AUTH_METHOD, "token"
                        ),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=["token", "password"],
                            mode=SelectSelectorMode.DROPDOWN,
                            translation_key="auth_method",
                        )
                    ),
                }
            )
            return self.async_show_form(step_id="cloud", data_schema=cloud_schema)
        except Exception as e:
            _LOGGER.exception("Unexpected error in async_step_cloud: %s", e)
            return self.async_abort(reason="unknown_error")

    async def async_step_cloud_token(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle cloud setup: Step 2 - Enter User Token."""
        errors = {}
        if user_input is not None:
            self.config_data.update(user_input)
            try:
                validation_result = await validate_input(self.hass, self.config_data)
                return await self._async_finish_flow(validation_result)
            except AbortFlow:
                raise
            except LifeSmartAuthError as e:
                _LOGGER.error("配置流程认证失败: %s", e)
                # 从异常中获取错误码
                if e.code:
                    _, advice, _ = get_error_advice(e.code)
                    errors["base"] = advice
                else:
                    errors["base"] = "invalid_auth"
            except ConfigEntryNotReady:
                errors["base"] = "cannot_connect"
            except Exception as e:
                _LOGGER.error("配置流程发生未知错误: %s", e, exc_info=True)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="cloud_token",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_LIFESMART_USERTOKEN,
                        default=self.config_data.get(CONF_LIFESMART_USERTOKEN, ""),
                    ): str
                }
            ),
            errors=errors,
        )

    async def async_step_cloud_password(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle cloud setup: Step 2 - Enter User Password."""
        errors = {}
        if user_input is not None:
            self.config_data.update(user_input)
            try:
                validation_result = await validate_input(self.hass, self.config_data)
                return await self._async_finish_flow(validation_result)
            except AbortFlow:
                raise
            except LifeSmartAuthError as e:
                _LOGGER.error("配置流程认证失败: %s", e)
                if e.code:
                    _, advice, _ = get_error_advice(e.code)
                    errors["base"] = advice
                else:
                    errors["base"] = "invalid_auth"
            except ConfigEntryNotReady:
                errors["base"] = "cannot_connect"
            except Exception as e:
                _LOGGER.error("配置流程发生未知错误: %s", e, exc_info=True)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="cloud_password",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_LIFESMART_USERPASSWORD): selector.TextSelector(
                        selector.TextSelectorConfig(type="password")
                    )
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> FlowResult:
        """Handle re-authentication."""
        # 检查上下文中是否有 entry_id
        entry_id = self.context.get("entry_id")
        if not entry_id:
            _LOGGER.error("重新认证失败：上下文中缺少 entry_id")
            return self.async_abort(reason="reauth_entry_not_found")

        self._reauth_entry = self.hass.config_entries.async_get_entry(entry_id)

        # 检查配置条目是否存在
        if self._reauth_entry is None:
            _LOGGER.error("重新认证失败：无法找到配置条目 %s", entry_id)
            return self.async_abort(reason="reauth_entry_not_found")

        # 将现有数据预填充到流程中
        self.config_data = self._reauth_entry.data.copy()
        # 直接进入云端配置的第一步
        return await self.async_step_cloud()

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return LifeSmartOptionsFlowHandler(config_entry)


class LifeSmartOptionsFlowHandler(config_entries.OptionsFlow):
    """Handles the LifeSmart options flow."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        super().__init__()

        # 兼容性：处理不同HA版本的config_entry访问方式
        # HA 2025.7.4+: config_entry属性存在但在init期间不可访问
        # HA 2024.12.0: config_entry属性存在且可访问
        # HA 2024.2.0及以下: config_entry属性不存在，需要手动设置
        config_entry_available = False
        try:
            # 尝试检查config_entry是否可用（但不访问它，因为可能抛出ValueError）
            if hasattr(self, "config_entry"):
                # 属性存在，但可能在init期间不可访问
                config_entry_available = True
        except (AttributeError, ValueError):
            # 属性不存在或不可访问
            pass

        # 只有在config_entry不可用时才手动设置
        if not config_entry_available:
            self.config_entry = config_entry

        # 保存config_entry引用，用于后续访问
        self._config_entry_ref = config_entry

        self.options_data = dict(config_entry.options)
        self.temp_data = {}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the option menu."""
        # 根据连接类型决定显示的菜单选项
        menu_options = ["main_params"]

        # 只有云端模式才显示认证参数选项和遥控器配置
        # 使用保存的引用以避免在新版本HA中的访问限制
        try:
            config_data = self.config_entry.data
        except (AttributeError, ValueError):
            # 如果无法访问config_entry，使用保存的引用
            config_data = self._config_entry_ref.data

        if config_data.get(CONF_TYPE) == config_entries.CONN_CLASS_CLOUD_PUSH:
            menu_options.append("auth_params")
            menu_options.append("add_remote")  # 添加遥控器配置选项

        return self.async_show_menu(
            step_id="init",
            menu_options=menu_options,
        )

    async def async_step_main_params(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle general settings."""
        if user_input is not None:
            self.options_data.update(user_input)
            return self.async_create_entry(title="", data=self.options_data)

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_EXCLUDE_ITEMS,
                    default=self.options_data.get(CONF_EXCLUDE_ITEMS, ""),
                ): str,
                vol.Optional(
                    CONF_EXCLUDE_AGTS,
                    default=self.options_data.get(CONF_EXCLUDE_AGTS, ""),
                ): str,
                vol.Optional(
                    CONF_AI_INCLUDE_AGTS,
                    default=self.options_data.get(CONF_AI_INCLUDE_AGTS, ""),
                ): str,
                vol.Optional(
                    CONF_AI_INCLUDE_ITEMS,
                    default=self.options_data.get(CONF_AI_INCLUDE_ITEMS, ""),
                ): str,
            }
        )
        return self.async_show_form(step_id="main_params", data_schema=schema)

    async def async_step_auth_params(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle authentication settings update (Step 1)."""
        # 检查是否为本地TCP模式，如果是则不应该显示认证参数选项
        # 使用保存的引用以避免在新版本HA中的访问限制
        try:
            config_data = self.config_entry.data
        except (AttributeError, ValueError):
            # 如果无法访问config_entry，使用保存的引用
            config_data = self._config_entry_ref.data

        if config_data.get(CONF_TYPE) == config_entries.CONN_CLASS_LOCAL_PUSH:
            return self.async_abort(reason="local_no_auth_params")

        self.temp_data = config_data.copy()

        if user_input is not None:
            self.temp_data.update(user_input)
            if user_input[CONF_LIFESMART_AUTH_METHOD] == "token":
                return await self.async_step_auth_token()
            return await self.async_step_auth_password()

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_LIFESMART_AUTH_METHOD,
                    default=self.temp_data.get(CONF_LIFESMART_AUTH_METHOD, "token"),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=["token", "password"],
                        mode=SelectSelectorMode.DROPDOWN,
                        translation_key="auth_method",
                    )
                )
            }
        )
        return self.async_show_form(step_id="auth_params", data_schema=schema)

    async def async_step_auth_token(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle auth update: Step 2 - Enter User Token."""
        errors = {}
        if user_input is not None:
            self.temp_data.update(user_input)
            try:
                await validate_input(self.hass, self.temp_data)
                # 使用保存的引用以避免在新版本HA中的访问限制
                try:
                    config_entry = self.config_entry
                except (AttributeError, ValueError):
                    config_entry = self._config_entry_ref

                self.hass.config_entries.async_update_entry(
                    config_entry, data=self.temp_data
                )
                return self.async_create_entry(title="", data={})
            except ConfigEntryAuthFailed as e:
                errors["base"] = str(e) or "invalid_auth"
            except Exception:
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="auth_token",
            data_schema=vol.Schema({vol.Required(CONF_LIFESMART_USERTOKEN): str}),
            errors=errors,
        )

    async def async_step_auth_password(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle auth update: Step 2 - Enter User Password."""
        errors = {}
        if user_input is not None:
            self.temp_data.update(user_input)
            try:
                await validate_input(self.hass, self.temp_data)
                # 使用保存的引用以避免在新版本HA中的访问限制
                try:
                    config_entry = self.config_entry
                except (AttributeError, ValueError):
                    config_entry = self._config_entry_ref

                self.hass.config_entries.async_update_entry(
                    config_entry, data=self.temp_data
                )
                return self.async_create_entry(title="", data={})
            except ConfigEntryAuthFailed as e:
                errors["base"] = str(e) or "invalid_auth"
            except Exception:
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="auth_password",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_LIFESMART_USERPASSWORD): selector.TextSelector(
                        selector.TextSelectorConfig(type="password")
                    )
                }
            ),
            errors=errors,
        )

    async def async_step_add_remote(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """添加遥控器配置 - 第1步：基本信息"""
        if user_input is not None:
            self.temp_data = user_input.copy()
            return await self.async_step_select_category()

        return self.async_show_form(
            step_id="add_remote",
            data_schema=vol.Schema(
                {
                    vol.Required("remote_name"): str,
                    vol.Required("hub_id"): str,  # TODO: 后续可改为设备选择器
                    vol.Required("device_id"): str,  # SPOT设备的me ID
                }
            ),
        )

    async def async_step_select_category(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """选择设备类别"""
        errors = {}

        if user_input is not None:
            self.temp_data.update(user_input)
            return await self.async_step_select_brand()

        try:
            # 获取云端客户端实例
            config_data = self._config_entry_ref.data
            client = LifeSmartOAPIClient(
                self.hass,
                config_data.get(CONF_REGION),
                config_data.get(CONF_LIFESMART_APPKEY),
                config_data.get(CONF_LIFESMART_APPTOKEN),
                config_data.get(CONF_LIFESMART_USERTOKEN),
                config_data.get(CONF_LIFESMART_USERID),
            )

            categories = await client.get_ir_categories_async()

            # 转换为选择器选项
            category_options = []
            for cat in categories:
                label = self._get_category_label(cat)
                category_options.append({"value": cat, "label": label})

            return self.async_show_form(
                step_id="select_category",
                data_schema=vol.Schema(
                    {
                        vol.Required("category"): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=category_options,
                                mode=SelectSelectorMode.DROPDOWN,
                            )
                        )
                    }
                ),
                errors=errors,
            )
        except Exception as e:
            _LOGGER.error("获取设备类别失败: %s", e)
            errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="select_category",
            data_schema=vol.Schema(
                {
                    vol.Required("category"): str,
                }
            ),
            errors=errors,
        )

    async def async_step_select_brand(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """选择品牌"""
        if user_input is not None:
            self.temp_data.update(user_input)
            return await self.async_step_select_model()

        try:
            config_data = self._config_entry_ref.data
            client = LifeSmartOAPIClient(
                self.hass,
                config_data.get(CONF_REGION),
                config_data.get(CONF_LIFESMART_APPKEY),
                config_data.get(CONF_LIFESMART_APPTOKEN),
                config_data.get(CONF_LIFESMART_USERTOKEN),
                config_data.get(CONF_LIFESMART_USERID),
            )

            brands = await client.get_ir_brands_async(self.temp_data["category"])

            brand_options = []
            for brand_name in brands.keys():
                brand_options.append({"value": brand_name, "label": brand_name})

            return self.async_show_form(
                step_id="select_brand",
                data_schema=vol.Schema(
                    {
                        vol.Required("brand"): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=brand_options, mode=SelectSelectorMode.DROPDOWN
                            )
                        )
                    }
                ),
            )
        except Exception as e:
            _LOGGER.error("获取品牌列表失败: %s", e)
            return self.async_abort(reason="api_error")

    async def async_step_select_model(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """选择遥控器型号"""
        if user_input is not None:
            self.temp_data.update(user_input)

            # 保存遥控器配置到选项中
            remotes = self.options_data.get("remotes", {})
            remote_id = f"{self.temp_data['category']}_{self.temp_data['brand']}_{self.temp_data['idx']}"

            remotes[remote_id] = {
                "name": self.temp_data["remote_name"],
                "hub_id": self.temp_data["hub_id"],
                "device_id": self.temp_data["device_id"],
                "category": self.temp_data["category"],
                "brand": self.temp_data["brand"],
                "idx": self.temp_data["idx"],
            }

            self.options_data["remotes"] = remotes
            return self.async_create_entry(title="", data=self.options_data)

        try:
            config_data = self._config_entry_ref.data
            client = LifeSmartOAPIClient(
                self.hass,
                config_data.get(CONF_REGION),
                config_data.get(CONF_LIFESMART_APPKEY),
                config_data.get(CONF_LIFESMART_APPTOKEN),
                config_data.get(CONF_LIFESMART_USERTOKEN),
                config_data.get(CONF_LIFESMART_USERID),
            )

            models = await client.get_ir_remote_indexes_async(
                self.temp_data["category"], self.temp_data["brand"]
            )

            model_options = []
            for idx in models:
                model_options.append({"value": idx, "label": f"型号 {idx}"})

            return self.async_show_form(
                step_id="select_model",
                data_schema=vol.Schema(
                    {
                        vol.Required("idx"): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=model_options, mode=SelectSelectorMode.DROPDOWN
                            )
                        )
                    }
                ),
            )
        except Exception as e:
            _LOGGER.error("获取遥控器型号失败: %s", e)
            return self.async_abort(reason="api_error")

    def _get_category_label(self, category: str) -> str:
        """获取设备类别的显示名称"""
        category_labels = {
            "tv": "电视机",
            "ac": "空调",
            "stb": "机顶盒",
            "dvd": "录像机",
            "box": "网络盒子",
            "fan": "风扇",
            "acl": "空气净化器",
            "custom": "自定义",
        }
        return category_labels.get(category, category)
