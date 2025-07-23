"""
对 lifesmart_client.py 的全覆盖单元测试。
"""

import json
from unittest.mock import AsyncMock, patch, ANY

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
from custom_components.lifesmart.exceptions import LifeSmartAPIError, LifeSmartAuthError
from custom_components.lifesmart.lifesmart_client import LifeSmartClient


# region Fixtures
@pytest.fixture
def client(hass):
    """提供一个标准的 LifeSmartClient 实例，包含所有必要参数。"""
    return LifeSmartClient(
        hass, "cn2", "appkey", "apptoken", "usertoken", "userid", "password"
    )


@pytest.fixture
def mock_async_call_api():
    """Mock _async_call_api 方法，用于测试上层辅助函数。"""
    with patch(
        "custom_components.lifesmart.lifesmart_client.LifeSmartClient._async_call_api",
        new_callable=AsyncMock,
    ) as mock_func:
        mock_func.return_value = {"code": 0}  # 默认返回成功
        yield mock_func


# endregion


# region Initialization and URL/Header Generation Tests
def test_url_and_header_generation(hass):
    """测试 API/WSS URL 和 HTTP Header 的生成逻辑。"""
    # 场景: 指定区域
    client_region = LifeSmartClient(hass, "cn2", "k", "t", "ut", "uid")
    assert client_region._get_api_url() == "https://api.cn2.ilifesmart.com/app"
    assert client_region.get_wss_url() == "wss://api.cn2.ilifesmart.com:8443/wsapp/"

    # 场景: AUTO/None/空字符串 区域
    for auto_region in ["AUTO", None, ""]:
        client_auto = LifeSmartClient(hass, auto_region, "k", "t", "ut", "uid")
        assert client_auto._get_api_url() == "https://api.ilifesmart.com/app"
        assert client_auto.get_wss_url() == "wss://api.ilifesmart.com:8443/wsapp/"

    # 场景: 验证 Header
    assert client_region._generate_header() == {"Content-Type": "application/json"}


# endregion


# region Core API Call, Signature and Error Handling Tests
@pytest.mark.asyncio
async def test_async_call_api_signature_and_error_handling(client):
    """测试 _async_call_api 的签名生成和对不同错误码的异常处理。"""
    # 场景: 签名逻辑验证 (包含排序)
    with patch.object(client, "_post_and_parse", return_value={"code": 0}) as mock_post:
        await client._async_call_api(
            "TestMethod", {"z_param": "val_z", "a_param": "val_a"}
        )

        # 验证签名原始串的构建顺序
        sdata_arg = mock_post.call_args[0][1]["system"]["sign"]
        call_sdata = client._get_signature(sdata_arg)
        assert "a_param:val_a,z_param:val_z" in call_sdata
        assert sdata_arg == client._get_signature(call_sdata)

    # 场景: 认证失败 (10004, 10005, 10006)
    for auth_error_code in [10004, 10005, 10006]:
        with patch.object(
            client,
            "_post_and_parse",
            return_value={"code": auth_error_code, "message": "auth error"},
        ):
            with pytest.raises(LifeSmartAuthError):
                await client._async_call_api("AnyMethod")

    # 场景: 通用API失败
    with patch.object(
        client, "_post_and_parse", return_value={"code": -1, "message": "general error"}
    ):
        with pytest.raises(LifeSmartAPIError):
            await client._async_call_api("AnyMethod")


@pytest.mark.asyncio
async def test_post_and_parse_all_failures(client):
    """测试 _post_and_parse 的所有网络和解析失败分支。"""
    with patch(
        "custom_components.lifesmart.lifesmart_client.LifeSmartClient._post_async"
    ) as mock_post:
        # 网络层错误
        mock_post.side_effect = ClientError("Connection failed")
        with pytest.raises(LifeSmartAPIError, match="网络请求失败"):
            await client._post_and_parse("http://a.b", {}, {})

        # JSON解析错误
        mock_post.side_effect = None
        mock_post.return_value = "this is not json"
        with pytest.raises(LifeSmartAPIError, match="网络请求失败"):
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
async def test_login_async_full_flow(client):
    """测试登录流程的所有成功和失败分支。"""
    # 场景: 完整成功路径
    with patch.object(client, "_post_and_parse") as mock_post:
        mock_post.side_effect = [
            {"code": "success", "token": "temp_token", "userid": "new_user_id"},
            {
                "code": "success",
                "usertoken": "new_user_token",
                "rgn": "cn1",
                "userid": "new_user_id",
            },
        ]
        result = await client.login_async()
        assert client._usertoken == "new_user_token"
        assert client._region == "cn1"
        assert client._userid == "new_user_id"
        assert result["usertoken"] == "new_user_token"

    # 场景: 步骤1失败
    with patch.object(
        client, "_post_and_parse", return_value={"code": "fail", "message": "pwd error"}
    ):
        with pytest.raises(LifeSmartAuthError, match=r"登录失败 \(步骤1\)"):
            await client.login_async()

    # 场景: 步骤2失败
    with patch.object(client, "_post_and_parse") as mock_post:
        mock_post.side_effect = [
            {"code": "success", "token": "temp_token", "userid": "user_id"},
            {"code": "fail", "message": "auth failed"},
        ]
        with pytest.raises(LifeSmartAuthError, match=r"认证失败 \(步骤2\)"):
            await client.login_async()


@pytest.mark.asyncio
async def test_async_refresh_token_full_flow(client):
    """测试令牌刷新流程的成功和失败分支。"""
    # 场景: 成功
    with patch.object(
        client,
        "_post_and_parse",
        return_value={"code": 0, "usertoken": "refreshed_token"},
    ):
        result = await client.async_refresh_token()
        assert client._usertoken == "refreshed_token"
        assert result["usertoken"] == "refreshed_token"

    # 场景: 失败
    with patch.object(
        client,
        "_post_and_parse",
        return_value={"code": -1, "message": "refresh failed"},
    ):
        with pytest.raises(LifeSmartAuthError, match="刷新令牌失败"):
            await client.async_refresh_token()


def test_generate_wss_auth(client):
    """测试 WebSocket 认证消息的生成。"""
    client._usertoken = "test_wss_token"
    auth_str = client.generate_wss_auth()
    auth_data = json.loads(auth_str)
    assert auth_data["method"] == "WbAuth"
    assert auth_data["system"]["usertoken"] == "test_wss_token"


# endregion


# region Public API Wrapper Method Tests
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method_to_test, api_method, call_args, expected_params, expected_api_path",
    [
        ("get_agt_list_async", "AgtGetList", (), None, "/api"),
        ("get_agt_details_async", "AgtGet", ("hub1",), {"agt": "hub1"}, "/api"),
        ("get_all_device_async", "EpGetAll", (), None, "/api"),
        ("get_scene_list_async", "SceneGet", ("hub1",), {"agt": "hub1"}, "/api"),
        ("get_room_list_async", "RoomGet", ("hub1",), {"agt": "hub1"}, "/api"),
        (
            "set_scene_async",
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
            "send_ir_key_async",
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
    expected_api_path,
):
    """测试所有API包装方法是否正确调用 _async_call_api。"""
    method = getattr(client, method_to_test)
    mock_async_call_api.return_value = {
        "code": 0,
        "message": [{"data": "test"}],
    }  # 模拟有效返回
    await method(*call_args)
    mock_async_call_api.assert_called_with(
        api_method, expected_params or {}, api_path=expected_api_path
    )


@pytest.mark.asyncio
async def test_get_wrappers_empty_or_malformed_response(mock_async_call_api, client):
    """测试 GET 类包装方法在收到空或格式错误的 message 时的处理。"""
    # 场景: message 是空列表
    mock_async_call_api.return_value = {"code": 0, "message": []}
    assert await client.get_all_device_async() == []

    # 场景: message 是 None
    mock_async_call_api.return_value = {"code": 0, "message": None}
    assert await client.get_agt_list_async() == []
    assert await client.get_agt_details_async("h1") == {}

    # 场景: EpGet 返回列表但为空，或格式错误
    mock_async_call_api.return_value = {"code": 0, "message": []}
    assert await client.get_epget_async("h1", "d1") == {}
    mock_async_call_api.return_value = {"code": 0, "message": ["not_a_dict"]}
    assert await client.get_epget_async("h1", "d1") == {}


# endregion


# region Complex Device Control Helper Method Tests
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "helper_method, args, expected_idx, expected_cmd, expected_val",
    [
        ("turn_on_light_switch_async", ("idx", "agt", "me"), "idx", CMD_TYPE_ON, 1),
        ("turn_off_light_switch_async", ("idx", "agt", "me"), "idx", CMD_TYPE_OFF, 0),
        (
            "press_switch_async",
            ("idx", "agt", "me", 550),
            "idx",
            CMD_TYPE_PRESS,
            6,
        ),  # 550ms -> round(5.5) -> 6*100ms
        (
            "press_switch_async",
            ("idx", "agt", "me", 50),
            "idx",
            CMD_TYPE_PRESS,
            1,
        ),  # 50ms -> round(0.5) -> 0, but min is 1
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
    "method, device_type, expected_idx, expected_cmd, expected_val",
    [
        # 开
        ("open_cover_async", "SL_LI_WW", "P1", CMD_TYPE_ON, 1),
        ("open_cover_async", "SL_SW_WIN", "OP", CMD_TYPE_ON, 1),
        ("open_cover_async", list(DOOYA_TYPES)[0], "P2", CMD_TYPE_SET_VAL, 100),
        ("open_cover_async", list(GARAGE_DOOR_TYPES)[0], "P3", CMD_TYPE_SET_VAL, 100),
        # 关
        ("close_cover_async", "SL_LI_WW", "P2", CMD_TYPE_ON, 1),
        ("close_cover_async", "SL_SW_WIN", "CL", CMD_TYPE_ON, 1),
        ("close_cover_async", list(DOOYA_TYPES)[0], "P2", CMD_TYPE_SET_VAL, 0),
        ("close_cover_async", list(GARAGE_DOOR_TYPES)[0], "P3", CMD_TYPE_SET_VAL, 0),
        # 停
        ("stop_cover_async", "SL_LI_WW", "P3", CMD_TYPE_ON, 1),
        ("stop_cover_async", "SL_SW_WIN", "ST", CMD_TYPE_ON, 1),
        (
            "stop_cover_async",
            list(DOOYA_TYPES)[0],
            "P2",
            CMD_TYPE_SET_CONFIG,
            CMD_TYPE_OFF,
        ),
        (
            "stop_cover_async",
            list(GARAGE_DOOR_TYPES)[0],
            "P3",
            CMD_TYPE_SET_CONFIG,
            CMD_TYPE_OFF,
        ),
    ],
)
async def test_cover_control_helpers(
    client, method, device_type, expected_idx, expected_cmd, expected_val
):
    """全面测试 Cover 控制方法对所有设备类型的处理。"""
    with patch.object(client, "set_single_ep_async") as mock_set:
        await getattr(client, method)("agt", "me", device_type)
        mock_set.assert_called_with(
            "agt", "me", expected_idx, expected_cmd, expected_val
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "device_type, position, expected_idx, expected_cmd, expected_val, expected_result",
    [
        (list(DOOYA_TYPES)[0], 50, "P2", CMD_TYPE_SET_VAL, 50, ANY),
        (list(GARAGE_DOOR_TYPES)[0], 80, "P3", CMD_TYPE_SET_VAL, 80, ANY),
        ("SL_SW_WIN", 50, None, None, None, -1),  # 不支持
    ],
)
async def test_set_cover_position_helper(
    client,
    device_type,
    position,
    expected_idx,
    expected_cmd,
    expected_val,
    expected_result,
):
    """测试设置窗帘位置的辅助方法。"""
    with patch.object(client, "set_single_ep_async", return_value=0) as mock_set:
        result = await client.set_cover_position_async(
            "agt", "me", position, device_type
        )
        if expected_result == -1:
            mock_set.assert_not_called()
            assert result == -1
        else:
            mock_set.assert_called_with(
                "agt", "me", expected_idx, expected_cmd, expected_val
            )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "device_type, hvac_mode, current_val, expected_calls",
    [
        # Turn OFF
        ("any_type", HVACMode.OFF, 0, [("P1", CMD_TYPE_OFF, 0)]),
        # Simple Mode Set (SL_UACCB, SL_NATURE, SL_FCU, V_AIR_P)
        (
            "SL_UACCB",
            HVACMode.COOL,
            0,
            [("P1", CMD_TYPE_ON, 1), ("P7", CMD_TYPE_SET_CONFIG, 3)],
        ),
        (
            "V_AIR_P",
            HVACMode.HEAT,
            0,
            [("P1", CMD_TYPE_ON, 1), ("MODE", CMD_TYPE_SET_CONFIG, 4)],
        ),
        # Bitmasking (SL_CP_AIR)
        (
            "SL_CP_AIR",
            HVACMode.HEAT,
            0b0,
            [
                ("P1", CMD_TYPE_ON, 1),
                ("P1", CMD_TYPE_SET_RAW, (0b0 & ~(0b11 << 13)) | (1 << 13)),
            ],
        ),
        # Bitmasking (SL_CP_DN)
        (
            "SL_CP_DN",
            HVACMode.AUTO,
            0,
            [
                ("P1", CMD_TYPE_ON, 1),
                ("P1", CMD_TYPE_SET_RAW, (0 & ~(1 << 31)) | (1 << 31)),
            ],
        ),
        # Bitmasking (SL_CP_VL)
        (
            "SL_CP_VL",
            HVACMode.HEAT,
            0b100,
            [
                ("P1", CMD_TYPE_ON, 1),
                ("P1", CMD_TYPE_SET_RAW, (0b100 & ~(0b11 << 1)) | (0 << 1)),
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
        assert mock_set.call_count == len(expected_calls)
        for idx, cmd, val in expected_calls:
            mock_set.assert_any_call("agt", "me", idx, cmd, val)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "device_type, temp, expected_idx, expected_cmd, expected_val",
    [
        ("V_AIR_P", 25.5, "tT", CMD_TYPE_SET_TEMP_DECIMAL, 255),
        ("SL_UACCB", 26.0, "P3", CMD_TYPE_SET_TEMP_DECIMAL, 260),
        ("SL_CP_DN", 18.0, "P3", CMD_TYPE_SET_RAW, 180),
        ("SL_CP_AIR", 22.5, "P4", CMD_TYPE_SET_RAW, 225),
        ("SL_NATURE", 23.0, "P8", CMD_TYPE_SET_TEMP_DECIMAL, 230),
        ("SL_FCU", 24.5, "P8", CMD_TYPE_SET_TEMP_FCU, 245),
        ("SL_CP_VL", 20.0, "P3", CMD_TYPE_SET_RAW, 200),
        ("UNSUPPORTED", 20.0, None, None, None),  # 不支持的类型
    ],
)
async def test_set_climate_temperature_helper(
    client, device_type, temp, expected_idx, expected_cmd, expected_val
):
    """全面测试设置温度的辅助方法。"""
    with patch.object(client, "set_single_ep_async", return_value=0) as mock_set:
        result = await client.async_set_climate_temperature(
            "agt", "me", device_type, temp
        )
        if expected_idx is None:
            mock_set.assert_not_called()
            assert result == -1
        else:
            mock_set.assert_called_with(
                "agt", "me", expected_idx, expected_cmd, expected_val
            )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "device_type, fan_mode, current_val, expected_idx, expected_cmd, expected_val, expected_result",
    [
        ("V_AIR_P", FAN_LOW, 0, "F", CMD_TYPE_SET_CONFIG, 15, ANY),
        ("SL_TR_ACIPM", FAN_MEDIUM, 0, "P2", CMD_TYPE_SET_RAW, 2, ANY),
        ("SL_NATURE", FAN_HIGH, 0, "P9", CMD_TYPE_SET_CONFIG, 75, ANY),
        ("SL_FCU", FAN_AUTO, 0, "P9", CMD_TYPE_SET_CONFIG, 101, ANY),
        (
            "SL_CP_AIR",
            FAN_LOW,
            0b0,
            "P1",
            CMD_TYPE_SET_RAW,
            (0b0 & ~(0b11 << 15)) | (1 << 15),
            ANY,
        ),
        ("UNSUPPORTED", FAN_LOW, 0, None, None, None, -1),
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
    expected_result,
):
    with patch.object(client, "set_single_ep_async", return_value=0) as mock_set:
        result = await client.async_set_climate_fan_mode(
            "agt", "me", device_type, fan_mode, current_val
        )
        if expected_result == -1:
            mock_set.assert_not_called()
            assert result == -1
        else:
            mock_set.assert_called_with(
                "agt", "me", expected_idx, expected_cmd, expected_val
            )


# endregion
