"""Custom cloud client for the LifeSmart integration by @MapleEve"""

import hashlib
import json
import logging
import time
from typing import Any, Optional

from homeassistant.components.climate import HVACMode
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
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


# ====================================================================
# 云端连接基类
# ====================================================================
class LifeSmartClient:
    """A class to manage LifeSmart API calls efficiently and robustly."""

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
        """Initialize the LifeSmart client."""
        self.hass = hass
        self._region = region
        self._appkey = appkey
        self._apptoken = apptoken
        self._usertoken = usertoken
        self._userid = userid
        self._apppassword = user_password

    # ====================================================================
    # 统一的API请求构建器
    # ====================================================================
    async def _async_call_api(
        self, method: str, params: Optional[dict] = None, api_path: str = "/api"
    ) -> dict[str, Any]:
        """A centralized method to build, sign, and send API requests."""
        url = f"{self.get_api_url()}{api_path}.{method}"
        tick = int(time.time())
        params = params or {}

        param_list = [f"method:{method}"]
        for key, value in sorted(params.items()):
            param_list.append(f"{key}:{value}")
        param_list.append(self.generate_time_and_credential_data(tick))
        sdata = ",".join(param_list)

        send_values = {
            "id": 1,
            "method": method,
            "system": self.generate_system_request_body(tick, sdata),
        }
        if params:
            send_values["params"] = params

        header = self.generate_header()
        send_data = json.dumps(send_values)

        _LOGGER.debug("API Request -> %s: %s", method, send_data)
        response_text = await self.post_async(url, send_data, header)
        response = json.loads(response_text)
        _LOGGER.debug("API Response <- %s: %s", method, response)

        if response.get("code") != 0:
            error_msg = f"API call '{method}' failed with code {response.get('code')}: {response.get('message')}"
            _LOGGER.error(error_msg)
            raise LifeSmartAPIError(error_msg, response.get("code"))

        return response.get("message", response)

    # --- Public API Methods ---

    # 登录到 LifeSmart 服务以获取用户令牌
    async def login_async(self) -> bool:
        """Login to LifeSmart service to get a user token."""
        # 登录流程特殊，包含两步，不使用通用调用器
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
            raise LifeSmartAuthError(
                f"Login request failed due to a network error: {e}"
            ) from e

        if response.get("code") != 0 or "token" not in response:
            raise LifeSmartAuthError(
                f"Login failed (step 1): {response.get('message', 'No message')}",
                response.get("code"),
            )

        url = self.get_api_url() + "/auth.do_auth"
        auth_data = {
            "userid": response["userid"],
            "token": response["token"],
            "appkey": self._appkey,
            "rgn": self._region,
        }

        # Update userid if it has changed
        if self._userid != response["userid"]:
            self._userid = response["userid"]

        send_data = json.dumps(auth_data)
        try:
            response_text = await self.post_async(url, send_data, header)
            response = json.loads(response_text)
        except Exception as e:
            raise LifeSmartAuthError(
                f"Auth request failed due to a network error: {e}"
            ) from e

        if response.get("code") == 0 and "usertoken" in response:
            self._usertoken = response["usertoken"]
            _LOGGER.info("Successfully logged in and obtained user token.")
            return True

        raise LifeSmartAuthError(
            f"Auth failed (step 2): {response.get('message', 'No message')}",
            response.get("code"),
        )

    # ====================================================================
    # 接口：所有管理和查询接口
    # ====================================================================

    async def get_agt_list_async(self) -> dict[str, Any]:
        """Get a list of all hubs (gateways) for the user. (API: AgtGetList)"""
        return await self._async_call_api("AgtGetList")

    async def get_agt_details_async(self, agt: str) -> dict[str, Any]:
        """Get detailed information for a single specified hub. (API: AgtGet)"""
        return await self._async_call_api("AgtGet", {"agt": agt})

    async def get_all_device_async(self) -> dict[str, Any]:
        """Get all devices for the current user. (API: EpGetAll)"""
        return await self._async_call_api("EpGetAll")

    async def get_scene_list_async(self, agt: str) -> dict[str, Any]:
        """Get all scenes for a specific hub. (API: SceneGet)"""
        return await self._async_call_api("SceneGet", {"agt": agt})

    async def get_room_list_async(self, agt: str) -> dict[str, Any]:
        """Get the list of rooms configured in a specific hub. (API: RoomGet)"""
        return await self._async_call_api("RoomGet", {"agt": agt})

    async def set_scene_async(self, agt: str, scene_id: str) -> dict[str, Any]:
        """Activate a scene. (API: SceneSet)"""
        response = await self._async_call_api("SceneSet", {"agt": agt, "id": scene_id})
        return response

    async def send_epset_async(
        self, agt: str, me: str, idx: str, command_type: str, val: Any
    ) -> int:
        """Send a generic command to a device endpoint. (API: EpSet)"""
        params = {"agt": agt, "me": me, "idx": idx, "type": command_type, "val": val}
        response = await self._async_call_api("EpSet", params)
        return response.get("code", -1)

    async def get_epget_async(self, agt: str, me: str) -> dict[str, Any]:
        """Get detailed information for a specific device. (API: EpGet)"""
        response = await self._async_call_api("EpGet", {"agt": agt, "me": me})
        return response.get("data", {})

    # --- IR Control (uses /irapi path) ---
    async def get_ir_remote_list_async(self, agt: str) -> dict[str, Any]:
        """Get the list of IR remotes for a specific hub."""
        return await self._async_call_api(
            "GetRemoteList", {"agt": agt}, api_path="/irapi"
        )

    async def send_ir_key_async(
        self, agt: str, ai: str, me: str, category: str, brand: str, keys: str
    ) -> dict[str, Any]:
        """Send an IR key."""
        params = {
            "agt": agt,
            "ai": ai,
            "me": me,
            "category": category,
            "brand": brand,
            "keys": keys,
        }
        return await self._async_call_api("SendKeys", params, api_path="/irapi")

    # --- Helper methods for direct control ---

    # 通用开启开关/灯
    async def turn_on_light_switch_async(self, idx: str, agt: str, me: str) -> int:
        """Turn on a light switch."""
        return await self.send_epset_async(agt, me, idx, "0x81", 1)

    # 通用关闭开关/灯
    async def turn_off_light_switch_async(self, idx: str, agt: str, me: str) -> int:
        """Turn off a light switch."""
        return await self.send_epset_async(agt, me, idx, "0x80", 0)

    # 点动开关方法
    async def press_switch_async(
        self, idx: str, agt: str, me: str, duration_ms: int
    ) -> int:
        """
        Press a switch to turn it on for a specified duration, then automatically off.
        (For devices like SL_P_SW)
        """
        # 将毫秒转换为设备需要的 100ms 单位
        val = max(1, round(duration_ms / 100))
        _LOGGER.debug(
            "Sending press command to %s-%s-%s: type=0x89, val=%d (duration: %dms)",
            agt,
            me,
            idx,
            val,
            duration_ms,
        )
        return await self.send_epset_async(agt, me, idx, "0x89", val)

    # 开启窗帘或车库门的异步方法
    async def open_cover_async(self, agt: str, me: str, device_type: str) -> int:
        """Open a cover/garage door."""
        if device_type in GARAGE_DOOR_TYPES:
            return await self.send_epset_async(agt, me, "P3", "0xCF", 100)
        elif device_type in DOOYA_TYPES:
            return await self.send_epset_async(agt, me, "P2", "0xCF", 100)
        else:
            # 适用于 SL_SW_WIN, SL_P_V2, SL_CN_* 等
            cmd_idx = (
                "OP"
                if device_type == "SL_SW_WIN"
                else "P1" if device_type in ["SL_CN_IF", "SL_CN_FE"] else "P2"
            )
            return await self.send_epset_async(agt, me, cmd_idx, "0x81", 1)

    # 关闭窗帘或车库门的异步方法
    async def close_cover_async(self, agt: str, me: str, device_type: str) -> int:
        """Close a cover/garage door."""
        if device_type in GARAGE_DOOR_TYPES:
            return await self.send_epset_async(agt, me, "P3", "0xCF", 0)
        elif device_type in DOOYA_TYPES:
            return await self.send_epset_async(agt, me, "P2", "0xCF", 0)
        else:
            cmd_idx = (
                "CL"
                if device_type == "SL_SW_WIN"
                else "P2" if device_type in ["SL_CN_IF", "SL_CN_FE"] else "P3"
            )
            return await self.send_epset_async(agt, me, cmd_idx, "0x81", 1)

    # 停止窗帘或车库门的异步方法
    async def stop_cover_async(self, agt: str, me: str, device_type: str) -> int:
        """Stop a cover/garage door."""
        if device_type in GARAGE_DOOR_TYPES or device_type in DOOYA_TYPES:
            cmd_idx = "P3" if device_type in GARAGE_DOOR_TYPES else "P2"
            return await self.send_epset_async(agt, me, cmd_idx, "0xCE", 0x80)
        else:
            cmd_idx = (
                "ST"
                if device_type == "SL_SW_WIN"
                else "P3" if device_type in ["SL_CN_IF", "SL_CN_FE"] else "P4"
            )
            return await self.send_epset_async(agt, me, cmd_idx, "0x81", 1)

    # 设置窗帘或车库门到特定位置的异步方法
    async def set_cover_position_async(
        self, agt: str, me: str, position: int, device_type: str
    ) -> int:
        """Set cover/garage door to a specific position."""
        if device_type in GARAGE_DOOR_TYPES:
            return await self.send_epset_async(agt, me, "P3", "0xCF", position)
        elif device_type in DOOYA_TYPES:
            return await self.send_epset_async(agt, me, "P2", "0xCF", position)
        _LOGGER.warning(
            "Device type %s does not support setting position.", device_type
        )
        return -1

    # 设置空调设备的异步方法
    async def async_set_climate_hvac_mode(
        self,
        agt: str,
        me: str,
        device_type: str,
        hvac_mode: HVACMode,
        current_val: int = 0,
    ) -> int:
        """Set HVAC mode for a climate device."""
        if hvac_mode == HVACMode.OFF:
            return await self.send_epset_async(agt, me, "P1", "0x80", 0)

        await self.send_epset_async(agt, me, "P1", "0x81", 1)

        mode_val = REVERSE_LIFESMART_HVAC_MODE_MAP.get(hvac_mode)
        if mode_val is not None and device_type in [
            "SL_UACCB",
            "SL_NATURE",
            "SL_FCU",
            "V_AIR_P",
        ]:
            idx = "MODE" if device_type == "V_AIR_P" else "P7"
            return await self.send_epset_async(agt, me, idx, "0xCE", mode_val)

        if device_type == "SL_CP_AIR":
            mode_val = REVERSE_LIFESMART_CP_AIR_MODE_MAP.get(hvac_mode)
            if mode_val is not None:
                # 更新 P1 的 bit 13-14
                new_val = (current_val & ~(0b11 << 13)) | (mode_val << 13)
                return await self.send_epset_async(agt, me, "P1", "0xFF", new_val)

        if device_type == "SL_CP_DN":
            is_auto = 1 if hvac_mode == HVACMode.AUTO else 0
            new_val = (current_val & ~(1 << 31)) | (is_auto << 31)
            return await self.send_epset_async(agt, me, "P1", "0xFF", new_val)

        if device_type == "SL_CP_VL":
            mode_map = {HVACMode.HEAT: 0, HVACMode.AUTO: 2}  # 映射回设备值
            mode_val = mode_map.get(hvac_mode, 0)
            new_val = (current_val & ~(0b11 << 1)) | (mode_val << 1)
            return await self.send_epset_async(agt, me, "P1", "0xFF", new_val)
        return 0

    # 设置空调温度的异步方法
    async def async_set_climate_temperature(
        self, agt: str, me: str, device_type: str, temp: float
    ) -> int:
        """Set target temperature for a climate device."""
        temp_val = int(temp * 10)
        idx_map = {
            "V_AIR_P": ("tT", "0x88"),
            "SL_UACCB": ("P3", "0x88"),
            "SL_CP_DN": ("P3", "0xFF"),
            "SL_CP_AIR": ("P4", "0xFF"),
            "SL_NATURE": ("P8", "0x88"),
            "SL_FCU": ("P8", "0x89"),
            "SL_CP_VL": ("P3", "0xFF"),
        }
        if device_type in idx_map:
            idx, cmd_type = idx_map[device_type]
            return await self.send_epset_async(agt, me, idx, cmd_type, temp_val)
        return -1

    # 设置空调风速的异步方法
    async def async_set_climate_fan_mode(
        self, agt: str, me: str, device_type: str, fan_mode: str, current_val: int = 0
    ) -> int:
        """Set fan mode for a climate device."""
        if device_type == "V_AIR_P":
            fan_val = LIFESMART_F_FAN_MODE_MAP.get(fan_mode)
            return await self.send_epset_async(agt, me, "F", "0xCE", fan_val)
        elif device_type == "SL_TR_ACIPM":
            fan_val = REVERSE_LIFESMART_ACIPM_FAN_MAP.get(fan_mode)
            return await self.send_epset_async(agt, me, "P2", "0xFF", fan_val)
        elif device_type in ["SL_NATURE", "SL_FCU"]:
            fan_val = REVERSE_LIFESMART_TF_FAN_MODE_MAP.get(fan_mode)
            return await self.send_epset_async(agt, me, "P9", "0xCE", fan_val)
        elif device_type == "SL_CP_AIR":
            fan_val = REVERSE_LIFESMART_CP_AIR_FAN_MAP.get(fan_mode)
            if fan_val is not None:
                # 更新 P1 的 bit 15-16
                new_val = (current_val & ~(0b11 << 15)) | (fan_val << 15)
                return await self.send_epset_async(agt, me, "P1", "0xFF", new_val)

        return -1

    # --- Utility and Private Methods ---

    async def post_async(self, url: str, data: str, headers: dict) -> str:
        """Send a POST request using Home Assistant's shared client session."""
        session = async_get_clientsession(self.hass)
        async with session.post(url, data=data, headers=headers) as response:
            response.raise_for_status()
            return await response.text()

    def get_signature(self, data: str) -> str:
        """Generate the MD5 signature required by the LifeSmart API."""
        return hashlib.md5(data.encode("utf-8")).hexdigest()

    def get_api_url(self) -> str:
        """Generate the base API URL based on the selected region."""
        if not self._region or self._region.upper() == "AUTO":
            return "https://api.ilifesmart.com/app"
        return f"https://api.{self._region.lower()}.ilifesmart.com/app"

    def get_wss_url(self) -> str:
        """Generate the WebSocket (WSS) URL based on the selected region."""
        if not self._region or self._region.upper() == "AUTO":
            return "wss://api.ilifesmart.com:8443/wsapp/"
        return f"wss://api.{self._region.lower()}.ilifesmart.com:8443/wsapp/"

    def generate_system_request_body(self, tick: int, data: str) -> dict[str, Any]:
        """Generate the 'system' node for the request body."""
        return {
            "ver": "1.0",
            "lang": "en",
            "userid": self._userid,
            "appkey": self._appkey,
            "time": tick,
            "sign": self.get_signature(data),
        }

    def generate_time_and_credential_data(self, tick: int) -> str:
        """Generate the credential part of the signature string."""
        return (
            f"time:{tick},userid:{self._userid},usertoken:{self._usertoken},"
            f"appkey:{self._appkey},apptoken:{self._apptoken}"
        )

    def generate_header(self) -> dict[str, str]:
        """Generate the default HTTP header."""
        return {"Content-Type": "application/json"}

    def generate_wss_auth(self) -> str:
        """Generate the authentication message for the WebSocket connection."""
        tick = int(time.time())
        sdata = "method:WbAuth," + self.generate_time_and_credential_data(tick)
        send_values = {
            "id": 1,
            "method": "WbAuth",
            "system": self.generate_system_request_body(tick, sdata),
        }
        return json.dumps(send_values)
