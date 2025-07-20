"""测试 LifeSmart 配置流程"""

from unittest.mock import patch, AsyncMock

import pytest
from homeassistant import config_entries, data_entry_flow
from homeassistant.const import (
    CONF_TYPE,
    CONF_HOST,
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_PORT,
    CONF_REGION,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from custom_components.lifesmart.const import (
    DOMAIN,
    CONF_LIFESMART_APPKEY,
    CONF_LIFESMART_APPTOKEN,
    CONF_LIFESMART_USERID,
    CONF_LIFESMART_USERTOKEN,
    CONF_LIFESMART_USERPASSWORD,
    CONF_LIFESMART_AUTH_METHOD,
    CONF_EXCLUDE_ITEMS,
)
from custom_components.lifesmart.exceptions import LifeSmartAuthError


@pytest.mark.asyncio
async def test_config_flow_user_step(hass: HomeAssistant):
    """测试初始的用户选择步骤。"""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"

    # 模拟选择云端模式
    with patch(
        "custom_components.lifesmart.config_flow.LifeSmartConfigFlowHandler.async_step_cloud",
        return_value={"type": data_entry_flow.FlowResultType.FORM, "step_id": "cloud"},
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_TYPE: "cloud_push"}
        )
        await hass.async_block_till_done()
        assert result2["step_id"] == "cloud"

    # 模拟选择本地模式
    with patch(
        "custom_components.lifesmart.config_flow.LifeSmartConfigFlowHandler.async_step_local",
        return_value={"type": data_entry_flow.FlowResultType.FORM, "step_id": "local"},
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_TYPE: "local_push"}
        )
        await hass.async_block_till_done()
        assert result3["step_id"] == "local"


@pytest.mark.asyncio
async def test_config_flow_cloud_token_success(hass: HomeAssistant):
    """测试云端配置流程（使用Token认证）并成功创建条目。"""
    with patch(
        "custom_components.lifesmart.config_flow.validate_input",
        new_callable=AsyncMock,
    ) as mock_validate:
        # 模拟验证成功
        mock_validate.return_value = {
            "title": "LifeSmart (mock_userid)",
            "data": {
                CONF_LIFESMART_APPKEY: "mock_appkey",
                CONF_LIFESMART_USERID: "mock_userid",
                CONF_LIFESMART_USERTOKEN: "mock_usertoken",
            },
        }

        # 1. 开始流程
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        # 2. 选择云端模式
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_TYPE: "cloud_push"}
        )

        # 3. 填写基本信息并选择Token认证
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_LIFESMART_APPKEY: "mock_appkey",
                CONF_LIFESMART_APPTOKEN: "mock_apptoken",
                CONF_LIFESMART_USERID: "mock_userid",
                CONF_REGION: "cn2",
                CONF_LIFESMART_AUTH_METHOD: "token",
            },
        )
        assert result["step_id"] == "cloud_token"

        # 4. 填写Token并完成
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_LIFESMART_USERTOKEN: "mock_usertoken"}
        )
        await hass.async_block_till_done()

        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result["title"] == "LifeSmart (mock_userid)"
        assert result["data"][CONF_LIFESMART_APPKEY] == "mock_appkey"


@pytest.mark.asyncio
async def test_config_flow_cloud_password_success(hass: HomeAssistant):
    """测试云端配置流程（使用密码认证）并成功创建条目。"""
    with patch(
        "custom_components.lifesmart.config_flow.validate_input",
        new_callable=AsyncMock,
    ) as mock_validate:
        # 模拟密码登录后返回了新的token
        mock_validate.return_value = {
            "title": "LifeSmart (mock_userid)",
            "data": {
                CONF_LIFESMART_APPKEY: "mock_appkey",
                CONF_LIFESMART_USERID: "mock_userid",
                CONF_LIFESMART_USERTOKEN: "newly_fetched_token",  # 验证这个新token是否被保存
            },
        }

        # ... 省略前面相同的步骤 ...
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_TYPE: "cloud_push"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_LIFESMART_APPKEY: "mock_appkey",
                CONF_LIFESMART_APPTOKEN: "mock_apptoken",
                CONF_LIFESMART_USERID: "mock_userid",
                CONF_REGION: "cn2",
                CONF_LIFESMART_AUTH_METHOD: "password",
            },
        )
        assert result["step_id"] == "cloud_password"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_LIFESMART_USERPASSWORD: "mock_password"}
        )
        await hass.async_block_till_done()

        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_LIFESMART_USERTOKEN] == "newly_fetched_token"


@pytest.mark.asyncio
async def test_config_flow_cloud_auth_error(hass: HomeAssistant):
    """测试云端配置流程中发生认证失败。"""
    with patch(
        "custom_components.lifesmart.config_flow.validate_input",
        new_callable=AsyncMock,
    ) as mock_validate:
        # 模拟认证失败
        mock_validate.side_effect = LifeSmartAuthError("Invalid token", 10005)

        # ... 省略前面相同的步骤 ...
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_TYPE: "cloud_push"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_LIFESMART_APPKEY: "mock_appkey",
                CONF_LIFESMART_APPTOKEN: "mock_apptoken",
                CONF_LIFESMART_USERID: "mock_userid",
                CONF_REGION: "cn2",
                CONF_LIFESMART_AUTH_METHOD: "token",
            },
        )
        # 提交错误的token
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_LIFESMART_USERTOKEN: "invalid_token"}
        )

        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "cloud_token"
        assert result["errors"]["base"] is not None  # 应该包含错误信息


@pytest.mark.asyncio
async def test_config_flow_local_success(hass: HomeAssistant):
    """测试本地配置流程并成功创建条目。"""
    with patch(
        "custom_components.lifesmart.config_flow.validate_local_input",
        new_callable=AsyncMock,
    ) as mock_validate_local:
        mock_validate_local.return_value = True  # 模拟本地验证成功

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_TYPE: "local_push"}
        )
        assert result["step_id"] == "local"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.168.1.100",
                CONF_PORT: 3000,
                CONF_USERNAME: "admin",
                CONF_PASSWORD: "admin",
            },
        )
        await hass.async_block_till_done()

        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result["title"] == "Local Hub (192.168.1.100)"
        assert result["data"][CONF_HOST] == "192.168.1.100"
        assert result["data"][CONF_TYPE] == "local_push"


@pytest.mark.asyncio
async def test_config_flow_local_failure(hass: HomeAssistant):
    """测试本地配置流程因连接失败而显示错误。"""
    with patch(
        "custom_components.lifesmart.config_flow.validate_local_input",
        new_callable=AsyncMock,
    ) as mock_validate_local:
        mock_validate_local.side_effect = ConfigEntryNotReady("Connection failed")

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_TYPE: "local_push"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.168.1.100",
                CONF_PORT: 3000,
                CONF_USERNAME: "admin",
                CONF_PASSWORD: "wrong_password",
            },
        )

        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "local"
        assert result["errors"]["base"] == "invalid_auth"


@pytest.mark.asyncio
async def test_options_flow(hass: HomeAssistant, mock_config_entry):
    """测试选项流程。"""
    # 将模拟的配置条目添加到HASS中
    mock_config_entry.add_to_hass(hass)

    # 初始化选项流程
    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

    # 1. 显示菜单
    assert result["type"] == data_entry_flow.FlowResultType.MENU
    assert result["step_id"] == "init"

    # 2. 选择并进入主要参数设置
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"next_step_id": "main_params"}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "main_params"

    # 3. 提交新的选项
    new_exclude_list = "dev1,dev2"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_EXCLUDE_ITEMS: new_exclude_list}
    )

    # 4. 验证流程结束并更新了选项
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert mock_config_entry.options[CONF_EXCLUDE_ITEMS] == new_exclude_list


@pytest.mark.asyncio
async def test_reauth_flow(hass: HomeAssistant, mock_config_entry):
    """测试重新认证流程。"""
    mock_config_entry.add_to_hass(hass)

    # 模拟一个需要重新认证的场景
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_REAUTH,
            "entry_id": mock_config_entry.entry_id,
        },
        data=mock_config_entry.data,
    )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "cloud"  # 应该直接跳转到云端配置第一步

    # 模拟验证成功
    with patch(
        "custom_components.lifesmart.config_flow.validate_input",
        return_value={
            "title": "LifeSmart (mock_userid)",
            "data": {
                **mock_config_entry.data,
                CONF_LIFESMART_USERTOKEN: "new_reauthed_token",
            },
        },
    ), patch.object(
        hass.config_entries, "async_reload", return_value=None
    ) as mock_reload:
        # 提交新密码
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {**mock_config_entry.data, CONF_LIFESMART_AUTH_METHOD: "password"},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_LIFESMART_USERPASSWORD: "new_password"}
        )

        assert result["type"] == data_entry_flow.FlowResultType.ABORT
        assert result["reason"] == "reauth_successful"

        # 验证配置条目数据已更新
        assert mock_config_entry.data[CONF_LIFESMART_USERTOKEN] == "new_reauthed_token"

        # 验证集成被重新加载
        mock_reload.assert_called_once_with(mock_config_entry.entry_id)
