"""
LifeSmart OpenAPI 客户端测试套件。

此测试套件提供对 openapi_client.py 的全面覆盖，包括：
- 客户端初始化和配置管理
- 核心 API 调用机制和签名验证
- 认证流程（登录、刷新令牌）
- WebSocket 连接管理
- 设备控制辅助方法
- 错误处理和边界条件
- 网络异常和恢复机制

测试使用结构化的类组织，每个类专注于特定的功能领域，
并包含详细的中文注释以确保可维护性。
"""

import json
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import ClientError
from homeassistant.components.climate import (
    HVACMode,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_HIGH,
    FAN_AUTO,
)

from custom_components.lifesmart.core.const import (
    CMD_TYPE_ON,
    CMD_TYPE_OFF,
    CMD_TYPE_PRESS,
    CMD_TYPE_SET_VAL,
    CMD_TYPE_SET_CONFIG,
    CMD_TYPE_SET_TEMP_DECIMAL,
    CMD_TYPE_SET_RAW_ON,
    CMD_TYPE_SET_TEMP_FCU,
    GARAGE_DOOR_TYPES,
    DOOYA_TYPES,
)
from custom_components.lifesmart.core.exceptions import (
    LifeSmartAPIError,
    LifeSmartAuthError,
)
from custom_components.lifesmart.core.openapi_client import LifeSmartOAPIClient


# ==================== 测试数据和Fixtures ====================


@pytest.fixture
def client_config():
    """提供标准的客户端配置参数。"""
    return {
        "region": "cn2",
        "appkey": "test_appkey",
        "apptoken": "test_apptoken",
        "usertoken": "test_usertoken",
        "userid": "test_userid",
        "user_password": "test_password",
    }


@pytest.fixture
def client(hass, client_config):
    """提供一个标准的 LifeSmartOAPIClient 实例，包含所有必要参数。"""
    return LifeSmartOAPIClient(
        hass,
        client_config["region"],
        client_config["appkey"],
        client_config["apptoken"],
        client_config["usertoken"],
        client_config["userid"],
        client_config["user_password"],
    )


@pytest.fixture
def mock_async_call_api():
    """Mock _async_call_api 方法，用于测试上层辅助函数。"""
    with patch(
        "custom_components.lifesmart.core.openapi_client.LifeSmartOAPIClient._async_call_api",
        new_callable=AsyncMock,
    ) as mock_func:
        mock_func.return_value = {"code": 0, "message": "success"}  # 默认返回成功
        yield mock_func


@pytest.fixture
def mock_post_response():
    """提供标准的HTTP响应模拟。"""
    return {"code": 0, "message": {"data": "test_response"}}


# ==================== 基础功能测试类 ====================


class TestClientInitialization:
    """测试客户端初始化和基础配置功能。"""

    def test_client_initialization_with_all_params(self, hass, client_config):
        """测试使用完整参数初始化客户端。"""
        client = LifeSmartOAPIClient(
            hass,
            client_config["region"],
            client_config["appkey"],
            client_config["apptoken"],
            client_config["usertoken"],
            client_config["userid"],
            client_config["user_password"],
        )

        assert client.hass == hass, "Home Assistant实例应该正确设置"
        assert client._region == client_config["region"], "区域应该正确设置"
        assert client._appkey == client_config["appkey"], "AppKey应该正确设置"
        assert client._apptoken == client_config["apptoken"], "AppToken应该正确设置"
        assert client._usertoken == client_config["usertoken"], "UserToken应该正确设置"
        assert client._userid == client_config["userid"], "UserID应该正确设置"
        assert client._apppassword == client_config["user_password"], "密码应该正确设置"

    def test_client_initialization_without_password(self, hass, client_config):
        """测试不提供密码参数的初始化。"""
        client = LifeSmartOAPIClient(
            hass,
            client_config["region"],
            client_config["appkey"],
            client_config["apptoken"],
            client_config["usertoken"],
            client_config["userid"],
        )

        assert client._apppassword is None, "未提供密码时应该为None"


class TestURLAndConfiguration:
    """测试URL生成和配置管理功能。"""

    @pytest.mark.parametrize(
        "region, expected_api_url, expected_wss_url",
        [
            (
                "cn2",
                "https://api.cn2.ilifesmart.com/app",
                "wss://api.cn2.ilifesmart.com:8443/wsapp/",
            ),
            (
                "us",
                "https://api.us.ilifesmart.com/app",
                "wss://api.us.ilifesmart.com:8443/wsapp/",
            ),
            (
                "AUTO",
                "https://api.ilifesmart.com/app",
                "wss://api.ilifesmart.com:8443/wsapp/",
            ),
            (
                "",
                "https://api.ilifesmart.com/app",
                "wss://api.ilifesmart.com:8443/wsapp/",
            ),
            (
                None,
                "https://api.ilifesmart.com/app",
                "wss://api.ilifesmart.com:8443/wsapp/",
            ),
        ],
        ids=["ChinaRegion", "USRegion", "AutoRegion", "EmptyRegion", "NullRegion"],
    )
    def test_url_generation_for_different_regions(
        self, hass, region, expected_api_url, expected_wss_url
    ):
        """测试不同区域的API和WebSocket URL生成逻辑。"""
        client = LifeSmartOAPIClient(hass, region, "k", "t", "ut", "uid")

        assert (
            client._get_api_url() == expected_api_url
        ), f"区域{region}的API URL应该正确"
        assert (
            client.get_wss_url() == expected_wss_url
        ), f"区域{region}的WSS URL应该正确"

    def test_http_header_generation(self, client):
        """测试HTTP请求头的生成。"""
        headers = client._generate_header()
        expected_headers = {"Content-Type": "application/json"}

        assert headers == expected_headers, "HTTP请求头应该正确生成"

    def test_signature_generation(self, client):
        """测试MD5签名生成功能。"""
        test_data = "method:TestMethod,time:1234567890,userid:testuser,usertoken:testtoken,appkey:testkey,apptoken:testtoken"
        signature = client._get_signature(test_data)

        assert isinstance(signature, str), "签名应该是字符串类型"
        assert len(signature) == 32, "MD5签名应该是32位十六进制字符串"

        # 验证相同输入生成相同签名
        signature2 = client._get_signature(test_data)
        assert signature == signature2, "相同输入应该生成相同签名"


# ==================== 核心API调用测试类 ====================


class TestCoreAPICall:
    """测试核心API调用机制，包括签名生成和错误处理。"""

    @pytest.mark.asyncio
    async def test_async_call_api_with_parameters(self, client):
        """测试带参数的API调用和签名生成。"""
        with (
            patch.object(
                client, "_post_and_parse", return_value={"code": 0}
            ) as mock_post,
            patch(
                "custom_components.lifesmart.core.openapi_client.LifeSmartOAPIClient._get_signature"
            ) as mock_get_signature,
        ):
            mock_get_signature.return_value = "mocked_signature"

            # 测试带参数的API调用
            await client._async_call_api(
                "TestMethodWithParams", {"z_param": "val_z", "a_param": "val_a"}
            )

            mock_get_signature.assert_called_once()
            signature_raw_string = mock_get_signature.call_args.args[0]
            assert (
                "a_param:val_a,z_param:val_z" in signature_raw_string
            ), "签名字符串应包含按字母序排列的参数"

            sent_payload = mock_post.call_args.args[1]
            assert (
                sent_payload["system"]["sign"] == "mocked_signature"
            ), "发送的负载中应包含正确的签名"
            assert "params" in sent_payload, "带参数的请求应包含params字段"

    @pytest.mark.asyncio
    async def test_async_call_api_without_parameters(self, client):
        """测试无参数的API调用。"""
        with (
            patch.object(
                client, "_post_and_parse", return_value={"code": 0}
            ) as mock_post,
            patch(
                "custom_components.lifesmart.core.openapi_client.LifeSmartOAPIClient._get_signature"
            ) as mock_get_signature,
        ):
            mock_get_signature.return_value = "mocked_signature"

            await client._async_call_api("TestMethodNoParams")

            mock_get_signature.assert_called_once()
            signature_raw_string = mock_get_signature.call_args.args[0]
            assert (
                "a_param" not in signature_raw_string
            ), "无参数时签名字符串中不应包含参数"

            sent_payload = mock_post.call_args.args[1]
            assert "params" not in sent_payload, "无参数请求中不应包含params字段"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "error_code, expected_exception",
        [
            (10004, LifeSmartAuthError),
            (10005, LifeSmartAuthError),
            (10006, LifeSmartAuthError),
            (-1, LifeSmartAPIError),
            (500, LifeSmartAPIError),
        ],
        ids=[
            "AuthError10004",
            "AuthError10005",
            "AuthError10006",
            "GeneralError",
            "ServerError",
        ],
    )
    async def test_async_call_api_error_handling(
        self, client, error_code, expected_exception
    ):
        """测试不同错误码的异常处理。"""
        with patch.object(
            client,
            "_post_and_parse",
            return_value={"code": error_code, "message": "error"},
        ):
            with pytest.raises(expected_exception):
                await client._async_call_api("AnyMethod")

    @pytest.mark.asyncio
    async def test_post_and_parse_network_failure(self, client):
        """测试网络请求失败的处理。"""
        with patch(
            "custom_components.lifesmart.core.openapi_client.LifeSmartOAPIClient._post_async",
            new_callable=AsyncMock,
        ) as mock_post:
            mock_post.side_effect = ClientError("Connection failed")

            with pytest.raises(LifeSmartAPIError, match="网络请求失败"):
                await client._post_and_parse("http://test.com", {}, {})

    @pytest.mark.asyncio
    async def test_post_and_parse_json_decode_failure(self, client):
        """测试JSON解析失败的处理。"""
        with patch(
            "custom_components.lifesmart.core.openapi_client.LifeSmartOAPIClient._post_async",
            new_callable=AsyncMock,
        ) as mock_post:
            mock_post.return_value = "invalid json response"

            with pytest.raises(LifeSmartAPIError, match="JSON解析失败"):
                await client._post_and_parse("http://test.com", {}, {})

    @pytest.mark.parametrize(
        "response, expected_code",
        [
            (None, -1),
            ({"message": "no code"}, -1),
            ({"code": "not_an_int"}, -1),
            ({"code": None}, -1),
            ({"code": 0}, 0),
            ({"code": "123"}, 123),
        ],
        ids=[
            "NullResponse",
            "MissingCode",
            "InvalidCode",
            "NullCode",
            "ValidZero",
            "ValidString",
        ],
    )
    def test_get_code_from_response_edge_cases(self, client, response, expected_code):
        """测试响应码提取的各种边界情况。"""
        result = client._get_code_from_response(response, "test_method")
        assert result == expected_code, f"响应 {response} 应该返回 {expected_code}"


# ==================== 认证和WebSocket测试类 ====================


class TestAuthenticationFlow:
    """测试认证流程，包括登录和令牌刷新。"""

    @pytest.mark.asyncio
    async def test_login_async_successful_flow(self, client):
        """测试完整的登录认证成功流程。"""
        # 模拟两步认证响应
        step1_response = {
            "code": "success",
            "token": "temp_token",
            "userid": "new_user_id",
        }
        step2_response = {
            "code": "success",
            "usertoken": "new_user_token",
            "rgn": "cn1",
            "userid": "new_user_id",
        }

        with patch.object(client, "_post_and_parse") as mock_post:
            mock_post.side_effect = [step1_response, step2_response]

            result = await client.login_async()

            assert client._usertoken == "new_user_token", "客户端应更新为新的用户令牌"
            assert client._region == "cn1", "客户端应更新为新的区域"
            assert client._userid == "new_user_id", "客户端应更新为新的用户ID"
            assert result["usertoken"] == "new_user_token", "返回结果应包含新的用户令牌"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "userid, apppassword, expected_error",
        [
            (None, "valid_pass", "用户名或应用密码无效，无法登录。"),
            ("", "valid_pass", "用户名或应用密码无效，无法登录。"),
            ("valid_user", None, "用户名或应用密码无效，无法登录。"),
            ("valid_user", "", "用户名或应用密码无效，无法登录。"),
        ],
        ids=["NullUserid", "EmptyUserid", "NullPassword", "EmptyPassword"],
    )
    async def test_login_async_invalid_credentials(
        self, client, userid, apppassword, expected_error
    ):
        """测试无效凭据时的登录失败。"""
        original_userid = client._userid
        original_apppassword = client._apppassword

        try:
            client._userid = userid
            client._apppassword = apppassword

            with pytest.raises(LifeSmartAuthError, match=expected_error):
                await client.login_async()
        finally:
            # 恢复原始值
            client._userid = original_userid
            client._apppassword = original_apppassword

    @pytest.mark.asyncio
    async def test_refresh_token_successful_flow(self, client):
        """测试令牌刷新成功流程。"""
        mock_response = {"code": 0, "usertoken": "refreshed_token"}

        with patch.object(client, "_post_and_parse") as mock_post:
            mock_post.return_value = mock_response

            result = await client.async_refresh_token()

            assert client._usertoken == "refreshed_token", "客户端令牌应该被刷新"
            assert (
                result["usertoken"] == "refreshed_token"
            ), "返回结果应包含刷新后的令牌"

    @pytest.mark.asyncio
    async def test_refresh_token_failure(self, client):
        """测试令牌刷新失败的处理。"""
        with patch.object(client, "_post_and_parse") as mock_post:
            mock_post.side_effect = LifeSmartAuthError("刷新失败")

            with pytest.raises(LifeSmartAuthError):
                await client.async_refresh_token()


class TestWebSocketManagement:
    """测试WebSocket连接管理功能。"""

    def test_generate_wss_auth_message(self, client):
        """测试WebSocket认证消息的生成。"""
        client._usertoken = "test_wss_token"
        auth_str = client.generate_wss_auth()
        auth_data = json.loads(auth_str)

        assert "system" in auth_data, "WebSocket认证数据应包含system字段"
        assert "sign" in auth_data["system"], "system字段应包含签名"
        assert "userid" in auth_data["system"], "system字段应包含用户ID"
        assert auth_data["method"] == "WbAuth", "认证方法应该是WbAuth"

    @pytest.mark.parametrize(
        "region, expected_wss_url",
        [
            ("cn2", "wss://api.cn2.ilifesmart.com:8443/wsapp/"),
            ("us", "wss://api.us.ilifesmart.com:8443/wsapp/"),
            ("AUTO", "wss://api.ilifesmart.com:8443/wsapp/"),
            (None, "wss://api.ilifesmart.com:8443/wsapp/"),
        ],
        ids=["ChinaRegion", "USRegion", "AutoRegion", "NullRegion"],
    )
    def test_wss_url_generation_for_regions(self, hass, region, expected_wss_url):
        """测试不同区域的WebSocket URL生成。"""
        client = LifeSmartOAPIClient(hass, region, "k", "t", "ut", "uid")
        wss_url = client.get_wss_url()

        assert wss_url == expected_wss_url, f"区域{region}的WebSocket URL应该正确"


# ==================== API包装方法测试类 ====================


class TestAPIWrapperMethods:
    """测试所有公共API包装方法的功能。"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "method_name, api_method, args, expected_params, api_path",
        [
            ("get_agt_list_async", "AgtGetList", (), None, "/api"),
            ("get_agt_details_async", "AgtGet", ("hub1",), {"agt": "hub1"}, "/api"),
            ("async_get_all_devices", "EpGetAll", (), None, "/api"),
            ("get_scene_list_async", "SceneGet", ("hub1",), {"agt": "hub1"}, "/api"),
            ("get_room_list_async", "RoomGet", ("hub1",), {"agt": "hub1"}, "/api"),
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
                ("hub1", "me1", "cat1", "brand1", "key1", "ai1"),
                {
                    "agt": "hub1",
                    "me": "me1",
                    "category": "cat1",
                    "brand": "brand1",
                    "keys": "key1",
                    "ai": "ai1",
                },
                "/irapi",
            ),
        ],
        ids=[
            "GetAgtList",
            "GetAgtDetails",
            "GetAllDevices",
            "GetSceneList",
            "GetRoomList",
            "GetEpDetails",
            "GetIRRemoteList",
            "SendIRKey",
        ],
    )
    async def test_api_wrapper_methods(
        self,
        mock_async_call_api,
        client,
        method_name,
        api_method,
        args,
        expected_params,
        api_path,
    ):
        """测试所有API包装方法是否正确调用_async_call_api。"""
        method = getattr(client, method_name)
        mock_async_call_api.return_value = {"code": 0, "message": [{"data": "test"}]}

        await method(*args)

        if expected_params is None:
            mock_async_call_api.assert_called_with(api_method, api_path=api_path)
        else:
            mock_async_call_api.assert_called_with(
                api_method, expected_params, api_path=api_path
            )

    @pytest.mark.asyncio
    async def test_set_single_ep_async_direct(self, mock_async_call_api, client):
        """测试单个端点设置方法的直接调用。"""
        await client.set_single_ep_async("agt1", "me1", "L1", "0x81", 1)

        expected_params = {
            "agt": "agt1",
            "me": "me1",
            "idx": "L1",
            "type": "0x81",
            "val": 1,
        }
        mock_async_call_api.assert_called_once_with(
            "EpSet", expected_params, api_path="/api"
        )

    @pytest.mark.asyncio
    async def test_set_multi_eps_async_json_serialization(
        self, mock_async_call_api, client
    ):
        """测试多端点设置方法的JSON序列化。"""
        io_list = [{"idx": "L1", "val": 1}, {"idx": "L2", "val": 0}]

        await client.set_multi_eps_async("agt1", "me1", io_list)

        expected_params = {"agt": "agt1", "me": "me1", "args": json.dumps(io_list)}
        mock_async_call_api.assert_called_with(
            "EpsSet", expected_params, api_path="/api"
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "response_message, expected_result",
        [
            ([], []),
            (None, []),
            ([{"data": "valid"}], [{"data": "valid"}]),
            ("not_a_list", []),
        ],
        ids=["EmptyList", "NullMessage", "ValidList", "InvalidType"],
    )
    async def test_list_methods_response_handling(
        self, mock_async_call_api, client, response_message, expected_result
    ):
        """测试返回列表的方法对各种响应的处理。"""
        mock_async_call_api.return_value = {"code": 0, "message": response_message}

        result = await client.get_agt_list_async()
        assert (
            result == expected_result
        ), f"响应 {response_message} 应该返回 {expected_result}"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "response_message, expected_result",
        [
            ({}, {}),
            (None, {}),
            ({"valid": "data"}, {"valid": "data"}),
            ("not_a_dict", {}),
            ([], {}),
        ],
        ids=["EmptyDict", "NullMessage", "ValidDict", "InvalidString", "InvalidList"],
    )
    async def test_dict_methods_response_handling(
        self, mock_async_call_api, client, response_message, expected_result
    ):
        """测试返回字典的方法对各种响应的处理。"""
        mock_async_call_api.return_value = {"code": 0, "message": response_message}

        result = await client.get_agt_details_async("hub1")
        assert (
            result == expected_result
        ), f"响应 {response_message} 应该返回 {expected_result}"

    @pytest.mark.asyncio
    async def test_get_epget_async_list_response_handling(
        self, mock_async_call_api, client
    ):
        """测试EpGet方法的特殊列表响应处理逻辑。"""
        # EpGet返回的是列表，但我们取第一个元素
        mock_async_call_api.return_value = {"code": 0, "message": [{"devices": "data"}]}
        result = await client.get_epget_async("hub1", "dev1")
        assert result == {"devices": "data"}, "应该返回列表中的第一个元素"

        # 测试空列表的情况
        mock_async_call_api.return_value = {"code": 0, "message": []}
        result = await client.get_epget_async("hub1", "dev1")
        assert result == {}, "空列表应该返回空字典"

    @pytest.mark.asyncio
    async def test_async_set_scene_method(self, mock_async_call_api, client):
        """测试云端场景触发的两步骤逻辑：先获取场景列表，再根据ID触发场景。"""
        # 模拟场景列表返回
        scene_list = [
            {"id": "scene_001", "name": "morning_scene"},
            {"id": "scene_002", "name": "evening_scene"},
            {"id": "scene_003", "name": "test_scene"},
        ]

        # 设置SceneGet API返回的场景列表
        scene_get_response = {"code": 0, "message": scene_list}
        # 设置SceneSet API返回成功
        scene_set_response = {"code": 0, "message": "success"}

        # 配置mock按顺序返回不同响应
        mock_async_call_api.side_effect = [scene_get_response, scene_set_response]

        # 测试触发存在的场景
        result = await client._async_set_scene("test_agt", "test_scene")

        # 验证返回值
        assert result == 0, "场景触发成功应该返回0"

        # 验证API调用顺序和参数
        assert mock_async_call_api.call_count == 2, "应该调用两次API"

        # 验证第一次调用是SceneGet
        first_call = mock_async_call_api.call_args_list[0]
        assert first_call[0][0] == "SceneGet", "第一次调用应该是SceneGet"
        assert first_call[0][1] == {"agt": "test_agt"}, "SceneGet应该传递正确的参数"
        assert first_call[1]["api_path"] == "/api", "应该使用正确的API路径"

        # 验证第二次调用是SceneSet
        second_call = mock_async_call_api.call_args_list[1]
        assert second_call[0][0] == "SceneSet", "第二次调用应该是SceneSet"
        assert second_call[0][1] == {
            "agt": "test_agt",
            "id": "scene_003",
        }, "SceneSet应该使用找到的场景ID"
        assert second_call[1]["api_path"] == "/api", "应该使用正确的API路径"

    @pytest.mark.asyncio
    async def test_async_set_scene_scene_not_found(self, mock_async_call_api, client):
        """测试场景不存在时的处理逻辑。"""
        # 模拟场景列表不包含目标场景
        scene_list = [
            {"id": "scene_001", "name": "morning_scene"},
            {"id": "scene_002", "name": "evening_scene"},
        ]

        scene_get_response = {"code": 0, "message": scene_list}
        mock_async_call_api.return_value = scene_get_response

        # 测试触发不存在的场景
        result = await client._async_set_scene("test_agt", "nonexistent_scene")

        # 验证返回值
        assert result == -1, "场景不存在时应该返回-1"

        # 验证只调用了SceneGet，没有调用SceneSet
        assert mock_async_call_api.call_count == 1, "场景不存在时只应该调用一次SceneGet"

        call = mock_async_call_api.call_args_list[0]
        assert call[0][0] == "SceneGet", "调用应该是SceneGet"


# ==================== 设备控制辅助方法测试类 ====================


class TestDeviceControlHelpers:
    """测试设备控制的辅助方法功能。"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "helper_method, args, expected_idx, expected_cmd, expected_val",
        [
            ("turn_on_light_switch_async", ("idx", "agt", "me"), "idx", CMD_TYPE_ON, 1),
            (
                "turn_off_light_switch_async",
                ("idx", "agt", "me"),
                "idx",
                CMD_TYPE_OFF,
                0,
            ),
            ("press_switch_async", ("idx", "agt", "me", 550), "idx", CMD_TYPE_PRESS, 6),
            ("press_switch_async", ("idx", "agt", "me", 50), "idx", CMD_TYPE_PRESS, 1),
        ],
        ids=["TurnOnLight", "TurnOffLight", "LongPress", "ShortPress"],
    )
    async def test_basic_switch_control_helpers(
        self, client, helper_method, args, expected_idx, expected_cmd, expected_val
    ):
        """测试基础开关控制辅助方法。"""
        with patch.object(client, "set_single_ep_async") as mock_set:
            method = getattr(client, helper_method)
            await method(*args)
            mock_set.assert_called_with(
                args[1], args[2], expected_idx, expected_cmd, expected_val
            )


class TestCoverControlHelpers:
    """测试窗帘控制辅助方法的功能。"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "method_name, device_type, expected_calls",
        [
            # 定位窗帘 - GARAGE_DOOR类型
            (
                "open_cover_async",
                list(GARAGE_DOOR_TYPES)[0],
                [("P3", CMD_TYPE_SET_VAL, 100)],
            ),
            (
                "close_cover_async",
                list(GARAGE_DOOR_TYPES)[0],
                [("P3", CMD_TYPE_SET_VAL, 0)],
            ),
            (
                "stop_cover_async",
                list(GARAGE_DOOR_TYPES)[0],
                [("P3", CMD_TYPE_SET_CONFIG, CMD_TYPE_OFF)],
            ),
            # 定位窗帘 - DOOYA类型
            ("open_cover_async", list(DOOYA_TYPES)[0], [("P2", CMD_TYPE_SET_VAL, 100)]),
            ("close_cover_async", list(DOOYA_TYPES)[0], [("P2", CMD_TYPE_SET_VAL, 0)]),
            (
                "stop_cover_async",
                list(DOOYA_TYPES)[0],
                [("P2", CMD_TYPE_SET_CONFIG, CMD_TYPE_OFF)],
            ),
            # 非定位窗帘
            ("open_cover_async", "SL_SW_WIN", [("OP", CMD_TYPE_ON, 1)]),
            ("close_cover_async", "SL_SW_WIN", [("CL", CMD_TYPE_ON, 1)]),
            ("stop_cover_async", "SL_SW_WIN", [("ST", CMD_TYPE_ON, 1)]),
        ],
        ids=[
            "GarageDoorOpen",
            "GarageDoorClose",
            "GarageDoorStop",
            "DooyaOpen",
            "DooyaClose",
            "DooyaStop",
            "NonPositionalOpen",
            "NonPositionalClose",
            "NonPositionalStop",
        ],
    )
    async def test_cover_control_methods(
        self, client, method_name, device_type, expected_calls
    ):
        """测试窗帘控制方法对不同设备类型的处理。"""
        with patch.object(client, "set_single_ep_async") as mock_set:
            method = getattr(client, method_name)
            await method("agt", "me", device_type)

            for expected_idx, expected_cmd, expected_val in expected_calls:
                mock_set.assert_called_with(
                    "agt", "me", expected_idx, expected_cmd, expected_val
                )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "device_type, position, should_call, expected_args",
        [
            (list(DOOYA_TYPES)[0], 50, True, ("P2", CMD_TYPE_SET_VAL, 50)),
            (list(GARAGE_DOOR_TYPES)[0], 80, True, ("P3", CMD_TYPE_SET_VAL, 80)),
            ("SL_SW_WIN", 50, False, None),  # 非定位窗帘不支持位置设置
        ],
        ids=["DooyaPosition", "GarageDoorPosition", "NonPositionalUnsupported"],
    )
    async def test_set_cover_position_method(
        self, client, device_type, position, should_call, expected_args
    ):
        """测试窗帘位置设置方法。"""
        with patch.object(client, "set_single_ep_async", return_value=0) as mock_set:
            await client.set_cover_position_async("agt", "me", position, device_type)

            if should_call:
                mock_set.assert_called_with("agt", "me", *expected_args)
            else:
                mock_set.assert_not_called()


class TestClimateControlHelpers:
    """测试气候设备控制辅助方法的功能。"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "device_type, hvac_mode, current_val, expected_calls_count",
        [
            ("any_type", HVACMode.OFF, 0, 1),  # 关闭只调用一次
            ("V_AIR_P", HVACMode.HEAT, 0, 2),  # 开启和设置模式
            ("SL_CP_AIR", HVACMode.COOL, 0b1010101010101010, 2),  # 位运算模式
        ],
        ids=["TurnOff", "SimpleMode", "BitwiseMode"],
    )
    async def test_climate_hvac_mode_control(
        self, client, device_type, hvac_mode, current_val, expected_calls_count
    ):
        """测试HVAC模式控制方法。"""
        with patch.object(client, "set_single_ep_async") as mock_set:
            await client.async_set_climate_hvac_mode(
                "agt", "me", device_type, hvac_mode, current_val
            )
            assert (
                mock_set.call_count == expected_calls_count
            ), f"应该调用{expected_calls_count}次"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "device_type, temperature, expected_conversion",
        [
            ("V_AIR_P", 25.5, ("tT", CMD_TYPE_SET_TEMP_DECIMAL, 255)),
            ("SL_CP_DN", 18.0, ("P3", CMD_TYPE_SET_RAW_ON, 180)),
            ("SL_FCU", 22.0, ("P8", CMD_TYPE_SET_TEMP_FCU, 220)),
            ("UNSUPPORTED", 20.0, None),
        ],
        ids=["DecimalTemp", "RawTemp", "FCUTemp", "UnsupportedDevice"],
    )
    async def test_climate_temperature_control(
        self, client, device_type, temperature, expected_conversion
    ):
        """测试温度控制方法。"""
        with patch.object(client, "set_single_ep_async", return_value=0) as mock_set:
            await client.async_set_climate_temperature(
                "agt", "me", device_type, temperature
            )

            if expected_conversion:
                mock_set.assert_called_with("agt", "me", *expected_conversion)
            else:
                mock_set.assert_not_called()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "device_type, fan_mode, current_val, expected_conversion",
        [
            ("V_AIR_P", FAN_LOW, 0, ("F", CMD_TYPE_SET_CONFIG, 15)),
            ("SL_TR_ACIPM", FAN_MEDIUM, 0, ("P2", CMD_TYPE_SET_RAW_ON, 2)),
            ("SL_NATURE", FAN_HIGH, 0, ("P9", CMD_TYPE_SET_CONFIG, 75)),
            ("SL_FCU", FAN_AUTO, 0, ("P9", CMD_TYPE_SET_CONFIG, 101)),
            ("UNSUPPORTED", FAN_LOW, 0, None),
        ],
        ids=[
            "V_AIR_P_Low",
            "TR_ACIPM_Medium",
            "Nature_High",
            "FCU_Auto",
            "UnsupportedDevice",
        ],
    )
    async def test_climate_fan_mode_control(
        self, client, device_type, fan_mode, current_val, expected_conversion
    ):
        """测试风扇模式控制方法。"""
        with patch.object(client, "set_single_ep_async", return_value=0) as mock_set:
            await client.async_set_climate_fan_mode(
                "agt", "me", device_type, fan_mode, current_val
            )

            if expected_conversion:
                mock_set.assert_called_with("agt", "me", *expected_conversion)
            else:
                mock_set.assert_not_called()


# ==================== 错误处理和边界条件测试类 ====================


class TestErrorHandlingAndEdgeCases:
    """测试错误处理和各种边界条件。"""

    @pytest.mark.asyncio
    async def test_unsupported_device_type_handling(self, client, caplog):
        """测试不支持的设备类型处理。"""
        with patch.object(client, "set_single_ep_async") as mock_set:
            # 测试窗帘控制
            result = await client.open_cover_async("agt", "me", "UNSUPPORTED_TYPE")
            assert result == -1, "不支持的设备类型应该返回-1"
            mock_set.assert_not_called()
            assert "UNSUPPORTED_TYPE" in caplog.text, "应该记录不支持的设备类型"

            caplog.clear()
            mock_set.reset_mock()

            # 测试风扇模式控制
            result = await client.async_set_climate_fan_mode(
                "agt", "me", "UNSUPPORTED_TYPE", FAN_LOW
            )
            assert result == -1, "不支持的设备类型应该返回-1"
            mock_set.assert_not_called()
            assert "不支持风扇模式" in caplog.text, "应该记录不支持风扇模式的错误信息"

    @pytest.mark.asyncio
    async def test_malformed_api_responses(self, mock_async_call_api, client):
        """测试格式错误的API响应处理。"""
        # 测试非预期格式的响应
        test_cases = [
            {"code": 0, "message": "not_expected_format"},
            {"code": 0},  # 缺少message字段
            {"message": []},  # 缺少code字段
        ]

        for bad_response in test_cases:
            mock_async_call_api.return_value = bad_response

            # 测试列表方法
            result = await client.get_agt_list_async()
            assert result == [], f"格式错误的响应 {bad_response} 应该返回空列表"

            # 测试字典方法
            result = await client.get_agt_details_async("hub1")
            assert result == {}, f"格式错误的响应 {bad_response} 应该返回空字典"


# ==================== 兼容性和集成测试类 ====================


class TestCompatibilityAndIntegration:
    """测试与Home Assistant和其他组件的兼容性。"""

    @pytest.mark.asyncio
    async def test_home_assistant_session_integration(self, client):
        """测试与Home Assistant HTTP会话的集成。"""
        with patch(
            "custom_components.lifesmart.core.openapi_client.async_get_clientsession"
        ) as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value = mock_session

            # 直接模拟 _post_async 方法以避免复杂的 aiohttp 模拟
            with patch.object(
                client, "_post_async", return_value='{"code": 0}'
            ) as mock_post:
                result = await client._post_and_parse(
                    "http://test.com",
                    {"test": "data"},
                    {"Content-Type": "application/json"},
                )

                assert result == {"code": 0}, "应该正确解析JSON响应"
                mock_post.assert_called_once()

    def test_static_utility_methods(self, client):
        """测试静态工具方法的功能。"""
        # 测试签名生成
        test_string = "test_signature_data"
        signature1 = client._get_signature(test_string)
        signature2 = client._get_signature(test_string)
        assert signature1 == signature2, "相同输入应该生成相同签名"
        assert len(signature1) == 32, "MD5签名应该是32位"

        # 测试HTTP头生成
        headers = client._generate_header()
        assert (
            headers["Content-Type"] == "application/json"
        ), "应该设置正确的Content-Type"


# ==================== SuperBowl API 测试类 ====================


class TestSuperBowlAPIMethods:
    """测试 SuperBowl API 的各种查询方法。"""

    @pytest.mark.asyncio
    async def test_get_ir_categories_async(self, mock_async_call_api, client):
        """测试获取红外分类 API。"""
        # 设置预期响应
        mock_async_call_api.return_value = {
            "code": 0,
            "message": ["tv", "ac", "stb", "dvd"],
        }

        result = await client.get_ir_categories_async()

        # 验证调用参数
        mock_async_call_api.assert_called_once_with("GetCategory", api_path="/irapi")

        # 验证返回结果
        assert result == ["tv", "ac", "stb", "dvd"], "应该返回分类列表"

    @pytest.mark.asyncio
    async def test_get_ir_brands_async(self, mock_async_call_api, client):
        """测试获取指定分类的品牌列表 API。"""
        # 设置预期响应
        mock_async_call_api.return_value = {
            "code": 0,
            "message": {"data": {"samsung": 1, "lg": 2, "sony": 3}},
        }

        result = await client.get_ir_brands_async("tv")

        # 验证调用参数
        mock_async_call_api.assert_called_once_with(
            "GetBrands", {"category": "tv"}, api_path="/irapi"
        )

        # 验证返回结果
        expected_brands = {"samsung": 1, "lg": 2, "sony": 3}
        assert result == expected_brands, "应该返回品牌字典"

    @pytest.mark.asyncio
    async def test_get_ir_codes_async_with_keys(self, mock_async_call_api, client):
        """测试获取红外码 API（带按键参数）。"""
        # 设置预期响应
        mock_async_call_api.return_value = {
            "code": 0,
            "message": {
                "power": {"param": {"data": "ABC123", "type": 1}},
                "volume_up": {"param": {"data": "DEF456", "type": 1}},
            },
        }

        result = await client.get_ir_codes_async(
            "tv", "samsung", "1", ["power", "volume_up"]
        )

        # 验证调用参数
        expected_params = {
            "category": "tv",
            "brand": "samsung",
            "idx": "1",
            "keys": json.dumps(["power", "volume_up"]),
        }
        mock_async_call_api.assert_called_once_with(
            "GetCodes", expected_params, api_path="/irapi"
        )

        # 验证返回结果
        expected_codes = {
            "power": {"param": {"data": "ABC123", "type": 1}},
            "volume_up": {"param": {"data": "DEF456", "type": 1}},
        }
        assert result == expected_codes, "应该返回红外码字典"

    @pytest.mark.asyncio
    async def test_get_ir_ac_codes_async_default_params(
        self, mock_async_call_api, client
    ):
        """测试获取空调红外码 API（使用默认参数）。"""
        # 设置预期响应
        mock_async_call_api.return_value = {
            "code": 0,
            "message": [{"param": {"data": "AABBCC", "type": 1}}],
        }

        result = await client.get_ir_ac_codes_async("ac", "daikin", "1")

        # 验证调用参数 - 应该使用默认值
        expected_params = {
            "category": "ac",
            "brand": "daikin",
            "idx": "1",
            "key": "power",
            "power": 1,
            "mode": 1,
            "temp": 25,
            "wind": 0,
            "swing": 0,
        }
        mock_async_call_api.assert_called_once_with(
            "GetACCodes", expected_params, api_path="/irapi"
        )


class TestInfraredControlLogic:
    """测试红外控制逻辑，包括 SendKeys 和 SendACKeys API 调用。"""

    @pytest.mark.asyncio
    async def test_async_ir_control_regular_device(self, mock_async_call_api, client):
        """测试普通设备的红外控制。"""
        # 设置 _send_ir_keys_api 的 mock
        with patch.object(client, "_send_ir_keys_api", return_value=0) as mock_send_ir:
            options = {
                "agt": "hub1",
                "me": "spot1",
                "category": "tv",
                "brand": "samsung",
                "keys": ["power", "volume_up"],
            }

            result = await client._async_ir_control("spot1", options)

            # 验证调用了普通红外 API
            mock_send_ir.assert_called_once_with(options)
            assert result == 0, "应该返回成功码"

    @pytest.mark.asyncio
    async def test_async_ir_control_ac_device(self, mock_async_call_api, client):
        """测试空调设备的红外控制。"""
        # 设置 _send_ac_keys_api 的 mock
        with patch.object(client, "_send_ac_keys_api", return_value=0) as mock_send_ac:
            options = {
                "agt": "hub1",
                "me": "spot1",
                "category": "ac",
                "brand": "daikin",
                "key": "power",
                "power": 1,
                "mode": 1,
                "temp": 26,
            }

            result = await client._async_ir_control("spot1", options)

            # 验证调用了空调红外 API
            mock_send_ac.assert_called_once_with(options)
            assert result == 0, "应该返回成功码"

    @pytest.mark.asyncio
    async def test_send_ir_keys_api_key_formatting(self, mock_async_call_api, client):
        """测试普通红外 API 的按键格式化逻辑。"""
        # 测试字符串按键
        options = {
            "agt": "hub1",
            "me": "spot1",
            "category": "tv",
            "brand": "samsung",
            "keys": "power",
        }

        await client._send_ir_keys_api(options)

        # 验证字符串被转换为 JSON 数组格式
        call_args = mock_async_call_api.call_args[0][1]
        assert call_args["keys"] == '["power"]', "字符串按键应该被转换为 JSON 数组"

        mock_async_call_api.reset_mock()

        # 测试列表按键
        options["keys"] = ["power", "volume_up", "channel_up"]
        await client._send_ir_keys_api(options)

        call_args = mock_async_call_api.call_args[0][1]
        assert (
            call_args["keys"] == '["power", "volume_up", "channel_up"]'
        ), "列表按键应该被序列化为 JSON"

    @pytest.mark.asyncio
    async def test_send_ac_keys_api_default_values(self, mock_async_call_api, client):
        """测试空调红外 API 的默认值设置。"""
        options = {
            "agt": "hub1",
            "me": "spot1",
            "category": "ac",
            "brand": "mitsubishi",
        }

        result = await client._send_ac_keys_api(options)

        # 验证所有参数都使用了默认值
        call_args = mock_async_call_api.call_args[0][1]
        assert call_args["key"] == "power", "默认按键应该是 power"
        assert call_args["power"] == 1, "默认电源状态应该是 1"
        assert call_args["mode"] == 1, "默认模式应该是 1"
        assert call_args["temp"] == 25, "默认温度应该是 25"
        assert call_args["wind"] == 0, "默认风速应该是 0"
        assert call_args["swing"] == 0, "默认摆风应该是 0"


class TestRawInfraredCodeSending:
    """测试原始红外码发送功能。"""

    @pytest.mark.asyncio
    async def test_async_send_ir_code_with_bytes(self, mock_async_call_api, client):
        """测试使用字节数据发送原始红外码。"""
        ir_data = b"\xab\xcd\xef\x12"

        result = await client._async_send_ir_code("spot1", ir_data)

        # 验证调用参数
        call_args = mock_async_call_api.call_args[0][1]
        keys_data = json.loads(call_args["keys"])

        assert (
            keys_data[0]["param"]["data"] == "ABCDEF12"
        ), "字节数据应该被转换为大写十六进制"
        assert keys_data[0]["param"]["type"] == 1, "类型应该设置为 1"

    @pytest.mark.asyncio
    async def test_async_send_ir_code_with_list(self, mock_async_call_api, client):
        """测试使用列表数据发送原始红外码。"""
        ir_data = [171, 205, 239, 18]  # 对应 0xAB, 0xCD, 0xEF, 0x12

        result = await client._async_send_ir_code("spot1", ir_data)

        # 验证调用参数
        call_args = mock_async_call_api.call_args[0][1]
        keys_data = json.loads(call_args["keys"])

        assert (
            keys_data[0]["param"]["data"] == "ABCDEF12"
        ), "列表数据应该被转换为大写十六进制"
