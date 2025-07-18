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

from homeassistant.components.climate import HVACMode
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    # --- 命令类型常量 ---
    CMD_TYPE_ON,
    CMD_TYPE_OFF,
    CMD_TYPE_PRESS,
    CMD_TYPE_SET_VAL,
    CMD_TYPE_SET_CONFIG,
    CMD_TYPE_SET_TEMP_DECIMAL,
    CMD_TYPE_SET_RAW,
    CMD_TYPE_SET_TEMP_FCU,
    # --- 设备类型和映射 ---
    HUB_ID_KEY,
    DEVICE_ID_KEY,
    SUBDEVICE_INDEX_KEY,
    DEVICE_DATA_KEY,
    DOOYA_TYPES,
    GARAGE_DOOR_TYPES,
    REVERSE_LIFESMART_HVAC_MODE_MAP,
    REVERSE_LIFESMART_TF_FAN_MODE_MAP,
    LIFESMART_F_FAN_MODE_MAP,
    REVERSE_LIFESMART_ACIPM_FAN_MAP,
    REVERSE_LIFESMART_CP_AIR_FAN_MAP,
    REVERSE_LIFESMART_CP_AIR_MODE_MAP,
)
from .exceptions import LifeSmartAPIError, LifeSmartAuthError

_LOGGER = logging.getLogger(__name__)


class LifeSmartClient:
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
        _apppassword (Optional[str]): 用户密码（仅用于登录获取令牌）。
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
        url = f"{self.get_api_url()}{api_path}.{method}"
        tick = int(time.time())
        params = params or {}

        # 构造用于签名的字符串
        param_list = [f"method:{method}"]
        for key, value in sorted(params.items()):
            param_list.append(f"{key}:{value}")
        param_list.append(self.generate_time_and_credential_data(tick))
        sdata = ",".join(param_list)

        # 构造最终的请求体
        send_values = {
            "id": 1,
            "method": method,
            "system": self.generate_system_request_body(tick, sdata),
        }
        if params:
            send_values["params"] = params

        header = self.generate_header()
        send_data = json.dumps(send_values)

        _LOGGER.debug("API 请求 -> %s: %s", method, send_data)
        response_text = await self.post_async(url, send_data, header)
        response = json.loads(response_text)
        _LOGGER.debug("API 响应 <- %s: %s", method, response)

        if response.get("code") != 0:
            error_msg = f"API 调用 '{method}' 失败，错误码 {response.get('code')}: {response.get('message')}"
            _LOGGER.error(error_msg)
            raise LifeSmartAPIError(error_msg, response.get("code"))

        return response.get("message", response)

    async def login_async(self) -> bool:
        """登录到 LifeSmart 服务以获取用户令牌。

        这是一个两步认证过程，首先用密码获取临时令牌，然后用临时令牌换取
        长期的用户令牌 (usertoken)。

        Returns:
            如果登录成功，则返回 True。

        Raises:
            LifeSmartAuthError: 如果任何一步认证失败。
        """
        # 登录流程特殊，不使用通用调用器 `_async_call_api`
        url = self.get_api_url() + "/auth.login"
        login_data = {
            "uid": self._userid,
            "pwd": self._apppassword,
            "appkey": self._appkey,
        }
        header = self.generate_header()
        send_data = json.dumps(login_data)
        try:
            response_text = await self.post_async(url, send_data, header)
            response = json.loads(response_text)
        except Exception as e:
            raise LifeSmartAuthError(f"登录请求因网络错误失败: {e}") from e

        if response.get("code") != 0 or "token" not in response:
            raise LifeSmartAuthError(
                f"登录失败 (步骤 1): {response.get('message', '无消息')}",
                response.get("code"),
            )

        # 第二步：使用临时令牌进行最终认证
        url = self.get_api_url() + "/auth.do_auth"
        auth_data = {
            "userid": response["userid"],
            "token": response["token"],
            "appkey": self._appkey,
            "rgn": self._region,
        }

        # 如果 userid 发生变化，则更新
        if self._userid != response["userid"]:
            self._userid = response["userid"]

        send_data = json.dumps(auth_data)
        try:
            response_text = await self.post_async(url, send_data, header)
            response = json.loads(response_text)
        except Exception as e:
            raise LifeSmartAuthError(f"认证请求因网络错误失败: {e}") from e

        if response.get("code") == 0 and "usertoken" in response:
            self._usertoken = response["usertoken"]
            _LOGGER.info("成功登录并获取用户令牌。")
            return True

        raise LifeSmartAuthError(
            f"认证失败 (步骤 2): {response.get('message', '无消息')}",
            response.get("code"),
        )

    # ====================================================================
    # 接口：所有管理和查询接口
    # ====================================================================

    async def get_agt_list_async(self) -> dict[str, Any]:
        """获取用户下的所有中枢（网关）列表。(API: AgtGetList)"""
        return await self._async_call_api("AgtGetList")

    async def get_agt_details_async(self, agt: str) -> dict[str, Any]:
        """获取指定中枢的详细信息。(API: AgtGet)"""
        return await self._async_call_api("AgtGet", {HUB_ID_KEY: agt})

    async def get_all_device_async(self) -> list[dict[str, Any]]:
        """获取当前用户下的所有设备。(API: EpGetAll)"""
        return await self._async_call_api("EpGetAll")

    async def get_scene_list_async(self, agt: str) -> dict[str, Any]:
        """获取指定中枢下的所有场景。(API: SceneGet)"""
        return await self._async_call_api("SceneGet", {HUB_ID_KEY: agt})

    async def get_room_list_async(self, agt: str) -> dict[str, Any]:
        """获取指定中枢下配置的房间列表。(API: RoomGet)"""
        return await self._async_call_api("RoomGet", {HUB_ID_KEY: agt})

    async def set_scene_async(self, agt: str, scene_id: str) -> dict[str, Any]:
        """激活一个场景。(API: SceneSet)"""
        return await self._async_call_api("SceneSet", {HUB_ID_KEY: agt, "id": scene_id})

    async def send_epset_async(
        self, agt: str, me: str, idx: str, command_type: str, val: Any
    ) -> int:
        params = {
            HUB_ID_KEY: agt,
            DEVICE_ID_KEY: me,
            SUBDEVICE_INDEX_KEY: idx,
            "type": command_type,
            "val": val,
        }
        response = await self._async_call_api("EpSet", params)
        return response.get("code", -1)

    async def async_set_multi_ep_async(
        self, agt: str, me: str, io_list: list[dict]
    ) -> int:
        """向设备端点同时发送多个IO口的命令。(API: EpSet)

        Args:
            agt: 中枢ID。
            me: 设备ID。
            io_list: 一个包含多个IO设置的列表，
                     例如: [{"idx": "DYN", "type": "0xff", "val": 123},
                            {"idx": "RGBW", "type": "0x81", "val": 1}]
        """
        # LifeSmart的EpSet接口通过在val字段中传递一个列表来实现多IO口设置
        params = {HUB_ID_KEY: agt, DEVICE_ID_KEY: me, "val": io_list}
        response = await self._async_call_api("EpSet", params)
        return response.get("code", -1)

    async def get_epget_async(self, agt: str, me: str) -> dict[str, Any]:
        """获取指定设备的详细信息。(API: EpGet)"""
        response = await self._async_call_api(
            "EpGet", {HUB_ID_KEY: agt, DEVICE_ID_KEY: me}
        )
        return response.get(DEVICE_DATA_KEY, {})

    async def get_ir_remote_list_async(self, agt: str) -> dict[str, Any]:
        """获取指定中枢下的红外遥控器列表。(API: GetRemoteList)"""
        return await self._async_call_api(
            "GetRemoteList", {HUB_ID_KEY: agt}, api_path="/irapi"
        )

    async def send_ir_key_async(
        self, agt: str, ai: str, me: str, category: str, brand: str, keys: str
    ) -> dict[str, Any]:
        """发送一个红外按键命令。(API: SendKeys)"""
        params = {
            HUB_ID_KEY: agt,
            "ai": ai,
            DEVICE_ID_KEY: me,
            "category": category,
            "brand": brand,
            "keys": keys,
        }
        return await self._async_call_api("SendKeys", params, api_path="/irapi")

    # --- 设备直接控制的辅助方法 ---

    async def turn_on_light_switch_async(self, idx: str, agt: str, me: str) -> int:
        """开启一个灯或开关。"""
        return await self.send_epset_async(agt, me, idx, CMD_TYPE_ON, 1)

    async def turn_off_light_switch_async(self, idx: str, agt: str, me: str) -> int:
        """关闭一个灯或开关。"""
        return await self.send_epset_async(agt, me, idx, CMD_TYPE_OFF, 0)

    async def press_switch_async(
        self, idx: str, agt: str, me: str, duration_ms: int
    ) -> int:
        """执行点动操作（按下后在指定时间后自动弹起）。"""
        # 将毫秒转换为设备需要的 100ms 单位
        val = max(1, round(duration_ms / 100))
        return await self.send_epset_async(agt, me, idx, CMD_TYPE_PRESS, val)

    async def open_cover_async(self, agt: str, me: str, device_type: str) -> int:
        """开启窗帘或车库门。"""
        if device_type in GARAGE_DOOR_TYPES:
            return await self.send_epset_async(agt, me, "P3", CMD_TYPE_SET_VAL, 100)
        elif device_type in DOOYA_TYPES:
            return await self.send_epset_async(agt, me, "P2", CMD_TYPE_SET_VAL, 100)
        else:
            cmd_idx = "OP" if device_type == "SL_SW_WIN" else "P1"
            return await self.send_epset_async(agt, me, cmd_idx, CMD_TYPE_ON, 1)

    async def close_cover_async(self, agt: str, me: str, device_type: str) -> int:
        """关闭窗帘或车库门。"""
        if device_type in GARAGE_DOOR_TYPES:
            return await self.send_epset_async(agt, me, "P3", CMD_TYPE_SET_VAL, 0)
        elif device_type in DOOYA_TYPES:
            return await self.send_epset_async(agt, me, "P2", CMD_TYPE_SET_VAL, 0)
        else:
            cmd_idx = "CL" if device_type == "SL_SW_WIN" else "P2"
            return await self.send_epset_async(agt, me, cmd_idx, CMD_TYPE_ON, 1)

    async def stop_cover_async(self, agt: str, me: str, device_type: str) -> int:
        """停止窗帘或车库门。"""
        if device_type in GARAGE_DOOR_TYPES or device_type in DOOYA_TYPES:
            cmd_idx = "P3" if device_type in GARAGE_DOOR_TYPES else "P2"
            return await self.send_epset_async(
                agt, me, cmd_idx, CMD_TYPE_SET_CONFIG, CMD_TYPE_OFF
            )
        else:
            cmd_idx = "ST" if device_type == "SL_SW_WIN" else "P3"
            return await self.send_epset_async(agt, me, cmd_idx, CMD_TYPE_ON, 1)

    async def set_cover_position_async(
        self, agt: str, me: str, position: int, device_type: str
    ) -> int:
        """设置窗帘或车库门到指定位置。"""
        if device_type in GARAGE_DOOR_TYPES:
            return await self.send_epset_async(
                agt, me, "P3", CMD_TYPE_SET_VAL, position
            )
        elif device_type in DOOYA_TYPES:
            return await self.send_epset_async(
                agt, me, "P2", CMD_TYPE_SET_VAL, position
            )
        _LOGGER.warning("设备类型 %s 不支持设置位置。", device_type)
        return -1

    async def async_set_climate_hvac_mode(
        self,
        agt: str,
        me: str,
        device_type: str,
        hvac_mode: HVACMode,
        current_val: int = 0,
    ) -> int:
        """设置温控设备的 HVAC 模式。"""
        if hvac_mode == HVACMode.OFF:
            return await self.send_epset_async(agt, me, "P1", CMD_TYPE_OFF, 0)

        await self.send_epset_async(agt, me, "P1", CMD_TYPE_ON, 1)

        mode_val = REVERSE_LIFESMART_HVAC_MODE_MAP.get(hvac_mode)
        if mode_val is not None and device_type in [
            "SL_UACCB",
            "SL_NATURE",
            "SL_FCU",
            "V_AIR_P",
        ]:
            idx = "MODE" if device_type == "V_AIR_P" else "P7"
            return await self.send_epset_async(
                agt, me, idx, CMD_TYPE_SET_CONFIG, mode_val
            )

        if device_type == "SL_CP_AIR":
            mode_val = REVERSE_LIFESMART_CP_AIR_MODE_MAP.get(hvac_mode)
            if mode_val is not None:
                new_val = (current_val & ~(0b11 << 13)) | (mode_val << 13)
                return await self.send_epset_async(
                    agt, me, "P1", CMD_TYPE_SET_RAW, new_val
                )

        if device_type == "SL_CP_DN":
            is_auto = 1 if hvac_mode == HVACMode.AUTO else 0
            new_val = (current_val & ~(1 << 31)) | (is_auto << 31)
            return await self.send_epset_async(agt, me, "P1", CMD_TYPE_SET_RAW, new_val)

        if device_type == "SL_CP_VL":
            mode_map = {HVACMode.HEAT: 0, HVACMode.AUTO: 2}
            mode_val = mode_map.get(hvac_mode, 0)
            new_val = (current_val & ~(0b11 << 1)) | (mode_val << 1)
            return await self.send_epset_async(agt, me, "P1", CMD_TYPE_SET_RAW, new_val)
        return 0

    async def async_set_climate_temperature(
        self, agt: str, me: str, device_type: str, temp: float
    ) -> int:
        """设置温控设备的目标温度。"""
        temp_val = int(temp * 10)
        idx_map = {
            "V_AIR_P": ("tT", CMD_TYPE_SET_TEMP_DECIMAL),
            "SL_UACCB": ("P3", CMD_TYPE_SET_TEMP_DECIMAL),
            "SL_CP_DN": ("P3", CMD_TYPE_SET_RAW),
            "SL_CP_AIR": ("P4", CMD_TYPE_SET_RAW),
            "SL_NATURE": ("P8", CMD_TYPE_SET_TEMP_DECIMAL),
            "SL_FCU": ("P8", CMD_TYPE_SET_TEMP_FCU),
            "SL_CP_VL": ("P3", CMD_TYPE_SET_RAW),
        }
        if device_type in idx_map:
            idx, cmd_type = idx_map[device_type]
            return await self.send_epset_async(agt, me, idx, cmd_type, temp_val)
        return -1

    async def async_set_climate_fan_mode(
        self, agt: str, me: str, device_type: str, fan_mode: str, current_val: int = 0
    ) -> int:
        """设置温控设备的风扇模式。"""
        if device_type == "V_AIR_P":
            fan_val = LIFESMART_F_FAN_MODE_MAP.get(fan_mode)
            return await self.send_epset_async(
                agt, me, "F", CMD_TYPE_SET_CONFIG, fan_val
            )
        elif device_type == "SL_TR_ACIPM":
            fan_val = REVERSE_LIFESMART_ACIPM_FAN_MAP.get(fan_mode)
            return await self.send_epset_async(agt, me, "P2", CMD_TYPE_SET_RAW, fan_val)
        elif device_type in ["SL_NATURE", "SL_FCU"]:
            fan_val = REVERSE_LIFESMART_TF_FAN_MODE_MAP.get(fan_mode)
            return await self.send_epset_async(
                agt, me, "P9", CMD_TYPE_SET_CONFIG, fan_val
            )
        elif device_type == "SL_CP_AIR":
            fan_val = REVERSE_LIFESMART_CP_AIR_FAN_MAP.get(fan_mode)
            if fan_val is not None:
                new_val = (current_val & ~(0b11 << 15)) | (fan_val << 15)
                return await self.send_epset_async(
                    agt, me, "P1", CMD_TYPE_SET_RAW, new_val
                )
        return -1

    # --- 内部工具和私有方法 ---

    async def post_async(self, url: str, data: str, headers: dict) -> str:
        """使用 Home Assistant 的共享客户端会话发送 POST 请求。"""
        session = async_get_clientsession(self.hass)
        async with session.post(url, data=data, headers=headers) as response:
            response.raise_for_status()
            return await response.text()

    def get_signature(self, data: str) -> str:
        """生成 LifeSmart API 所需的 MD5 签名。"""
        return hashlib.md5(data.encode("utf-8")).hexdigest()

    def get_api_url(self) -> str:
        """根据所选区域生成基础 API URL。"""
        if not self._region or self._region.upper() == "AUTO":
            return "https://api.ilifesmart.com/app"
        return f"https://api.{self._region.lower()}.ilifesmart.com/app"

    def get_wss_url(self) -> str:
        """根据所选区域生成 WebSocket (WSS) URL。"""
        if not self._region or self._region.upper() == "AUTO":
            return "wss://api.ilifesmart.com:8443/wsapp/"
        return f"wss://api.{self._region.lower()}.ilifesmart.com:8443/wsapp/"

    def generate_system_request_body(self, tick: int, data: str) -> dict[str, Any]:
        """为请求体生成 'system' 节点。"""
        return {
            "ver": "1.0",
            "lang": "en",
            "userid": self._userid,
            "appkey": self._appkey,
            "time": tick,
            "sign": self.get_signature(data),
        }

    def generate_time_and_credential_data(self, tick: int) -> str:
        """为签名字符串生成凭据部分。"""
        return (
            f"time:{tick},userid:{self._userid},usertoken:{self._usertoken},"
            f"appkey:{self._appkey},apptoken:{self._apptoken}"
        )

    def generate_header(self) -> dict[str, str]:
        """生成默认的 HTTP 头部。"""
        return {"Content-Type": "application/json"}

    def generate_wss_auth(self) -> str:
        """为 WebSocket 连接生成认证消息。"""
        tick = int(time.time())
        sdata = "method:WbAuth," + self.generate_time_and_credential_data(tick)
        send_values = {
            "id": 1,
            "method": "WbAuth",
            "system": self.generate_system_request_body(tick, sdata),
        }
        return json.dumps(send_values)
