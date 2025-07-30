"""由 @MapleEve 实现的 LifeSmart 云端客户端。

此模块提供了一个 LifeSmartClient 类，用于封装与 LifeSmart 云端 API 的所有交互。
它负责构建请求、处理签名、发送命令，并为上层平台（如 switch, light）
提供了一套清晰、易于使用的异步方法来控制设备。
"""

import hashlib
import json
import logging
import time
from typing import Any, Optional

from aiohttp.client_exceptions import ClientError
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.lifesmart.const import (
    # --- 命令类型常量 ---
    # (这些常量现在由基类使用)
    # --- 设备类型和映射 ---
    HUB_ID_KEY,
    DEVICE_ID_KEY,
    SUBDEVICE_INDEX_KEY,
)
from custom_components.lifesmart.core.client_base import LifeSmartClientBase
from custom_components.lifesmart.diagnostics import get_error_advice
from custom_components.lifesmart.exceptions import LifeSmartAPIError, LifeSmartAuthError

_LOGGER = logging.getLogger(__name__)


class LifeSmartClient(LifeSmartClientBase):
    """一个用于高效、健壮地管理 LifeSmart API 调用的类。

    此类封装了所有与 LifeSmart API 的通信细节，包括认证、签名生成、
    请求发送和响应处理。

    Attributes:
        hass: Home Assistant 的核心实例。
        _region (str): 服务器区域代码。
        _appkey (str): 应用 AppKey。
        _apptoken (str): 应用 AppToken。
        _usertoken (str): 用户 UserToken。
        _userid (str): 用户 UserID。
        _apppassword (Optional[str]): App 用户密码（仅用于登录获取令牌）。
    """

    def __init__(
        self,
        hass: HomeAssistant,
        region: str,
        appkey: str,
        apptoken: str,
        usertoken: str,
        userid: str,
        user_password: Optional[str] = None,
    ) -> None:
        """初始化 LifeSmart 客户端。"""
        self.hass = hass
        self._region = region
        self._appkey = appkey
        self._apptoken = apptoken
        self._usertoken = usertoken
        self._userid = userid
        self._apppassword = user_password

    # ====================================================================
    # 核心 API 调用器
    # ====================================================================

    async def _async_call_api(
        self, method: str, params: Optional[dict] = None, api_path: str = "/api"
    ) -> dict[str, Any]:
        """一个集中的方法，用于构建、签名和发送 API 请求。

        Args:
            method: API 方法名称 (例如 "EpGetAll")。
            params: 请求的参数字典。
            api_path: API 的路径 (默认为 "/api", 红外为 "/irapi")。

        Returns:
            API 响应中的 "message" 部分，或整个响应字典。

        Raises:
            LifeSmartAPIError: 当 API 返回非零错误码时引发。
        """
        url = f"{self._get_api_url()}{api_path}.{method}"
        tick = int(time.time())
        params = params or {}

        sdata_parts = [f"method:{method}"]

        # 只有 params 字典内部的字段需要按 key 升序排列
        if params:
            for key in sorted(params.keys()):
                sdata_parts.append(f"{key}:{params[key]}")

        sdata_parts.extend(
            [
                f"time:{tick}",
                f"userid:{self._userid}",
                f"usertoken:{self._usertoken or ''}",
                f"appkey:{self._appkey}",
                f"apptoken:{self._apptoken}",
            ]
        )

        sdata = ",".join(sdata_parts)
        signature = self._get_signature(sdata)
        _LOGGER.debug("签名原始串: %s", sdata)
        # --- 签名逻辑结束 ---

        send_values = {
            "id": tick,
            "method": method,
            "system": {
                "ver": "1.0",
                "lang": "en",
                "userid": self._userid,
                "appkey": self._appkey,
                "time": tick,
                "sign": signature,
            },
        }
        if params:
            send_values["params"] = params

        _LOGGER.debug("通用API 请求 -> %s: %s", method, send_values)
        response = await self._post_and_parse(url, send_values, self._generate_header())
        _LOGGER.debug("通用API 响应 <- %s: %s", method, response)

        code = response.get("code")
        if code != 0:
            error_code = response.get("code")
            raw_message = response.get("message")
            desc, advice, category = get_error_advice(error_code)
            log_message = (
                f"API 调用 '{method}' 失败! [错误码: {error_code}] "
                f"[分类: {category or '未知'}] [描述: {desc}] [原始消息: {raw_message}]"
            )
            _LOGGER.error(log_message)
            if error_code in {10004, 10005, 10006}:
                raise LifeSmartAuthError(advice, error_code)
            raise LifeSmartAPIError(advice, error_code)

        return response

    # ====================================================================
    # 认证 API 的专属实现
    # ====================================================================
    async def login_async(self) -> dict[str, Any]:
        """登录到 LifeSmart 服务以获取用户令牌。

        这是一个两步认证过程，首先用密码获取临时令牌，然后用临时令牌换取长期的用户令牌 (usertoken)
        此方法处理 /auth.login 和 /auth.do_auth 两个特殊的、无签名的端点。

        Returns:
            如果登录成功，则返回 True。

        Raises:
            LifeSmartAuthError: 如果任何一步认证失败。
        """
        if not self._userid or not self._apppassword:
            raise LifeSmartAuthError("用户名或应用密码无效，无法登录。")

        header = self._generate_header()

        # 步骤 1: /auth.login (无签名)
        url_step1 = f"{self._get_api_url()}/auth.login"
        body_step1 = {
            "uid": self._userid,
            "pwd": self._apppassword,
            "appkey": self._appkey,
        }
        _LOGGER.debug("登录请求 (步骤1) -> %s", body_step1)
        response1 = await self._post_and_parse(url_step1, body_step1, header)
        _LOGGER.debug("登录响应 (步骤1) <- %s", response1)

        if response1.get("code") != "success" or "token" not in response1:
            raise LifeSmartAuthError(
                f"登录失败 (步骤1): {response1.get('message', '无消息')}",
                response1.get("code"),
            )

        # --- 步骤 2: /auth.do_auth ---
        url_step2 = f"{self._get_api_url()}/auth.do_auth"
        body_step2 = {
            "userid": response1["userid"],
            "token": response1["token"],
            "appkey": self._appkey,
            "rgn": self._region,
        }
        _LOGGER.debug("认证请求 (步骤2) -> %s", body_step2)
        response2 = await self._post_and_parse(url_step2, body_step2, header)
        _LOGGER.debug("认证响应 (步骤2) <- %s", response2)

        if response2.get("code") == "success" and "usertoken" in response2:
            self._usertoken = response2["usertoken"]
            self._region = response2["rgn"]
            if self._userid != response2["userid"]:
                self._userid = response2["userid"]
            _LOGGER.info("成功登录并获取用户令牌。")
            return response2

        raise LifeSmartAuthError(
            f"认证失败 (步骤2): {response2.get('message', '无消息')}",
            response2.get("code"),
        )

    async def async_refresh_token(self) -> dict[str, Any]:
        """刷新用户令牌 (usertoken) 以延长其有效期。

        此方法处理 /auth.refreshtoken 这个特殊的、带顶层签名的端点。

        Returns:
            一个包含新 'usertoken' 和 'expiredtime' 的字典。

        Raises:
            LifeSmartAuthError: 如果刷新失败。
        """
        url = f"{self._get_api_url()}/auth.refreshtoken"
        tick = int(time.time())

        # 1. 构造签名原始串
        sdata_params = {"appkey": self._appkey, "time": tick, "userid": self._userid}
        sdata = "&".join([f"{k}={v}" for k, v in sorted(sdata_params.items())])
        sdata += f"&apptoken={self._apptoken}&usertoken={self._usertoken or ''}"
        signature = self._get_signature(sdata)
        _LOGGER.debug("刷新令牌签名原始串 (sdata): %s", sdata)
        _LOGGER.debug("生成刷新令牌签名 (sign): %s", signature)

        # 2. 构造扁平化的请求体
        send_values = {
            "id": tick,
            "appkey": self._appkey,
            "time": tick,
            "userid": self._userid,
            "sign": signature,
        }

        # 3. 发送请求
        _LOGGER.debug("刷新令牌请求 -> %s", send_values)
        response = await self._post_and_parse(url, send_values, self._generate_header())
        _LOGGER.debug("刷新令牌响应 <- %s", response)

        if response.get("code") == 0 and "usertoken" in response:
            self._usertoken = response["usertoken"]
            _LOGGER.info("用户令牌刷新成功。")
            return response

        raise LifeSmartAuthError(
            f"刷新令牌失败: {response.get('message', '未知错误')}", response.get("code")
        )

    def get_wss_url(self) -> str:
        """根据所选区域生成 WebSocket (WSS) URL。"""
        if not self._region or self._region.upper() == "AUTO":
            return "wss://api.ilifesmart.com:8443/wsapp/"
        return f"wss://api.{self._region.lower()}.ilifesmart.com:8443/wsapp/"

    def generate_wss_auth(self) -> str:
        """为 WebSocket 连接生成认证消息。"""
        tick = int(time.time())

        sdata_parts = [
            "method:WbAuth",
            f"time:{tick}",
            f"userid:{self._userid}",
            f"usertoken:{self._usertoken or ''}",
            f"appkey:{self._appkey}",
            f"apptoken:{self._apptoken}",
        ]
        sdata = ",".join(sdata_parts)

        send_values = {
            "id": 1,
            "method": "WbAuth",
            "system": {
                "ver": "1.0",
                "lang": "en",
                "userid": self._userid,
                "appkey": self._appkey,
                "time": tick,
                "sign": self._get_signature(sdata),
            },
        }
        return json.dumps(send_values)

    # ====================================================================
    # 接口：所有管理和查询接口
    # ====================================================================

    async def get_agt_list_async(self) -> list[dict[str, Any]]:
        """获取用户下的所有中枢（网关）列表。(API: AgtGetList)"""
        response = await self._async_call_api("AgtGetList", api_path="/api")
        message = response.get("message")
        return message if isinstance(message, list) else []

    async def get_agt_details_async(self, agt: str) -> dict[str, Any]:
        """获取指定中枢的详细信息。(API: AgtGet)"""
        response = await self._async_call_api(
            "AgtGet", {HUB_ID_KEY: agt}, api_path="/api"
        )
        message = response.get("message")
        return message if isinstance(message, dict) else {}

    async def get_all_device_async(self) -> list[dict[str, Any]]:
        """获取当前用户下的所有设备。(API: EpGetAll)"""
        response = await self._async_call_api("EpGetAll", api_path="/api")
        message = response.get("message")
        return message if isinstance(message, list) else []

    async def get_scene_list_async(self, agt: str) -> list[dict[str, Any]]:
        """获取指定中枢下的所有场景。(API: SceneGet)"""
        response = await self._async_call_api(
            "SceneGet", {HUB_ID_KEY: agt}, api_path="/api"
        )
        message = response.get("message")
        return message if isinstance(message, list) else []

    async def get_room_list_async(self, agt: str) -> list[dict[str, Any]]:
        """获取指定中枢下配置的房间列表。(API: RoomGet)"""
        response = await self._async_call_api(
            "RoomGet", {HUB_ID_KEY: agt}, api_path="/api"
        )
        message = response.get("message")
        return message if isinstance(message, list) else []

    async def set_single_ep_async(
        self, agt: str, me: str, idx: str, command_type: str, val: Any
    ) -> int:
        params = {
            HUB_ID_KEY: agt,
            DEVICE_ID_KEY: me,
            SUBDEVICE_INDEX_KEY: idx,
            "type": command_type,
            "val": val,
        }
        response = await self._async_call_api("EpSet", params, api_path="/api")
        return self._get_code_from_response(response, "EpSet")

    async def set_multi_eps_async(self, agt: str, me: str, io_list: list[dict]) -> int:
        """向设备端点同时发送多个IO口的命令。(API: EpsSet)

        根据官方文档，此方法使用 EpsSet 接口，并将操作列表作为JSON字符串
        在 'args' 参数中传递。

        Args:
            agt: 中枢ID。
            me: 设备ID。
            io_list: 一个包含多个IO设置的列表，
                     例如: [{"idx": "DYN", "type": "0xff", "val": 123},
                            {"idx": "RGBW", "type": "0x81", "val": 1}]
        """
        args_str = json.dumps(io_list)
        params = {HUB_ID_KEY: agt, DEVICE_ID_KEY: me, "args": args_str}
        response = await self._async_call_api("EpsSet", params, api_path="/api")
        return self._get_code_from_response(response, "EpsSet")

    async def get_epget_async(self, agt: str, me: str) -> dict[str, Any]:
        """获取指定设备的详细信息。(API: EpGet)"""
        response = await self._async_call_api(
            "EpGet", {HUB_ID_KEY: agt, DEVICE_ID_KEY: me}, api_path="/api"
        )

        message = response.get("message")

        if isinstance(message, list) and message:
            device_data = message[0]
            if isinstance(device_data, dict):
                return device_data

        return {}

    async def get_ir_remote_list_async(self, agt: str) -> dict[str, Any]:
        """获取指定中枢下的红外遥控器列表。(API: GetRemoteList)"""
        response = await self._async_call_api(
            "GetRemoteList", {HUB_ID_KEY: agt}, api_path="/irapi"
        )
        message = response.get("message")
        return message if isinstance(message, dict) else {}

    # ====================================================================
    # 基类抽象方法的实现
    # ====================================================================

    async def _async_send_single_command(
        self, agt: str, me: str, idx: str, command_type: str, val: Any
    ) -> int:
        """
        [云端实现] 发送单个IO口命令。
        此方法通过调用 set_single_ep_async 来实现基类的抽象方法。
        """
        return await self.set_single_ep_async(agt, me, idx, command_type, val)

    async def _async_send_multi_command(
        self, agt: str, me: str, io_list: list[dict]
    ) -> int:
        """
        [云端实现] 同时发送多个IO口的命令。
        此方法通过调用 set_multi_eps_async 来实现基类的抽象方法。
        """
        return await self.set_multi_eps_async(agt, me, io_list)

    async def set_scene_async(self, agt: str, scene_id: str) -> int:
        """
        [云端实现] 激活一个场景。(API: SceneSet)
        此方法通过调用底层的 _async_call_api 来实现基类的抽象方法。
        """
        response = await self._async_call_api(
            "SceneSet", {HUB_ID_KEY: agt, "id": scene_id}, api_path="/api"
        )
        return self._get_code_from_response(response, "SceneSet")

    async def send_ir_key_async(
        self, agt: str, ai: str, me: str, category: str, brand: str, keys: str
    ) -> int:
        """
        [云端实现] 发送一个红外按键命令。(API: SendKeys)
        此方法通过调用底层的 _async_call_api 来实现基类的抽象方法。
        """
        params = {
            HUB_ID_KEY: agt,
            "ai": ai,
            DEVICE_ID_KEY: me,
            "category": category,
            "brand": brand,
            "keys": keys,
        }
        response = await self._async_call_api("SendKeys", params, api_path="/irapi")
        return self._get_code_from_response(response, "SendKeys")

    # ====================================================================
    # 设备直接控制的辅助方法控制方法 (`turn_on_light_switch_async`, `open_cover_async`,
    # `async_set_climate_hvac_mode` 等) 现已移至 `client_base.py` 中，
    # 并由该类继承。
    # ====================================================================

    # ====================================================================
    # 内部工具方法
    # ====================================================================

    async def _post_and_parse(self, url: str, data: dict, headers: dict) -> dict:
        """一个辅助函数，用于发送POST请求并解析JSON响应。"""
        try:
            response_text = await self._post_async(url, json.dumps(data), headers)
            return json.loads(response_text)
        except ClientError as e:
            _LOGGER.error("POST请求到 %s 时发生网络错误: %s", url, e)
            raise LifeSmartAPIError(f"网络请求失败: {e}") from e
        except json.JSONDecodeError as e:
            _LOGGER.error("解析来自 %s 的响应时发生JSON错误: %s", url, e)
            raise LifeSmartAPIError(f"JSON解析失败: {e}") from e

    async def _post_async(self, url: str, data: str, headers: dict) -> str:
        """使用 Home Assistant 的共享客户端会话发送 POST 请求。"""
        session = async_get_clientsession(self.hass)
        async with session.post(url, data=data, headers=headers) as response:
            response.raise_for_status()
            return await response.text()

    def _get_api_url(self) -> str:
        """根据所选区域生成基础 API URL。"""
        if not self._region or self._region.upper() == "AUTO":
            return "https://api.ilifesmart.com/app"
        return f"https://api.{self._region.lower()}.ilifesmart.com/app"

    @staticmethod
    def _get_code_from_response(response: dict, method_name: str) -> int:
        """用于从“设置”类API的响应中安全地提取和转换'code'。"""
        if not isinstance(response, dict):
            _LOGGER.warning("%s: API响应不是预期的字典类型: %s", method_name, response)
            return -1

        code_val = response.get("code")
        if code_val is None:
            _LOGGER.warning("%s: API响应中缺少 'code' 字段: %s", method_name, response)
            return -1

        try:
            return int(code_val)
        except (ValueError, TypeError):
            _LOGGER.error(
                "%s: API返回的 'code' 字段不是有效的整数: %s", method_name, code_val
            )
            return -1

    @staticmethod
    def _get_signature(data: str) -> str:
        """根据传入的原始串计算MD5签名。"""
        return hashlib.md5(data.encode("utf-8")).hexdigest()

    @staticmethod
    def _generate_header() -> dict[str, str]:
        """生成默认的 HTTP 头部。"""
        return {"Content-Type": "application/json"}
