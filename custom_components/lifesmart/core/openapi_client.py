"""由 @MapleEve 实现的 LifeSmart 云端客户端。

此模块提供了一个 LifeSmartOAPIClient 类，用于封装与 LifeSmart 云端 API 的所有交互。
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
    # --- 设备类型和映射 ---
    HUB_ID_KEY,
    DEVICE_ID_KEY,
    SUBDEVICE_INDEX_KEY,
)
from custom_components.lifesmart.core.client_base import LifeSmartClientBase
from custom_components.lifesmart.diagnostics import get_error_advice
from custom_components.lifesmart.exceptions import LifeSmartAPIError, LifeSmartAuthError

_LOGGER = logging.getLogger(__name__)


class LifeSmartOAPIClient(LifeSmartClientBase):
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
        self, agt: str, me: str, idx: str, command_type: int, val: Any
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

    async def get_ir_categories_async(self) -> list[str]:
        """获取支持的红外遥控器种类。(API: GetCategory)"""
        response = await self._async_call_api("GetCategory", api_path="/irapi")
        message = response.get("message")
        return message if isinstance(message, list) else []

    async def get_ir_brands_async(self, category: str) -> dict[str, int]:
        """获取指定种类的红外遥控器品牌列表。(API: GetBrands)"""
        response = await self._async_call_api(
            "GetBrands", {"category": category}, api_path="/irapi"
        )
        message = response.get("message", {})
        return message.get("data", {}) if isinstance(message, dict) else {}

    async def get_ir_remote_indexes_async(self, category: str, brand: str) -> list[str]:
        """获取指定品牌的遥控器索引列表。(API: GetRemoteIdxs)"""
        response = await self._async_call_api(
            "GetRemoteIdxs", {"category": category, "brand": brand}, api_path="/irapi"
        )
        message = response.get("message", {})
        return message.get("data", []) if isinstance(message, dict) else []

    async def get_ir_codes_async(
        self, category: str, brand: str, idx: str, keys: list[str] = None
    ) -> dict[str, Any]:
        """获取普通遥控器的红外码。(API: GetCodes)"""
        params = {"category": category, "brand": brand, "idx": idx}
        if keys:
            params["keys"] = json.dumps(keys)
        response = await self._async_call_api("GetCodes", params, api_path="/irapi")
        message = response.get("message")
        return message if isinstance(message, dict) else {}

    async def get_ir_ac_codes_async(
        self,
        category: str,
        brand: str,
        idx: str,
        key: str = "power",
        power: int = 1,
        mode: int = 1,
        temp: int = 25,
        wind: int = 0,
        swing: int = 0,
    ) -> list[dict[str, Any]]:
        """获取空调遥控器的红外码。(API: GetACCodes)"""
        params = {
            "category": category,
            "brand": brand,
            "idx": idx,
            "key": key,
            "power": power,
            "mode": mode,
            "temp": temp,
            "wind": wind,
            "swing": swing,
        }
        response = await self._async_call_api("GetACCodes", params, api_path="/irapi")
        message = response.get("message")
        return message if isinstance(message, list) else []

    # ====================================================================
    # 基类抽象方法的实现
    # ====================================================================

    async def _async_get_all_devices(self, timeout=10) -> list[dict[str, Any]]:
        """
        [云端实现] 通过调用 EpGetAll API 获取所有设备信息。
        """
        _LOGGER.debug("通过云端 API (EpGetAll) 获取设备列表...")
        response = await self._async_call_api("EpGetAll", api_path="/api")
        message = response.get("message")
        if isinstance(message, list):
            return message

        _LOGGER.warning("EpGetAll 未返回预期的设备列表: %s", message)
        return []

    async def _async_send_single_command(
        self, agt: str, me: str, idx: str, command_type: int, val: Any
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

    async def _async_set_scene(self, agt: str, scene_name: str) -> int:
        """
        [云端实现] 激活一个场景。(API: SceneSet)

        由于云端API需要场景ID而不是名字，这里会先获取场景列表，
        根据场景名字查找对应的ID，然后触发场景。
        """
        try:
            # 首先获取场景列表以找到对应的场景ID
            scenes = await self._async_get_scene_list(agt)

            scene_id = next(
                (
                    scene.get("id")
                    for scene in scenes
                    if scene.get("name") == scene_name
                ),
                None,
            )
            if not scene_id:
                _LOGGER.error("未找到名为 '%s' 的场景", scene_name)
                return -1

            _LOGGER.info("找到场景 '%s'，ID: %s，正在触发...", scene_name, scene_id)

            # 使用场景ID触发场景
            response = await self._async_call_api(
                "SceneSet", {HUB_ID_KEY: agt, "id": scene_id}, api_path="/api"
            )
            return self._get_code_from_response(response, "SceneSet")

        except Exception as e:
            _LOGGER.error("云端场景触发失败: %s", e, exc_info=True)
            return -1

    async def _async_send_ir_key(
        self,
        agt: str,
        me: str,
        category: str,
        brand: str,
        keys: str,
        ai: str = "",
        idx: str = "",
    ) -> int:
        """
        [云端实现] 发送一个红外按键命令。(API: SendKeys)
        此方法通过调用底层的 _async_call_api 来实现基类的抽象方法。
        """
        params = {
            HUB_ID_KEY: agt,
            DEVICE_ID_KEY: me,
            "category": category,
            "brand": brand,
            "keys": keys,
        }

        # 根据官方API文档，ai和idx二选一
        if ai:
            params["ai"] = ai
        elif idx:
            params["idx"] = idx
        else:
            raise ValueError("ai和idx参数必须提供其中一个")

        response = await self._async_call_api("SendKeys", params, api_path="/irapi")
        return self._get_code_from_response(response, "SendKeys")

    async def _async_add_scene(self, agt: str, scene_name: str, actions: str) -> int:
        """
        [云端实现] 创建新场景。
        注意：此方法可能需要特殊权限，如果API不支持将返回错误。
        """
        # 由于缺乏具体的API文档，我们尝试使用可能的端点
        try:
            params = {
                HUB_ID_KEY: agt,
                "name": scene_name,
                "actions": actions,
            }
            response = await self._async_call_api("SceneAdd", params, api_path="/api")
            return self._get_code_from_response(response, "SceneAdd")
        except LifeSmartAPIError as e:
            _LOGGER.warning("场景创建可能不被支持: %s", e)
            return -1

    async def _async_delete_scene(self, agt: str, scene_name: str) -> int:
        """
        [云端实现] 删除场景。

        由于云端API需要场景ID而不是名字，这里会先获取场景列表，
        根据场景名字查找对应的ID，然后删除场景。
        注意：此方法可能需要特殊权限，如果API不支持将返回错误。
        """
        try:
            # 首先获取场景列表以找到对应的场景ID
            scenes = await self._async_get_scene_list(
                agt
            )  # 使用带缓存的场景列表获取方法

            scene_id = next(
                (
                    scene.get("id")
                    for scene in scenes
                    if scene.get("name") == scene_name
                ),
                None,
            )
            if not scene_id:
                _LOGGER.error("未找到名为 '%s' 的场景", scene_name)
                return -1

            _LOGGER.info("找到场景 '%s'，ID: %s，正在删除...", scene_name, scene_id)

            # 使用场景ID删除场景
            params = {
                HUB_ID_KEY: agt,
                "id": scene_id,
            }
            response = await self._async_call_api("SceneDel", params, api_path="/api")
            return self._get_code_from_response(response, "SceneDel")

        except LifeSmartAPIError as e:
            _LOGGER.warning("场景删除可能不被支持: %s", e)
            return -1
        except Exception as e:
            _LOGGER.error("云端场景删除失败: %s", e)
            return -1

    async def _async_get_scene_list(self, agt: str) -> list[dict[str, Any]]:
        """
        [云端实现] 获取场景列表。(API: SceneGet)
        此方法通过调用已存在的 get_scene_list_async 来实现基类的抽象方法。
        """
        return await self.get_scene_list_async(agt)

    async def _async_get_room_list(self, agt: str) -> list[dict[str, Any]]:
        """
        [云端实现] 获取房间列表。(API: RoomGet)
        此方法通过调用已存在的 get_room_list_async 来实现基类的抽象方法。
        """
        return await self.get_room_list_async(agt)

    async def _async_get_hub_list(self) -> list[dict[str, Any]]:
        """
        [云端实现] 获取中枢列表。(API: AgtGetList)
        此方法通过调用已存在的 get_agt_list_async 来实现基类的抽象方法。
        """
        return await self.get_agt_list_async()

    async def _async_change_device_icon(self, device_id: str, icon: str) -> int:
        """
        [云端实现] 修改设备图标。
        注意：此功能可能需要特殊权限，如果API不支持将返回错误。
        """
        try:
            # 尝试使用可能的API端点进行设备图标修改
            params = {
                DEVICE_ID_KEY: device_id,
                "icon": icon,
            }
            response = await self._async_call_api("EpSetIcon", params, api_path="/api")
            return self._get_code_from_response(response, "EpSetIcon")
        except LifeSmartAPIError as e:
            _LOGGER.warning("设备图标修改可能不被支持: %s", e)
            return -1

    async def _async_set_device_eeprom(
        self, device_id: str, key: str, value: Any
    ) -> int:
        """
        [云端实现] 设置设备EEPROM。
        注意：此功能可能需要特殊权限，如果API不支持将返回错误。
        """
        try:
            params = {
                DEVICE_ID_KEY: device_id,
                "key": key,
                "value": value,
            }
            response = await self._async_call_api(
                "EpSetEeprom", params, api_path="/api"
            )
            return self._get_code_from_response(response, "EpSetEeprom")
        except LifeSmartAPIError as e:
            _LOGGER.warning("设备EEPROM设置可能不被支持: %s", e)
            return -1

    async def _async_add_device_timer(
        self, device_id: str, cron_info: str, key: str
    ) -> int:
        """
        [云端实现] 为设备添加定时器。
        注意：此功能可能需要特殊权限，如果API不支持将返回错误。
        """
        try:
            params = {
                DEVICE_ID_KEY: device_id,
                "cron": cron_info,
                "key": key,
            }
            response = await self._async_call_api("EpAddTimer", params, api_path="/api")
            return self._get_code_from_response(response, "EpAddTimer")
        except LifeSmartAPIError as e:
            _LOGGER.warning("设备定时器添加可能不被支持: %s", e)
            return -1

    async def _async_ir_control(self, device_id: str, options: dict) -> int:
        """
        [云端实现] 通过SuperBowl红外API控制红外设备。
        使用documented SendKeys或SendACKeys API根据设备类型发送控制命令。
        """
        try:
            # 从options中提取必要参数
            agt = options.get("agt")
            me = options.get("me") or device_id
            category = options.get("category")
            brand = options.get("brand")

            if not all([agt, category, brand]):
                _LOGGER.error(
                    "红外控制缺少必要参数: agt=%s, category=%s, brand=%s",
                    agt,
                    category,
                    brand,
                )
                return -1

            # 确保options中包含正确的me参数
            options = dict(options)  # 创建副本避免修改原始字典
            options["me"] = me

            # 如果是空调类型，使用SendACKeys API
            if category == "ac":
                return await self._send_ac_keys_api(options)
            else:
                # 普通设备使用SendKeys API
                return await self._send_ir_keys_api(options)

        except LifeSmartAPIError as e:
            _LOGGER.error("红外设备控制失败: %s", e)
            return -1

    async def _send_ir_keys_api(self, options: dict) -> int:
        """发送普通红外按键API调用。"""
        keys = options.get("keys", "POWER")
        if isinstance(keys, list):
            keys_str = json.dumps(keys)
        else:
            keys_str = f'["{keys}"]'

        send_params = {
            "agt": options["agt"],
            "me": options["me"],
            "category": options["category"],
            "brand": options["brand"],
            "keys": keys_str,
        }

        # 如果指定了ai参数，使用已有遥控器
        if "ai" in options:
            send_params["ai"] = options["ai"]
        elif "idx" in options:
            send_params["idx"] = options["idx"]

        response = await self._async_call_api(
            "SendKeys", send_params, api_path="/irapi"
        )
        return self._get_code_from_response(response, "SendKeys")

    async def _send_ac_keys_api(self, options: dict) -> int:
        """发送空调红外按键API调用。"""
        ac_params = {
            "agt": options["agt"],
            "me": options["me"],
            "category": options["category"],
            "brand": options["brand"],
            "key": options.get("key", "power"),
            "power": options.get("power", 1),
            "mode": options.get("mode", 1),
            "temp": options.get("temp", 25),
            "wind": options.get("wind", 0),
            "swing": options.get("swing", 0),
        }

        # 处理可选的keyDetail参数 (根据官方API文档)
        if "keyDetail" in options:
            ac_params["keyDetail"] = options["keyDetail"]

        # 如果指定了ai参数，使用已有遥控器
        if "ai" in options:
            ac_params["ai"] = options["ai"]
        elif "idx" in options:
            ac_params["idx"] = options["idx"]

        response = await self._async_call_api(
            "SendACKeys", ac_params, api_path="/irapi"
        )
        return self._get_code_from_response(response, "SendACKeys")

    async def _async_send_ir_code(self, device_id: str, ir_data: list | bytes) -> int:
        """
        [云端实现] 使用SuperBowl SendCodes API发送原始红外码。
        根据文档，此API用于发射获取到的红外码数据。
        """
        try:
            # 准备红外码数据格式
            if isinstance(ir_data, bytes):
                hex_data = ir_data.hex().upper()
            elif isinstance(ir_data, list):
                hex_data = "".join(f"{b:02X}" for b in ir_data)
            else:
                hex_data = str(ir_data)

            # 构建SendCodes格式的数据包
            keys_data = json.dumps([{"param": {"data": hex_data, "type": 1}}])

            params = {
                "agt": "unknown",  # 需要从设备信息中获取
                "me": device_id,
                "keys": keys_data,
            }

            response = await self._async_call_api(
                "SendCodes", params, api_path="/irapi"
            )
            return self._get_code_from_response(response, "SendCodes")

        except LifeSmartAPIError as e:
            _LOGGER.error("原始红外码发送失败: %s", e)
            return -1

    async def _async_ir_raw_control(self, device_id: str, raw_data: str) -> int:
        """
        [云端实现] 发送原始红外控制数据。
        注意：此功能可能需要特殊权限，如果API不支持将返回错误。
        """
        try:
            params = {
                DEVICE_ID_KEY: device_id,
                "rawdata": raw_data,
            }
            response = await self._async_call_api(
                "IrRawControl", params, api_path="/irapi"
            )
            return self._get_code_from_response(response, "IrRawControl")
        except LifeSmartAPIError as e:
            _LOGGER.warning("红外原始控制可能不被支持: %s", e)
            return -1

    async def _async_get_ir_remote_list(self, agt: str) -> dict[str, Any]:
        """
        [云端实现] 使用SuperBowl GetRemoteList API获取红外遥控器列表。
        根据文档，此API用于获取超级碗上的遥控器列表。
        """
        return await self.get_ir_remote_list_async(agt)

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
