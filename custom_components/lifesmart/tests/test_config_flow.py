"""测试 LifeSmart 配置流程"""

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
        "custom_components.lifesmart.config_flow.validate_local_input",
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

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"


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

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "cloud"


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

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "local"


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
    assert result["step_id"] == "cloud_token"

    # 3. Provide token and finish
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_LIFESMART_USERTOKEN: "mock_usertoken"}
    )
    await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "LifeSmart (mock_userid)"
    assert result["data"][CONF_LIFESMART_USERTOKEN] == "mock_usertoken"


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
    assert result["step_id"] == "cloud_password"

    # 2. Provide password and finish
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_LIFESMART_USERPASSWORD: "mock_password"}
    )
    await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_LIFESMART_USERTOKEN] == "newly_fetched_token"


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

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "cloud_token"
    assert (
        result["errors"]["base"]
        == "请检查用户令牌(UserToken)是否正确，或到LifeSmart平台检查授权。"
    )


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

    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "cannot_connect"


# endregion


# region: Local Flow Tests
@pytest.mark.asyncio
async def test_local_flow_success(hass: HomeAssistant, mock_validate_local):
    """测试本地模式配置成功。"""
    mock_validate_local.return_value = {"title": "Local Hub (192.168.1.100)"}

    # 1. Start flow, select local
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_TYPE: "local_push"}
    )
    assert result["step_id"] == "local"

    # 2. Provide details and finish
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], MOCK_USER_INPUT_LOCAL
    )
    await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Local Hub (192.168.1.100)"
    assert result["data"][CONF_HOST] == MOCK_USER_INPUT_LOCAL[CONF_HOST]


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

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "local"
    assert result["errors"]["base"] == "cannot_connect"


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
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "cloud"

    # 模拟用户在第一步选择密码认证
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {**mock_config_entry.data, CONF_LIFESMART_AUTH_METHOD: "password"},
    )
    assert result["step_id"] == "cloud_password"

    with patch(
        "homeassistant.config_entries.ConfigEntries.async_reload", return_value=True
    ) as mock_reload:
        # 提交新密码
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_LIFESMART_USERPASSWORD: "new_password"}
        )
        await hass.async_block_till_done()

        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "reauth_successful"
        assert mock_config_entry.data[CONF_LIFESMART_USERTOKEN] == "newly_fetched_token"
        mock_reload.assert_called_once_with(mock_config_entry.entry_id)


@pytest.mark.asyncio
async def test_options_flow(hass: HomeAssistant, mock_config_entry):
    """测试选项流程可以成功更新排除列表。"""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    assert result["type"] == FlowResultType.MENU
    assert result["step_id"] == "init"

    # 模拟用户选择 "main_params" 菜单项
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"next_step_id": "main_params"}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "main_params"

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

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert mock_config_entry.options[CONF_EXCLUDE_ITEMS] == new_exclude_list
    assert mock_config_entry.options[CONF_EXCLUDE_AGTS] == new_exclude_hubs


# endregion


# region: Edge Cases
@pytest.mark.asyncio
async def test_flow_aborts_if_already_configured(
    hass: HomeAssistant, mock_config_entry
):
    """测试如果用户已配置，流程会中止。"""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_TYPE: "cloud_push"}
    )

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

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


# endregion
