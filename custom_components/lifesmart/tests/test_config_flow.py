"""测试 LifeSmart 配置流程"""

import asyncio
from unittest.mock import patch, AsyncMock

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
    CONF_EXCLUDE_AGTS,
    CONF_EXCLUDE_ITEMS,
    CONF_LIFESMART_APPKEY,
    CONF_LIFESMART_APPTOKEN,
    CONF_LIFESMART_AUTH_METHOD,
    CONF_LIFESMART_USERID,
    CONF_LIFESMART_USERPASSWORD,
    CONF_LIFESMART_USERTOKEN,
    CONF_AI_INCLUDE_AGTS,
    CONF_AI_INCLUDE_ITEMS,
    DOMAIN,
)
from custom_components.lifesmart.exceptions import LifeSmartAuthError

# --- Mock Data ---

MOCK_USER_INPUT_CLOUD_BASE = {
    CONF_LIFESMART_APPKEY: "mock_appkey",
    CONF_LIFESMART_APPTOKEN: "mock_apptoken",
    CONF_LIFESMART_USERID: "mock_userid",
    CONF_REGION: "cn2",
}

MOCK_VALIDATE_SUCCESS_RESULT = {
    "title": "LifeSmart (mock_userid)",
    "data": {
        **MOCK_USER_INPUT_CLOUD_BASE,
        CONF_LIFESMART_USERTOKEN: "mock_usertoken",
    },
}

MOCK_VALIDATE_NEW_TOKEN_RESULT = {
    "title": "LifeSmart (mock_userid)",
    "data": {
        **MOCK_USER_INPUT_CLOUD_BASE,
        CONF_LIFESMART_USERTOKEN: "newly_fetched_token",
    },
}

MOCK_USER_INPUT_LOCAL = {
    CONF_HOST: "192.168.1.100",
    CONF_PORT: 3000,
    CONF_USERNAME: "admin",
    CONF_PASSWORD: "admin_password",
}

# --- Fixtures ---


@pytest.fixture(name="mock_validate")
def mock_validate_fixture():
    """提供一个统一的 patch fixture 来模拟 validate_input 函数。"""
    with patch(
        "custom_components.lifesmart.config_flow.validate_input",
        new_callable=AsyncMock,
    ) as mock_func:
        yield mock_func


@pytest.fixture(name="mock_validate_local")
def mock_validate_local_fixture():
    """提供一个统一的 patch fixture 来模拟 validate_local_input 函数。"""
    with patch(
        "custom_components.lifesmart.core.local_tcp_client.LifeSmartLocalTCPClient.check_login",
        new_callable=AsyncMock,
    ) as mock_func:
        yield mock_func


# --- Tests ---


# region: User Flow Tests
@pytest.mark.asyncio
async def test_user_step_shows_form(hass: HomeAssistant):
    """测试初始的用户流程显示一个选择表单。"""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == FlowResultType.FORM, "应该返回表单类型的结果"
    assert result["step_id"] == "user", "步骤ID应该是user"


@pytest.mark.asyncio
async def test_user_step_routes_to_cloud(hass: HomeAssistant):
    """测试选择'cloud_push'后，流程转向云端配置步骤。"""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_TYPE: "cloud_push"}
    )
    await hass.async_block_till_done()

    assert result["type"] == FlowResultType.FORM, "应该返回表单类型的结果"
    assert result["step_id"] == "cloud", "步骤ID应该是cloud"


@pytest.mark.asyncio
async def test_user_step_routes_to_local(hass: HomeAssistant):
    """测试选择'local_push'后，流程转向本地配置步骤。"""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_TYPE: "local_push"}
    )
    await hass.async_block_till_done()

    assert result["type"] == FlowResultType.FORM, "应该返回表单类型的结果"
    assert result["step_id"] == "local", "步骤ID应该是local"


# endregion


# region: Cloud Flow Tests
@pytest.mark.asyncio
async def test_cloud_flow_token_auth_success(hass: HomeAssistant, mock_validate):
    """测试云端Token认证流程成功并创建配置条目。"""
    mock_validate.return_value = MOCK_VALIDATE_SUCCESS_RESULT

    # 1. Start flow and select cloud
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_TYPE: "cloud_push"}
    )

    # 2. Select token auth
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {**MOCK_USER_INPUT_CLOUD_BASE, CONF_LIFESMART_AUTH_METHOD: "token"},
    )
    assert result["step_id"] == "cloud_token", "应该转到云端Token认证步骤"

    # 3. Provide token and finish
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_LIFESMART_USERTOKEN: "mock_usertoken"}
    )
    await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY, "应该创建配置条目"
    assert result["title"] == "LifeSmart (mock_userid)", "配置条目标题应该正确"
    assert (
        result["data"][CONF_LIFESMART_USERTOKEN] == "mock_usertoken"
    ), "应该保存用户提供的Token"


@pytest.mark.asyncio
async def test_cloud_flow_password_auth_success(hass: HomeAssistant, mock_validate):
    """测试云端密码认证流程成功，并保存返回的新Token。"""
    mock_validate.return_value = MOCK_VALIDATE_NEW_TOKEN_RESULT

    # 1. Start flow, select cloud, select password auth
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_TYPE: "cloud_push"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {**MOCK_USER_INPUT_CLOUD_BASE, CONF_LIFESMART_AUTH_METHOD: "password"},
    )
    assert result["step_id"] == "cloud_password", "应该转到云端密码认证步骤"

    # 2. Provide password and finish
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_LIFESMART_USERPASSWORD: "mock_password"}
    )
    await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY, "应该创建配置条目"
    assert (
        result["data"][CONF_LIFESMART_USERTOKEN] == "newly_fetched_token"
    ), "应该保存新获取的Token"


@pytest.mark.asyncio
async def test_cloud_flow_auth_error(hass: HomeAssistant, mock_validate):
    """测试当云端认证失败时，流程显示错误并停留在当前步骤。"""
    mock_validate.side_effect = LifeSmartAuthError("User not authorized", 10005)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_TYPE: "cloud_push"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {**MOCK_USER_INPUT_CLOUD_BASE, CONF_LIFESMART_AUTH_METHOD: "token"},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_LIFESMART_USERTOKEN: "invalid_token"}
    )

    assert result["type"] == FlowResultType.FORM, "应该返回表单类型的结果"
    assert result["step_id"] == "cloud_token", "应该停留在cloud_token步骤"
    assert (
        result["errors"]["base"]
        == "请检查用户令牌(UserToken)是否正确，或到LifeSmart平台检查授权。"
    ), "应该显示认证错误信息"


@pytest.mark.asyncio
async def test_cloud_flow_connection_error(hass: HomeAssistant, mock_validate):
    """测试当发生连接错误时，流程显示错误。"""
    mock_validate.side_effect = ConfigEntryNotReady

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_TYPE: "cloud_push"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {**MOCK_USER_INPUT_CLOUD_BASE, CONF_LIFESMART_AUTH_METHOD: "token"},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_LIFESMART_USERTOKEN: "any_token"}
    )

    assert result["type"] == FlowResultType.FORM, "应该返回表单类型的结果"
    assert result["errors"]["base"] == "cannot_connect", "应该显示连接错误信息"


# endregion


# region: Local Flow Tests
@pytest.mark.asyncio
async def test_local_flow_success(hass: HomeAssistant):
    """测试本地连接配置流程成功并正确清理。"""
    # 步骤 1: 初始化配置流程
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] == FlowResultType.FORM, "应该返回表单类型的结果"
    assert result["step_id"] == "user", "步骤ID应该是user"

    # 步骤 2: 选择本地连接类型
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TYPE: config_entries.CONN_CLASS_LOCAL_PUSH},
    )
    await hass.async_block_till_done()

    assert result2["type"] == FlowResultType.FORM, "应该返回表单类型的结果"
    assert result2["step_id"] == "local", "步骤ID应该是local"

    # 步骤 3: 模拟 check_login 成功，并提供本地连接信息
    # 我们 patch check_login 以避免实际的网络调用，并确保它能成功
    with patch(
        "custom_components.lifesmart.core.local_tcp_client.LifeSmartLocalTCPClient.check_login",
        return_value=True,
    ), patch(
        "custom_components.lifesmart.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry, patch(
        "custom_components.lifesmart.async_unload_entry",
        return_value=True,
    ) as mock_unload_entry:
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_PORT: 9876,
                CONF_USERNAME: "admin",
                CONF_PASSWORD: "password",
            },
        )
        await hass.async_block_till_done()

        # 步骤 4: 断言流程成功并创建了配置条目
        assert result3["type"] == FlowResultType.CREATE_ENTRY, "应该创建配置条目"
        assert result3["title"] == "Local Hub (1.1.1.1)", "配置条目标题应该正确"
        assert result3["data"] == {
            CONF_TYPE: config_entries.CONN_CLASS_LOCAL_PUSH,
            CONF_HOST: "1.1.1.1",
            CONF_PORT: 9876,
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "password",
        }, "配置数据应该正确保存"

        # 确保 async_setup_entry 被调用了一次
        assert len(mock_setup_entry.mock_calls) == 1, "async_setup_entry应该被调用一次"

        entry = hass.config_entries.async_entries(DOMAIN)[0]
        # 卸载它，这将调用我们 patch 过的 async_unload_entry
        assert await hass.config_entries.async_unload(
            entry.entry_id
        ), "应该能够成功卸载配置条目"
        await hass.async_block_till_done()

        # 确保 async_unload_entry 也被调用了
        assert (
            len(mock_unload_entry.mock_calls) == 1
        ), "async_unload_entry应该被调用一次"


@pytest.mark.asyncio
async def test_local_flow_failure(hass: HomeAssistant, mock_validate_local):
    """测试本地模式因连接/认证失败而显示错误。"""
    mock_validate_local.side_effect = ConfigEntryNotReady("Connection refused")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_TYPE: "local_push"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], MOCK_USER_INPUT_LOCAL
    )

    assert result["type"] == FlowResultType.FORM, "应该返回表单类型的结果"
    assert result["step_id"] == "local", "应该停留在local步骤"
    assert result["errors"]["base"] == "cannot_connect", "应该显示连接错误信息"


# endregion


# region: Re-auth and Options Flow
@pytest.mark.asyncio
async def test_reauth_flow_success(
    hass: HomeAssistant, mock_config_entry, mock_validate
):
    """测试重新认证流程能成功更新配置条目并重新加载集成。"""
    mock_config_entry.add_to_hass(hass)
    mock_validate.return_value = MOCK_VALIDATE_NEW_TOKEN_RESULT

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_REAUTH,
            "entry_id": mock_config_entry.entry_id,
        },
        data=mock_config_entry.data,
    )
    assert result["type"] == FlowResultType.FORM, "应该返回表单类型的结果"
    assert result["step_id"] == "cloud", "步骤ID应该是cloud"

    # 模拟用户在第一步选择密码认证
    user_input_step1 = {
        CONF_LIFESMART_APPKEY: mock_config_entry.data[CONF_LIFESMART_APPKEY],
        CONF_LIFESMART_APPTOKEN: mock_config_entry.data[CONF_LIFESMART_APPTOKEN],
        CONF_LIFESMART_USERID: mock_config_entry.data[CONF_LIFESMART_USERID],
        CONF_REGION: mock_config_entry.data[CONF_REGION],
        CONF_LIFESMART_AUTH_METHOD: "password",
    }
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input_step1,
    )
    assert result["step_id"] == "cloud_password", "应该转到云端密码认证步骤"

    with patch(
        "homeassistant.config_entries.ConfigEntries.async_reload", return_value=True
    ) as mock_reload:
        # 提交新密码
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_LIFESMART_USERPASSWORD: "new_password"}
        )
        await hass.async_block_till_done()

        assert result["type"] == FlowResultType.ABORT, "重新认证完成后应该中止流程"
        assert result["reason"] == "reauth_successful", "中止原因应该是重新认证成功"
        assert (
            mock_config_entry.data[CONF_LIFESMART_USERTOKEN] == "newly_fetched_token"
        ), "配置条目应该更新为新Token"
        mock_reload.assert_called_once_with(
            mock_config_entry.entry_id
        ), "应该重新加载配置条目"


@pytest.mark.asyncio
async def test_options_flow(hass: HomeAssistant, mock_config_entry):
    """测试选项流程可以成功更新排除列表。"""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    assert result["type"] == FlowResultType.MENU, "应该返回菜单类型的结果"
    assert result["step_id"] == "init", "步骤ID应该是init"

    # 模拟用户选择 "main_params" 菜单项
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"next_step_id": "main_params"}
    )
    assert result["type"] == FlowResultType.FORM, "应该返回表单类型的结果"
    assert result["step_id"] == "main_params", "应该转到main_params步骤"

    new_exclude_list = "dev1,dev2"
    new_exclude_hubs = "hub1"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_EXCLUDE_ITEMS: new_exclude_list,
            CONF_EXCLUDE_AGTS: new_exclude_hubs,
            CONF_AI_INCLUDE_AGTS: "",
            CONF_AI_INCLUDE_ITEMS: "",
        },
    )
    await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY, "应该创建选项条目"
    assert (
        mock_config_entry.options[CONF_EXCLUDE_ITEMS] == new_exclude_list
    ), "排除设备列表应该被正确更新"
    assert (
        mock_config_entry.options[CONF_EXCLUDE_AGTS] == new_exclude_hubs
    ), "排除Hub列表应该被正确更新"


# endregion


# region: Edge Cases
@pytest.mark.asyncio
async def test_flow_aborts_if_already_configured(
    hass: HomeAssistant,
):  # 移除 mock_config_entry fixture
    """测试如果用户已配置，流程会中止。"""
    # 1. 创建一个带有 unique_id 的模拟条目并添加到 hass
    existing_entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_USER_INPUT_CLOUD_BASE,
        unique_id=MOCK_USER_INPUT_CLOUD_BASE[CONF_LIFESMART_USERID],
    )
    existing_entry.add_to_hass(hass)

    # 2. 像新用户一样开始配置流程
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_TYPE: "cloud_push"}
    )

    # 3. 模拟验证成功，这将触发 unique_id 检查
    with patch(
        "custom_components.lifesmart.config_flow.validate_input",
        return_value=MOCK_VALIDATE_SUCCESS_RESULT,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {**MOCK_USER_INPUT_CLOUD_BASE, CONF_LIFESMART_AUTH_METHOD: "token"},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_LIFESMART_USERTOKEN: "any_token"}
        )

    # 4. 断言流程被正确中止
    assert result["type"] == FlowResultType.ABORT, "已存在相同配置时应该中止流程"
    assert result["reason"] == "already_configured", "中止原因应该是已配置"


# endregion


# region: Enhanced Options Flow Tests
@pytest.mark.asyncio
async def test_options_flow_local_tcp_no_auth_params(hass: HomeAssistant):
    """测试本地TCP模式的选项流程不显示认证参数菜单项。"""
    # 创建本地TCP模式的配置条目
    local_config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_TYPE: config_entries.CONN_CLASS_LOCAL_PUSH,
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 3000,
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "admin_pass",
        },
    )
    local_config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(local_config_entry.entry_id)

    assert result["type"] == FlowResultType.MENU, "应该返回菜单类型的结果"
    assert result["step_id"] == "init", "步骤ID应该是init"
    # 本地TCP模式应该只有 main_params 菜单项，没有 auth_params
    assert result["menu_options"] == [
        "main_params"
    ], "本地TCP模式只应该显示main_params选项"


@pytest.mark.asyncio
async def test_options_flow_cloud_mode_shows_auth_params(
    hass: HomeAssistant, mock_config_entry
):
    """测试云端模式的选项流程显示认证参数菜单项。"""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

    assert result["type"] == FlowResultType.MENU, "应该返回菜单类型的结果"
    assert result["step_id"] == "init", "步骤ID应该是init"
    # 云端模式应该有 main_params 和 auth_params 两个菜单项
    assert result["menu_options"] == [
        "main_params",
        "auth_params",
    ], "云端模式应该显示所有选项"


# endregion


# region: Error Handling and Edge Cases
@pytest.mark.asyncio
async def test_cloud_flow_unknown_error(hass: HomeAssistant, mock_validate):
    """测试云端流程遇到未知错误时的处理。"""
    mock_validate.side_effect = Exception("Unexpected error")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_TYPE: "cloud_push"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {**MOCK_USER_INPUT_CLOUD_BASE, CONF_LIFESMART_AUTH_METHOD: "token"},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_LIFESMART_USERTOKEN: "any_token"}
    )

    assert result["type"] == FlowResultType.FORM, "应该返回表单类型的结果"
    assert result["step_id"] == "cloud_token", "应该停留在cloud_token步骤"
    assert result["errors"]["base"] == "unknown", "应该显示未知错误信息"


@pytest.mark.asyncio
async def test_local_flow_auth_error(hass: HomeAssistant):
    """测试本地流程认证失败的处理。"""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_TYPE: "local_push"}
    )

    # 模拟认证失败
    with patch(
        "custom_components.lifesmart.core.local_tcp_client.LifeSmartLocalTCPClient.check_login",
        side_effect=ConnectionResetError("Authentication failed"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], MOCK_USER_INPUT_LOCAL
        )

    assert result["type"] == FlowResultType.FORM, "应该返回表单类型的结果"
    assert result["step_id"] == "local", "应该停留在local步骤"
    assert result["errors"]["base"] == "invalid_auth", "应该显示认证错误信息"


@pytest.mark.asyncio
async def test_local_flow_unknown_error(hass: HomeAssistant):
    """测试本地流程遇到未知错误时的处理。"""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_TYPE: "local_push"}
    )

    # 模拟未知错误 - 使用asyncio.TimeoutError，这会被归类为连接错误
    with patch(
        "custom_components.lifesmart.core.local_tcp_client.LifeSmartLocalTCPClient.check_login",
        side_effect=asyncio.TimeoutError("Connection timeout"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], MOCK_USER_INPUT_LOCAL
        )

    assert result["type"] == FlowResultType.FORM, "应该返回表单类型的结果"
    assert result["step_id"] == "local", "应该停留在local步骤"
    assert result["errors"]["base"] == "cannot_connect", "应该显示连接错误信息"


@pytest.mark.asyncio
async def test_validate_input_empty_device_list(hass: HomeAssistant):
    """测试validate_input函数获取到空设备列表的处理。"""
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
        return_value=[],  # 空设备列表
    ):
        # 空设备列表不应该导致错误，只是警告
        result = await validate_input(hass, test_data)
        assert result is not None, "空设备列表不应该导致验证失败"


@pytest.mark.asyncio
async def test_reauth_flow_missing_entry_id(hass: HomeAssistant):
    """测试重新认证流程缺少entry_id时正确处理。"""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_REAUTH},  # 缺少 entry_id
        data={},
    )

    assert result["type"] == FlowResultType.ABORT, "缺少entry_id时应该中止流程"
    assert result["reason"] == "reauth_entry_not_found", "中止原因应该是找不到条目"


@pytest.mark.asyncio
async def test_reauth_flow_invalid_entry_id(hass: HomeAssistant):
    """测试重新认证流程entry_id无效时正确处理。"""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_REAUTH,
            "entry_id": "non_existent_entry_id",
        },
        data={},
    )

    assert result["type"] == FlowResultType.ABORT, "无效entry_id时应该中止流程"
    assert result["reason"] == "reauth_entry_not_found", "中止原因应该是找不到条目"


# endregion
