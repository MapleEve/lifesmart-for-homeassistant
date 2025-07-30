"""
对 openapi_client.py 的全覆盖单元测试。
"""

import json
from unittest.mock import AsyncMock, patch, call

import pytest
from aiohttp import ClientError
from homeassistant.components.climate import (
    HVACMode,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_HIGH,
    FAN_AUTO,
)

from custom_components.lifesmart.const import (
    CMD_TYPE_ON,
    CMD_TYPE_OFF,
    CMD_TYPE_PRESS,
    CMD_TYPE_SET_VAL,
    CMD_TYPE_SET_CONFIG,
    CMD_TYPE_SET_TEMP_DECIMAL,
    CMD_TYPE_SET_RAW,
    CMD_TYPE_SET_TEMP_FCU,
    DOOYA_TYPES,
    GARAGE_DOOR_TYPES,
)
from custom_components.lifesmart.core.openapi_client import LifeSmartOAPIClient
from custom_components.lifesmart.exceptions import LifeSmartAPIError, LifeSmartAuthError


# region Fixtures
@pytest.fixture
def client(hass):
    """提供一个标准的 LifeSmartOAPIClient 实例，包含所有必要参数。"""
    return LifeSmartOAPIClient(
        hass, "cn2", "appkey", "apptoken", "usertoken", "userid", "password"
    )


@pytest.fixture
def mock_async_call_api():
    """Mock _async_call_api 方法，用于测试上层辅助函数。"""
    with patch(
        "custom_components.lifesmart.core.openapi_client.LifeSmartOAPIClient._async_call_api",
        new_callable=AsyncMock,
    ) as mock_func:
        mock_func.return_value = {"code": 0}  # 默认返回成功
        yield mock_func


# endregion


# region Initialization and URL/Header Generation Tests
def test_url_and_header_generation(hass):
    """测试 API/WSS URL 和 HTTP Header 的生成逻辑。"""
    client_region = LifeSmartOAPIClient(hass, "cn2", "k", "t", "ut", "uid")
    assert client_region._get_api_url() == "https://api.cn2.ilifesmart.com/app"
    assert client_region.get_wss_url() == "wss://api.cn2.ilifesmart.com:8443/wsapp/"

    for auto_region in ["AUTO", None, ""]:
        client_auto = LifeSmartOAPIClient(hass, auto_region, "k", "t", "ut", "uid")
        assert client_auto._get_api_url() == "https://api.ilifesmart.com/app"
        assert client_auto.get_wss_url() == "wss://api.ilifesmart.com:8443/wsapp/"

    assert client_region._generate_header() == {"Content-Type": "application/json"}


# endregion


# region Core API Call, Signature and Error Handling Tests
@pytest.mark.asyncio
async def test_async_call_api_signature_and_error_handling(client):
    """测试 _async_call_api 的签名生成和对不同错误码的异常处理。"""
    with patch.object(
        client, "_post_and_parse", return_value={"code": 0}
    ) as mock_post, patch(
        "custom_components.lifesmart.core.openapi_client.LifeSmartOAPIClient._get_signature"
    ) as mock_get_signature:
        mock_get_signature.return_value = "mocked_signature"

        # 1. 测试带参数的情况
        await client._async_call_api(
            "TestMethodWithParams", {"z_param": "val_z", "a_param": "val_a"}
        )
        mock_get_signature.assert_called_once()
        signature_raw_string = mock_get_signature.call_args.args[0]
        assert "a_param:val_a,z_param:val_z" in signature_raw_string
        sent_payload_with_params = mock_post.call_args.args[1]
        assert sent_payload_with_params["system"]["sign"] == "mocked_signature"

        # 2. 关键补充：测试不带参数的情况
        mock_get_signature.reset_mock()
        await client._async_call_api("TestMethodNoParams")
        mock_get_signature.assert_called_once()
        signature_raw_string_no_params = mock_get_signature.call_args.args[0]
        # 验证签名字符串中不包含任何参数部分
        assert "a_param" not in signature_raw_string_no_params
        assert "z_param" not in signature_raw_string_no_params
        sent_payload_no_params = mock_post.call_args.args[1]
        assert "params" not in sent_payload_no_params

    for auth_error_code in [10004, 10005, 10006]:
        with patch.object(
            client,
            "_post_and_parse",
            return_value={"code": auth_error_code, "message": "auth error"},
        ):
            with pytest.raises(LifeSmartAuthError):
                await client._async_call_api("AnyMethod")

    with patch.object(
        client, "_post_and_parse", return_value={"code": -1, "message": "general error"}
    ):
        with pytest.raises(LifeSmartAPIError):
            await client._async_call_api("AnyMethod")


@pytest.mark.asyncio
async def test_post_and_parse_network_failure(client):
    """测试 _post_and_parse 在网络失败时的行为。"""
    with patch(
        "custom_components.lifesmart.core.openapi_client.LifeSmartOAPIClient._post_async",
        new_callable=AsyncMock,
    ) as mock_post:
        mock_post.side_effect = ClientError("Connection failed")
        with pytest.raises(LifeSmartAPIError, match="网络请求失败"):
            await client._post_and_parse("http://a.b", {}, {})


@pytest.mark.asyncio
async def test_post_and_parse_json_failure(client):
    """测试 _post_and_parse 在JSON解析失败时的行为。"""
    with patch(
        "custom_components.lifesmart.core.openapi_client.LifeSmartOAPIClient._post_async",
        new_callable=AsyncMock,
    ) as mock_post:
        mock_post.return_value = "this is not json"
        with pytest.raises(LifeSmartAPIError, match="JSON解析失败"):
            await client._post_and_parse("http://a.b", {}, {})


def test_get_code_from_response_all_failures(client):
    """测试 _get_code_from_response 的所有失败分支。"""
    assert client._get_code_from_response(None, "test") == -1
    assert client._get_code_from_response({"message": "no code"}, "test") == -1
    assert client._get_code_from_response({"code": "not_an_int"}, "test") == -1
    assert client._get_code_from_response({"code": None}, "test") == -1


# endregion


# region Special Auth and WSS Flow Tests
@pytest.mark.asyncio
async def test_login_async_full_flow(client, mock_async_call_api):
    """测试登录流程的所有成功和失败分支。"""
    mock_async_call_api.side_effect = [
        {"code": "success", "token": "temp_token", "userid": "new_user_id"},
        {
            "code": "success",
            "usertoken": "new_user_token",
            "rgn": "cn1",
            "userid": "new_user_id",
        },
    ]
    # 模拟 _post_and_parse 因为 login 是特殊端点
    with patch.object(client, "_post_and_parse") as mock_post:
        mock_post.side_effect = mock_async_call_api.side_effect
        result = await client.login_async()

    assert client._usertoken == "new_user_token"
    assert client._region == "cn1"
    assert client._userid == "new_user_id"
    assert result["usertoken"] == "new_user_token"

    with patch.object(client, "_post_and_parse") as mock_post:
        mock_post.side_effect = LifeSmartAuthError(-1)
        with pytest.raises(LifeSmartAuthError):
            await client.login_async()

    with patch.object(client, "_post_and_parse") as mock_post:
        mock_post.side_effect = [
            {"code": "success", "token": "temp_token", "userid": "user_id"},
            LifeSmartAuthError(-1),
        ]
        with pytest.raises(LifeSmartAuthError):
            await client.login_async()

    with patch.object(client, "_post_and_parse") as mock_post:
        # 存储原始值以便恢复
        original_userid = client._userid
        original_apppassword = client._apppassword

        # 遍历无效的 userid 和 apppassword 组合
        for invalid_user, invalid_apppass in [
            (None, "valid_hash"),  # 无效用户名
            ("", "valid_hash"),  # 无效用户名
            ("valid_user", None),  # 无效应用密码
            ("valid_user", ""),  # 无效应用密码
        ]:
            client._userid = invalid_user
            client._apppassword = invalid_apppass

            with pytest.raises(
                LifeSmartAuthError, match="用户名或应用密码无效，无法登录。"
            ):
                await client.login_async()

            # 验证在这种情况下没有发起任何网络请求
            mock_post.assert_not_called()

        # 恢复原始值，避免影响后续测试
        client._userid = original_userid
        client._apppassword = original_apppassword


@pytest.mark.asyncio
async def test_async_refresh_token_full_flow(client, mock_async_call_api):
    """测试令牌刷新流程的成功和失败分支。"""
    mock_async_call_api.return_value = {"code": 0, "usertoken": "refreshed_token"}
    with patch.object(client, "_post_and_parse") as mock_post:
        mock_post.return_value = mock_async_call_api.return_value
        result = await client.async_refresh_token()

    assert client._usertoken == "refreshed_token"
    assert result["usertoken"] == "refreshed_token"

    with patch.object(client, "_post_and_parse") as mock_post:
        mock_post.side_effect = LifeSmartAuthError(-1)
        with pytest.raises(LifeSmartAuthError):
            await client.async_refresh_token()


def test_generate_wss_auth(client):
    """测试 WebSocket 认证消息的生成。"""
    client._usertoken = "test_wss_token"
    auth_str = client.generate_wss_auth()
    auth_data = json.loads(auth_str)
    assert "system" in auth_data
    assert "usertoken" not in auth_data["system"]
    assert "sign" in auth_data["system"]
    assert "userid" in auth_data["system"]


# endregion


# region Public API Wrapper Method Tests
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method_to_test, api_method, call_args, expected_params, api_path",
    [
        ("get_agt_list_async", "AgtGetList", (), None, "/api"),
        ("get_agt_details_async", "AgtGet", ("hub1",), {"agt": "hub1"}, "/api"),
        ("async_get_all_devices", "EpGetAll", (), None, "/api"),
        ("get_scene_list_async", "SceneGet", ("hub1",), {"agt": "hub1"}, "/api"),
        ("get_room_list_async", "RoomGet", ("hub1",), {"agt": "hub1"}, "/api"),
        (
            "async_set_scene",
            "SceneSet",
            ("hub1", "s1"),
            {"agt": "hub1", "id": "s1"},
            "/api",
        ),
        (
            "get_epget_async",
            "EpGet",
            ("hub1", "dev1"),
            {"agt": "hub1", "me": "dev1"},
            "/api",
        ),
        (
            "get_ir_remote_list_async",
            "GetRemoteList",
            ("hub1",),
            {"agt": "hub1"},
            "/irapi",
        ),
        (
            "async_send_ir_key",
            "SendKeys",
            ("hub1", "ai1", "me1", "cat1", "brand1", "key1"),
            {
                "agt": "hub1",
                "ai": "ai1",
                "me": "me1",
                "category": "cat1",
                "brand": "brand1",
                "keys": "key1",
            },
            "/irapi",
        ),
    ],
)
async def test_all_api_wrappers(
    mock_async_call_api,
    client,
    method_to_test,
    api_method,
    call_args,
    expected_params,
    api_path,
):
    """测试所有API包装方法是否正确调用 _async_call_api。"""
    method = getattr(client, method_to_test)
    mock_async_call_api.return_value = {"code": 0, "message": [{"data": "test"}]}
    await method(*call_args)
    if expected_params is None:
        mock_async_call_api.assert_called_with(api_method, api_path=api_path)
    else:
        mock_async_call_api.assert_called_with(
            api_method, expected_params, api_path=api_path
        )


@pytest.mark.asyncio
async def test_set_multi_eps_async_wrapper(mock_async_call_api, client):
    """测试 set_multi_eps_async 是否正确地将列表序列化为JSON字符串。"""
    io_list = [{"idx": "L1", "val": 1}, {"idx": "L2", "val": 0}]
    agt = "agt1"
    me = "me1"
    await client.set_multi_eps_async(agt, me, io_list)

    expected_params = {"agt": agt, "me": me, "args": json.dumps(io_list)}
    mock_async_call_api.assert_called_with("EpsSet", expected_params, api_path="/api")


@pytest.mark.asyncio
async def test_get_wrappers_empty_or_malformed_response(mock_async_call_api, client):
    """测试 GET 类包装方法在收到空或格式错误的 message 时的处理。"""
    mock_async_call_api.return_value = {"code": 0, "message": []}
    assert await client.async_get_all_devices() == []

    mock_async_call_api.return_value = {"code": 0, "message": None}
    assert await client.get_agt_list_async() == []
    assert await client.get_agt_details_async("h1") == {}

    mock_async_call_api.return_value = {"code": 0, "message": []}
    assert await client.get_epget_async("h1", "d1") == {}
    mock_async_call_api.return_value = {"code": 0, "message": ["not_a_dict"]}
    assert await client.get_epget_async("h1", "d1") == {}


@pytest.mark.asyncio
async def test_set_single_ep_async_direct_call(mock_async_call_api, client):
    """直接测试 set_single_ep_async 方法是否正确调用底层 API。"""
    agt = "agt1"
    me = "me1"
    idx = "L1"
    cmd_type = "0x81"
    val = 1

    await client.set_single_ep_async(agt, me, idx, cmd_type, val)

    expected_params = {
        "agt": agt,
        "me": me,
        "idx": idx,
        "type": cmd_type,
        "val": val,
    }
    mock_async_call_api.assert_called_once_with(
        "EpSet", expected_params, api_path="/api"
    )


# endregion


# region Complex Device Control Helper Method Tests
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "helper_method, args, expected_idx, expected_cmd, expected_val",
    [
        ("turn_on_light_switch_async", ("idx", "agt", "me"), "idx", CMD_TYPE_ON, 1),
        ("turn_off_light_switch_async", ("idx", "agt", "me"), "idx", CMD_TYPE_OFF, 0),
        ("press_switch_async", ("idx", "agt", "me", 550), "idx", CMD_TYPE_PRESS, 6),
        ("press_switch_async", ("idx", "agt", "me", 50), "idx", CMD_TYPE_PRESS, 1),
    ],
)
async def test_simple_control_helpers(
    client, helper_method, args, expected_idx, expected_cmd, expected_val
):
    """测试简单的设备控制辅助方法。"""
    with patch.object(client, "set_single_ep_async") as mock_set:
        method = getattr(client, helper_method)
        await method(*args)
        mock_set.assert_called_with(
            args[1], args[2], expected_idx, expected_cmd, expected_val
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method_name, device_type, expected_idx, expected_cmd, expected_val",
    [
        # --- 定位窗帘 (特殊命令) ---
        ("open_cover_async", list(GARAGE_DOOR_TYPES)[0], "P3", CMD_TYPE_SET_VAL, 100),
        ("close_cover_async", list(GARAGE_DOOR_TYPES)[0], "P3", CMD_TYPE_SET_VAL, 0),
        (
            "stop_cover_async",
            list(GARAGE_DOOR_TYPES)[0],
            "P3",
            CMD_TYPE_SET_CONFIG,
            CMD_TYPE_OFF,
        ),
        ("open_cover_async", list(DOOYA_TYPES)[0], "P2", CMD_TYPE_SET_VAL, 100),
        ("close_cover_async", list(DOOYA_TYPES)[0], "P2", CMD_TYPE_SET_VAL, 0),
        (
            "stop_cover_async",
            list(DOOYA_TYPES)[0],
            "P2",
            CMD_TYPE_SET_CONFIG,
            CMD_TYPE_OFF,
        ),
        # --- 非定位窗帘 (从 NON_POSITIONAL_COVER_CONFIG 映射) ---
        # SL_SW_WIN
        ("open_cover_async", "SL_SW_WIN", "OP", CMD_TYPE_ON, 1),
        ("close_cover_async", "SL_SW_WIN", "CL", CMD_TYPE_ON, 1),
        ("stop_cover_async", "SL_SW_WIN", "ST", CMD_TYPE_ON, 1),
        # SL_P_V2
        ("open_cover_async", "SL_P_V2", "P2", CMD_TYPE_ON, 1),
        ("close_cover_async", "SL_P_V2", "P3", CMD_TYPE_ON, 1),
        ("stop_cover_async", "SL_P_V2", "P4", CMD_TYPE_ON, 1),
        # SL_CN_IF
        ("open_cover_async", "SL_CN_IF", "P1", CMD_TYPE_ON, 1),
        ("close_cover_async", "SL_CN_IF", "P2", CMD_TYPE_ON, 1),
        ("stop_cover_async", "SL_CN_IF", "P3", CMD_TYPE_ON, 1),
        # SL_P (通用控制器)
        ("open_cover_async", "SL_P", "P2", CMD_TYPE_ON, 1),
        ("close_cover_async", "SL_P", "P3", CMD_TYPE_ON, 1),
        ("stop_cover_async", "SL_P", "P4", CMD_TYPE_ON, 1),
    ],
)
async def test_cover_control_helpers(
    client, method_name, device_type, expected_idx, expected_cmd, expected_val
):
    """全面测试 Cover 控制方法对所有设备类型的处理。"""
    with patch.object(client, "set_single_ep_async") as mock_set:
        method = getattr(client, method_name)
        await method("agt", "me", device_type)
        mock_set.assert_called_with(
            "agt", "me", expected_idx, expected_cmd, expected_val
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "device_type, position, expected_idx, expected_cmd, expected_val, should_call",
    [
        (list(DOOYA_TYPES)[0], 50, "P2", CMD_TYPE_SET_VAL, 50, True),
        (list(GARAGE_DOOR_TYPES)[0], 80, "P3", CMD_TYPE_SET_VAL, 80, True),
        ("SL_SW_WIN", 50, None, None, None, False),
    ],
)
async def test_set_cover_position_helper(
    client, device_type, position, expected_idx, expected_cmd, expected_val, should_call
):
    """测试设置窗帘位置的辅助方法。"""
    with patch.object(client, "set_single_ep_async", return_value=0) as mock_set:
        await client.set_cover_position_async("agt", "me", position, device_type)
        if should_call:
            mock_set.assert_called_with(
                "agt", "me", expected_idx, expected_cmd, expected_val
            )
        else:
            mock_set.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "device_type, hvac_mode, current_val, expected_calls",
    [
        # 基础测试：关闭
        ("any_type", HVACMode.OFF, 0, [call("agt", "me", "P1", CMD_TYPE_OFF, 0)]),
        # 简单模式设置
        (
            "V_AIR_P",
            HVACMode.HEAT,
            0,
            [
                call("agt", "me", "P1", CMD_TYPE_ON, 1),
                call("agt", "me", "MODE", CMD_TYPE_SET_CONFIG, 4),
            ],
        ),
        # --- 位运算测试 ---
        # SL_CP_AIR: 设置为 HEAT (mode_val=4), current_val=0b1010...
        (
            "SL_CP_AIR",
            HVACMode.HEAT,
            0b1010101010101010,
            [
                call("agt", "me", "P1", CMD_TYPE_ON, 1),
                call(
                    "agt",
                    "me",
                    "P1",
                    CMD_TYPE_SET_RAW,
                    (0b1010101010101010 & ~(0b11 << 13)) | (1 << 13),
                ),
            ],
        ),
        # SL_CP_DN: 设置为 AUTO (is_auto=1), current_val=0b0101...
        (
            "SL_CP_DN",
            HVACMode.AUTO,
            0b0101010101010101,
            [
                call("agt", "me", "P1", CMD_TYPE_ON, 1),
                call(
                    "agt",
                    "me",
                    "P1",
                    CMD_TYPE_SET_RAW,
                    (0b0101010101010101 & ~(1 << 31)) | (1 << 31),
                ),
            ],
        ),
        # SL_CP_VL: 设置为 HEAT (mode_val=0), current_val=0b1111...
        (
            "SL_CP_VL",
            HVACMode.HEAT,
            0b1111111111111111,
            [
                call("agt", "me", "P1", CMD_TYPE_ON, 1),
                call(
                    "agt",
                    "me",
                    "P1",
                    CMD_TYPE_SET_RAW,
                    (0b1111111111111111 & ~(0b11 << 1)) | (0 << 1),
                ),
            ],
        ),
    ],
)
async def test_set_climate_hvac_mode_helper(
    client, device_type, hvac_mode, current_val, expected_calls
):
    """全面测试设置HVAC模式的辅助方法。"""
    with patch.object(client, "set_single_ep_async") as mock_set:
        await client.async_set_climate_hvac_mode(
            "agt", "me", device_type, hvac_mode, current_val
        )
        # 对于 HVACMode.OFF，只应该有一次调用
        if hvac_mode == HVACMode.OFF:
            mock_set.assert_called_once_with(*expected_calls[0].args)
        else:
            mock_set.assert_has_calls(expected_calls, any_order=True)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "device_type, temp, expected_idx, expected_cmd, expected_val, should_call",
    [
        ("V_AIR_P", 25.5, "tT", CMD_TYPE_SET_TEMP_DECIMAL, 255, True),
        ("SL_CP_DN", 18.0, "P3", CMD_TYPE_SET_RAW, 180, True),
        ("SL_FCU", 22.0, "P8", CMD_TYPE_SET_TEMP_FCU, 220, True),
        ("UNSUPPORTED", 20.0, None, None, None, False),
    ],
)
async def test_set_climate_temperature_helper(
    client, device_type, temp, expected_idx, expected_cmd, expected_val, should_call
):
    """全面测试设置温度的辅助方法。"""
    with patch.object(client, "set_single_ep_async", return_value=0) as mock_set:
        await client.async_set_climate_temperature("agt", "me", device_type, temp)
        if should_call:
            mock_set.assert_called_with(
                "agt", "me", expected_idx, expected_cmd, expected_val
            )
        else:
            mock_set.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "device_type, fan_mode, current_val, expected_idx, expected_cmd, expected_val, should_call",
    [
        ("V_AIR_P", FAN_LOW, 0, "F", CMD_TYPE_SET_CONFIG, 15, True),
        ("SL_TR_ACIPM", FAN_MEDIUM, 0, "P2", CMD_TYPE_SET_RAW, 2, True),
        ("SL_NATURE", FAN_HIGH, 0, "P9", CMD_TYPE_SET_CONFIG, 75, True),
        ("SL_FCU", FAN_AUTO, 0, "P9", CMD_TYPE_SET_CONFIG, 101, True),
        (
            "SL_CP_AIR",
            FAN_LOW,
            0b0,
            "P1",
            CMD_TYPE_SET_RAW,
            (0b0 & ~(0b11 << 15)) | (1 << 15),
            True,
        ),
        ("UNSUPPORTED", FAN_LOW, 0, None, None, None, False),
    ],
)
async def test_set_climate_fan_mode_helper(
    client,
    device_type,
    fan_mode,
    current_val,
    expected_idx,
    expected_cmd,
    expected_val,
    should_call,
):
    with patch.object(client, "set_single_ep_async", return_value=0) as mock_set:
        await client.async_set_climate_fan_mode(
            "agt", "me", device_type, fan_mode, current_val
        )
        if should_call:
            mock_set.assert_called_with(
                "agt", "me", expected_idx, expected_cmd, expected_val
            )
        else:
            mock_set.assert_not_called()


# endregion


@pytest.mark.asyncio
async def test_control_helpers_with_unsupported_device(client, caplog):
    """测试当控制辅助方法遇到不支持的设备类型时的行为。"""
    with patch.object(client, "set_single_ep_async") as mock_set:
        # 测试 cover
        result_cover = await client.open_cover_async("agt", "me", "UNSUPPORTED_TYPE")
        assert result_cover == -1
        mock_set.assert_not_called()
        assert "UNSUPPORTED_TYPE" in caplog.text
        assert "open_cover" in caplog.text

        caplog.clear()
        mock_set.reset_mock()

        # 测试 climate temperature
        result_temp = await client.async_set_climate_temperature(
            "agt", "me", "UNSUPPORTED_TYPE", 25.0
        )
        assert result_temp == -1
        mock_set.assert_not_called()
        # 注意：这个方法当前没有日志记录，所以我们只验证行为

        caplog.clear()
        mock_set.reset_mock()

        # 测试 climate fan mode
        result_fan = await client.async_set_climate_fan_mode(
            "agt", "me", "UNSUPPORTED_TYPE", FAN_LOW
        )
        assert result_fan == -1
        mock_set.assert_not_called()
        assert "UNSUPPORTED_TYPE" in caplog.text
        assert "不支持风扇模式" in caplog.text
