"""
测试 LifeSmart 配置流程。

此测试套件覆盖完整的配置流程，包括：
- 初始用户流程和连接类型选择
- 云端配置流程（Token 和密码认证）
- 本地连接配置流程
- 重新认证流程和错误处理
- 选项流程（通用设置和认证参数）
- 边界条件和异常情况处理
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_REGION,
    CONF_TYPE,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import ConfigEntryNotReady
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.lifesmart.const import (
    CONF_AI_INCLUDE_AGTS,
    CONF_AI_INCLUDE_ITEMS,
    CONF_EXCLUDE_AGTS,
    CONF_EXCLUDE_ITEMS,
    CONF_LIFESMART_APPKEY,
    CONF_LIFESMART_APPTOKEN,
    CONF_LIFESMART_AUTH_METHOD,
    CONF_LIFESMART_USERID,
    CONF_LIFESMART_USERPASSWORD,
    CONF_LIFESMART_USERTOKEN,
    DOMAIN,
)
from custom_components.lifesmart.exceptions import LifeSmartAuthError

# ==================== 测试数据 ====================

MOCK_CLOUD_CREDENTIALS = {
    CONF_LIFESMART_APPKEY: "mock_appkey",
    CONF_LIFESMART_APPTOKEN: "mock_apptoken",
    CONF_LIFESMART_USERID: "mock_userid",
    CONF_REGION: "cn2",
}

MOCK_LOCAL_CREDENTIALS = {
    CONF_HOST: "192.168.1.100",
    CONF_PORT: 3000,
    CONF_USERNAME: "admin",
    CONF_PASSWORD: "admin_password",
}

MOCK_VALIDATION_SUCCESS = {
    "title": "LifeSmart (mock_userid)",
    "data": {
        **MOCK_CLOUD_CREDENTIALS,
        CONF_LIFESMART_USERTOKEN: "mock_usertoken",
    },
}

MOCK_VALIDATION_WITH_NEW_TOKEN = {
    "title": "LifeSmart (mock_userid)",
    "data": {
        **MOCK_CLOUD_CREDENTIALS,
        CONF_LIFESMART_USERTOKEN: "newly_fetched_token",
    },
}


# ==================== Fixtures ====================


@pytest.fixture
def mock_validate():
    """模拟 validate_input 函数。"""
    with patch(
        "custom_components.lifesmart.config_flow.validate_input",
        new_callable=AsyncMock,
    ) as mock_func:
        yield mock_func


@pytest.fixture
def mock_validate_local():
    """模拟本地连接验证。"""
    with patch(
        "custom_components.lifesmart.core.local_tcp_client.LifeSmartLocalTCPClient.check_login",
        new_callable=AsyncMock,
    ) as mock_func:
        yield mock_func


@pytest.fixture
def mock_config_entry():
    """提供标准的云端配置条目。"""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_TYPE: config_entries.CONN_CLASS_CLOUD_PUSH,
            **MOCK_CLOUD_CREDENTIALS,
            CONF_LIFESMART_USERTOKEN: "existing_token",
            CONF_LIFESMART_AUTH_METHOD: "token",
        },
        entry_id="test_entry_cloud",
    )


# ==================== 初始用户流程测试 ====================


class TestUserFlow:
    """测试初始用户流程和连接类型选择。"""

    @pytest.mark.asyncio
    async def test_user_step_shows_connection_form(self, hass: HomeAssistant):
        """测试初始步骤显示连接类型选择表单。"""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        assert result["type"] == FlowResultType.FORM, "应该显示表单"
        assert result["step_id"] == "user", "步骤应该是用户选择"

    @pytest.mark.asyncio
    async def test_user_step_routes_to_cloud(self, hass: HomeAssistant):
        """测试选择云端连接后正确跳转。"""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_TYPE: "cloud_push"}
        )

        assert result["type"] == FlowResultType.FORM, "应该显示表单"
        assert result["step_id"] == "cloud", "应该跳转到云端配置"

    @pytest.mark.asyncio
    async def test_user_step_routes_to_local(self, hass: HomeAssistant):
        """测试选择本地连接后正确跳转。"""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_TYPE: "local_push"}
        )

        assert result["type"] == FlowResultType.FORM, "应该显示表单"
        assert result["step_id"] == "local", "应该跳转到本地配置"


# ==================== 云端配置流程测试 ====================


class TestCloudFlow:
    """测试云端配置流程。"""

    @pytest.mark.asyncio
    async def test_token_authentication_success(
        self, hass: HomeAssistant, mock_validate
    ):
        """测试 Token 认证成功流程。"""
        mock_validate.return_value = MOCK_VALIDATION_SUCCESS

        # 启动流程并选择云端
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_TYPE: "cloud_push"}
        )

        # 选择 Token 认证
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {**MOCK_CLOUD_CREDENTIALS, CONF_LIFESMART_AUTH_METHOD: "token"},
        )
        assert result["step_id"] == "cloud_token", "应该进入 Token 输入步骤"

        # 提供 Token 并完成
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_LIFESMART_USERTOKEN: "mock_usertoken"}
        )

        assert result["type"] == FlowResultType.CREATE_ENTRY, "应该创建配置条目"
        assert result["title"] == "LifeSmart (mock_userid)", "标题应该正确"
        assert (
            result["data"][CONF_LIFESMART_USERTOKEN] == "mock_usertoken"
        ), "Token 应该保存"

    @pytest.mark.asyncio
    async def test_password_authentication_success(
        self, hass: HomeAssistant, mock_validate
    ):
        """测试密码认证成功流程。"""
        mock_validate.return_value = MOCK_VALIDATION_WITH_NEW_TOKEN

        # 启动流程并选择云端
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_TYPE: "cloud_push"}
        )

        # 选择密码认证
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {**MOCK_CLOUD_CREDENTIALS, CONF_LIFESMART_AUTH_METHOD: "password"},
        )
        assert result["step_id"] == "cloud_password", "应该进入密码输入步骤"

        # 提供密码并完成
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_LIFESMART_USERPASSWORD: "mock_password"}
        )

        assert result["type"] == FlowResultType.CREATE_ENTRY, "应该创建配置条目"
        assert (
            result["data"][CONF_LIFESMART_USERTOKEN] == "newly_fetched_token"
        ), "应该保存新 Token"

    @pytest.mark.asyncio
    async def test_authentication_error_handling(
        self, hass: HomeAssistant, mock_validate
    ):
        """测试认证错误的处理。"""
        mock_validate.side_effect = LifeSmartAuthError("User not authorized", 10005)

        result = await self._start_cloud_token_flow(hass)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_LIFESMART_USERTOKEN: "invalid_token"}
        )

        assert result["type"] == FlowResultType.FORM, "应该重新显示表单"
        assert result["step_id"] == "cloud_token", "应该停留在 Token 步骤"
        assert "请检查用户令牌" in result["errors"]["base"], "应该显示具体错误信息"

    @pytest.mark.asyncio
    async def test_connection_error_handling(self, hass: HomeAssistant, mock_validate):
        """测试连接错误的处理。"""
        mock_validate.side_effect = ConfigEntryNotReady("Connection failed")

        result = await self._start_cloud_token_flow(hass)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_LIFESMART_USERTOKEN: "any_token"}
        )

        assert result["type"] == FlowResultType.FORM, "应该重新显示表单"
        assert result["errors"]["base"] == "cannot_connect", "应该显示连接错误"

    @pytest.mark.asyncio
    async def test_unknown_error_handling(self, hass: HomeAssistant, mock_validate):
        """测试未知错误的处理。"""
        mock_validate.side_effect = Exception("Unexpected error")

        result = await self._start_cloud_token_flow(hass)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_LIFESMART_USERTOKEN: "any_token"}
        )

        assert result["type"] == FlowResultType.FORM, "应该重新显示表单"
        assert result["errors"]["base"] == "unknown", "应该显示未知错误"

    async def _start_cloud_token_flow(self, hass: HomeAssistant):
        """启动云端 Token 认证流程的辅助方法。"""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_TYPE: "cloud_push"}
        )
        return await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {**MOCK_CLOUD_CREDENTIALS, CONF_LIFESMART_AUTH_METHOD: "token"},
        )


# ==================== 本地配置流程测试 ====================


class TestLocalFlow:
    """测试本地连接配置流程。"""

    @pytest.mark.asyncio
    async def test_local_connection_success(self, hass: HomeAssistant):
        """测试本地连接成功配置。"""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_TYPE: config_entries.CONN_CLASS_LOCAL_PUSH}
        )

        # 模拟成功的本地连接验证
        with patch(
            "custom_components.lifesmart.core.local_tcp_client.LifeSmartLocalTCPClient.check_login",
            return_value=True,
        ):
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], MOCK_LOCAL_CREDENTIALS
            )

        assert result["type"] == FlowResultType.CREATE_ENTRY, "应该创建配置条目"
        assert result["title"] == "Local Hub (192.168.1.100)", "标题应该包含 IP"
        assert result["data"] == {
            **MOCK_LOCAL_CREDENTIALS,
            CONF_TYPE: config_entries.CONN_CLASS_LOCAL_PUSH,
        }, "配置数据应该正确"

    @pytest.mark.asyncio
    async def test_local_connection_auth_error(self, hass: HomeAssistant):
        """测试本地连接认证失败。"""
        result = await self._start_local_flow(hass)

        # 模拟认证失败
        with patch(
            "custom_components.lifesmart.core.local_tcp_client.LifeSmartLocalTCPClient.check_login",
            side_effect=ConnectionResetError("Authentication failed"),
        ):
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], MOCK_LOCAL_CREDENTIALS
            )

        assert result["type"] == FlowResultType.FORM, "应该重新显示表单"
        assert result["errors"]["base"] == "invalid_auth", "应该显示认证错误"

    @pytest.mark.asyncio
    async def test_local_connection_network_error(self, hass: HomeAssistant):
        """测试本地连接网络错误。"""
        result = await self._start_local_flow(hass)

        # 模拟连接超时
        with patch(
            "custom_components.lifesmart.core.local_tcp_client.LifeSmartLocalTCPClient.check_login",
            side_effect=asyncio.TimeoutError("Connection timeout"),
        ):
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], MOCK_LOCAL_CREDENTIALS
            )

        assert result["type"] == FlowResultType.FORM, "应该重新显示表单"
        assert result["errors"]["base"] == "cannot_connect", "应该显示连接错误"

    async def _start_local_flow(self, hass: HomeAssistant):
        """启动本地配置流程的辅助方法。"""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        return await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_TYPE: "local_push"}
        )


# ==================== 重新认证流程测试 ====================


class TestReauthFlow:
    """测试重新认证流程。"""

    @pytest.mark.asyncio
    async def test_reauth_success(
        self, hass: HomeAssistant, mock_config_entry, mock_validate
    ):
        """测试重新认证成功流程。"""
        mock_config_entry.add_to_hass(hass)
        mock_validate.return_value = MOCK_VALIDATION_WITH_NEW_TOKEN

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_REAUTH,
                "entry_id": mock_config_entry.entry_id,
            },
            data=mock_config_entry.data,
        )

        # 选择密码认证
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_LIFESMART_APPKEY: mock_config_entry.data[CONF_LIFESMART_APPKEY],
                CONF_LIFESMART_APPTOKEN: mock_config_entry.data[
                    CONF_LIFESMART_APPTOKEN
                ],
                CONF_LIFESMART_USERID: mock_config_entry.data[CONF_LIFESMART_USERID],
                CONF_REGION: mock_config_entry.data[CONF_REGION],
                CONF_LIFESMART_AUTH_METHOD: "password",
            },
        )

        # 模拟重新加载
        with patch(
            "homeassistant.config_entries.ConfigEntries.async_reload", return_value=True
        ) as mock_reload:
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], {CONF_LIFESMART_USERPASSWORD: "new_password"}
            )

            assert result["type"] == FlowResultType.ABORT, "重新认证应该中止流程"
            assert result["reason"] == "reauth_successful", "中止原因应该是成功"
            assert (
                mock_config_entry.data[CONF_LIFESMART_USERTOKEN]
                == "newly_fetched_token"
            ), "Token 应该更新"
            mock_reload.assert_called_once_with(
                mock_config_entry.entry_id
            ), "应该重新加载"

    @pytest.mark.asyncio
    async def test_reauth_missing_entry_id(self, hass: HomeAssistant):
        """测试缺少 entry_id 时的处理。"""
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_REAUTH},
            data={},
        )

        assert result["type"] == FlowResultType.ABORT, "应该中止流程"
        assert result["reason"] == "reauth_entry_not_found", "原因应该是找不到条目"

    @pytest.mark.asyncio
    async def test_reauth_invalid_entry_id(self, hass: HomeAssistant):
        """测试无效 entry_id 时的处理。"""
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_REAUTH,
                "entry_id": "non_existent_entry_id",
            },
            data={},
        )

        assert result["type"] == FlowResultType.ABORT, "应该中止流程"
        assert result["reason"] == "reauth_entry_not_found", "原因应该是找不到条目"


# ==================== 选项流程测试 ====================


class TestOptionsFlow:
    """测试选项配置流程。"""

    @pytest.mark.asyncio
    async def test_options_main_params_update(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """测试主要参数选项更新。"""
        mock_config_entry.add_to_hass(hass)

        result = await hass.config_entries.options.async_init(
            mock_config_entry.entry_id
        )
        assert result["type"] == FlowResultType.MENU, "应该显示菜单"

        # 选择主要参数
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], user_input={"next_step_id": "main_params"}
        )

        # 更新排除列表
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_EXCLUDE_ITEMS: "dev1,dev2",
                CONF_EXCLUDE_AGTS: "hub1",
                CONF_AI_INCLUDE_AGTS: "",
                CONF_AI_INCLUDE_ITEMS: "",
            },
        )

        assert result["type"] == FlowResultType.CREATE_ENTRY, "应该创建选项条目"
        assert (
            mock_config_entry.options[CONF_EXCLUDE_ITEMS] == "dev1,dev2"
        ), "排除设备应该更新"
        assert (
            mock_config_entry.options[CONF_EXCLUDE_AGTS] == "hub1"
        ), "排除 Hub 应该更新"

    @pytest.mark.asyncio
    async def test_options_cloud_mode_shows_auth_params(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """测试云端模式显示认证参数选项。"""
        mock_config_entry.add_to_hass(hass)

        result = await hass.config_entries.options.async_init(
            mock_config_entry.entry_id
        )

        assert result["type"] == FlowResultType.MENU, "应该显示菜单"
        assert "auth_params" in result["menu_options"], "云端模式应该显示认证参数选项"

    @pytest.mark.asyncio
    async def test_options_local_mode_hides_auth_params(self, hass: HomeAssistant):
        """测试本地模式隐藏认证参数选项。"""
        local_config_entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_TYPE: config_entries.CONN_CLASS_LOCAL_PUSH,
                **MOCK_LOCAL_CREDENTIALS,
            },
        )
        local_config_entry.add_to_hass(hass)

        result = await hass.config_entries.options.async_init(
            local_config_entry.entry_id
        )

        assert result["type"] == FlowResultType.MENU, "应该显示菜单"
        assert result["menu_options"] == ["main_params"], "本地模式只应该显示主要参数"


# ==================== 边界条件测试 ====================


class TestEdgeCases:
    """测试边界条件和异常情况。"""

    @pytest.mark.asyncio
    async def test_already_configured_abort(self, hass: HomeAssistant):
        """测试已配置用户时中止流程。"""
        # 创建已存在的配置条目
        existing_entry = MockConfigEntry(
            domain=DOMAIN,
            data=MOCK_CLOUD_CREDENTIALS,
            unique_id=MOCK_CLOUD_CREDENTIALS[CONF_LIFESMART_USERID],
        )
        existing_entry.add_to_hass(hass)

        # 尝试重新配置相同用户
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_TYPE: "cloud_push"}
        )

        with patch(
            "custom_components.lifesmart.config_flow.validate_input",
            return_value=MOCK_VALIDATION_SUCCESS,
        ):
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {**MOCK_CLOUD_CREDENTIALS, CONF_LIFESMART_AUTH_METHOD: "token"},
            )
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], {CONF_LIFESMART_USERTOKEN: "any_token"}
            )

        assert result["type"] == FlowResultType.ABORT, "应该中止流程"
        assert result["reason"] == "already_configured", "原因应该是已配置"

    @pytest.mark.asyncio
    async def test_validate_input_empty_device_list(self, hass: HomeAssistant):
        """测试空设备列表的处理。"""
        from custom_components.lifesmart.config_flow import validate_input

        test_data = {
            CONF_REGION: "cn2",
            CONF_LIFESMART_APPKEY: "test_key",
            CONF_LIFESMART_APPTOKEN: "test_token",
            CONF_LIFESMART_USERID: "test_user",
            CONF_LIFESMART_USERTOKEN: "test_token",
        }

        with patch(
            "custom_components.lifesmart.core.openapi_client.LifeSmartOAPIClient.async_get_all_devices",
            return_value=[],
        ):
            result = await validate_input(hass, test_data)
            assert result is not None, "空设备列表不应该导致验证失败"
