"""HACS implementation of LifeSmart by @MapleEve"""
import asyncio
import datetime
import json
import logging
import time

import websockets
from homeassistant.components import climate
from homeassistant.components.climate import FAN_HIGH, FAN_LOW, FAN_MEDIUM
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ATTR_MAX_MIREDS,
    ATTR_MIN_MIREDS,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_URL,
    Platform,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.helpers.entity import Entity

from .const import (
    AI_TYPES,
    BINARY_SENSOR_TYPES,
    CLIMATE_TYPES,
    CONF_AI_INCLUDE_AGTS,
    CONF_AI_INCLUDE_ITEMS,
    CONF_EXCLUDE_AGTS,
    CONF_EXCLUDE_ITEMS,
    CONF_LIFESMART_APPKEY,
    CONF_LIFESMART_APPTOKEN,
    CONF_LIFESMART_USERID,
    CONF_LIFESMART_USERTOKEN,
    COVER_TYPES,
    DEVICE_ID_KEY,
    DEVICE_NAME_KEY,
    DEVICE_TYPE_KEY,
    DEVICE_WITHOUT_IDXNAME,
    DOMAIN,
    EV_SENSOR_TYPES,
    GAS_SENSOR_TYPES,
    GENERIC_CONTROLLER_TYPES,
    GUARD_SENSOR_TYPES,
    HUB_ID_KEY,
    LIFESMART_HVAC_STATE_LIST,
    LIFESMART_SIGNAL_UPDATE_ENTITY,
    LIFESMART_STATE_MANAGER,
    LIGHT_DIMMER_TYPES,
    LIGHT_SWITCH_TYPES,
    LOCK_TYPES,
    OT_SENSOR_TYPES,
    SMART_PLUG_TYPES,
    SPOT_TYPES,
    SUBDEVICE_INDEX_KEY,
    SUPPORTED_PLATFORMS,
    SUPPORTED_SUB_BINARY_SENSORS,
    SUPPORTED_SUB_SWITCH_TYPES,
    SUPPORTED_SWTICH_TYPES,
    UNLOCK_METHOD,
    UPDATE_LISTENER,
)
from .lifesmart_client import LifeSmartClient

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    hass.data.setdefault(DOMAIN, {})

    app_key = config_entry.data.get(CONF_LIFESMART_APPKEY)
    app_token = config_entry.data.get(CONF_LIFESMART_APPTOKEN)
    user_token = config_entry.data.get(CONF_LIFESMART_USERTOKEN)
    user_id = config_entry.data.get(CONF_LIFESMART_USERID)
    baseurl = config_entry.data.get(CONF_URL)
    exclude_devices = config_entry.data.get(CONF_EXCLUDE_ITEMS, [])
    exclude_hubs = config_entry.data.get(CONF_EXCLUDE_AGTS, [])
    ai_include_hubs = config_entry.data.get(CONF_AI_INCLUDE_AGTS, [])
    ai_include_items = config_entry.data.get(CONF_AI_INCLUDE_ITEMS, [])

    # 监听配置选项更新
    update_listener = config_entry.add_update_listener(_async_update_listener)

    lifesmart_client = LifeSmartClient(
        baseurl,
        app_key,
        app_token,
        user_token,
        user_id,
    )

    devices = await lifesmart_client.get_all_device_async()

    hass.data[DOMAIN][config_entry.entry_id] = {
        "client": lifesmart_client,
        "exclude_devices": exclude_devices,
        "exclude_hubs": exclude_hubs,
        "ai_include_hubs": ai_include_hubs,
        "ai_include_items": ai_include_items,
        "devices": devices,
        UPDATE_LISTENER: update_listener,
    }

    for platform in SUPPORTED_PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(config_entry, platform)
        )

    async def send_keys(call):
        """Handle the service call."""
        agt = call.data[HUB_ID_KEY]
        me = call.data[DEVICE_ID_KEY]
        ai = call.data["ai"]
        category = call.data["category"]
        brand = call.data["brand"]
        keys = call.data["keys"]
        restkey = await hass.data[DOMAIN][config_entry.entry_id][
            "client"
        ].send_ir_key_async(
            agt,
            ai,
            me,
            category,
            brand,
            keys,
        )
        _LOGGER.debug("sendkey: %s", str(restkey))

    async def send_ackeys(call):
        """Handle the service call."""
        agt = call.data[HUB_ID_KEY]
        me = call.data[DEVICE_ID_KEY]
        ai = call.data["ai"]
        category = call.data["category"]
        brand = call.data["brand"]
        keys = call.data["keys"]
        power = call.data["power"]
        mode = call.data["mode"]
        temp = call.data["temp"]
        wind = call.data["wind"]
        swing = call.data["swing"]
        restackey = await hass.data[DOMAIN][config_entry.entry_id][
            "client"
        ].send_ir_ackey_async(
            agt,
            ai,
            me,
            category,
            brand,
            keys,
            power,
            mode,
            temp,
            wind,
            swing,
        )
        _LOGGER.debug("sendkey: %s", str(restackey))

    async def scene_set_async(call):
        """Handle the service call."""
        agt = call.data[HUB_ID_KEY]
        id = call.data["id"]
        restkey = await hass.data[DOMAIN][config_entry.entry_id][
            "client"
        ].set_scene_async(
            agt,
            id,
        )
        _LOGGER.debug("scene_set: %s", str(restkey))

    hass.services.async_register(DOMAIN, "send_keys", send_keys)
    hass.services.async_register(DOMAIN, "send_ackeys", send_ackeys)
    hass.services.async_register(DOMAIN, "scene_set", scene_set_async)

    ws_url = lifesmart_client.get_wss_url()
    hass.data[DOMAIN][LIFESMART_STATE_MANAGER] = LifeSmartStatesManager(hass, config_entry, ws_url=ws_url)
    hass.data[DOMAIN][LIFESMART_STATE_MANAGER].start()

    return True


async def data_update_handler(hass, config_entry, msg):
    data = msg["msg"]
    device_type = data[DEVICE_TYPE_KEY]
    hub_id = data[HUB_ID_KEY]
    device_id = data[DEVICE_ID_KEY]
    sub_device_key = data[SUBDEVICE_INDEX_KEY]
    exclude_devices = config_entry.data.get(CONF_EXCLUDE_ITEMS, [])
    exclude_hubs = config_entry.data.get(CONF_EXCLUDE_AGTS, [])
    ai_include_hubs = config_entry.data.get(CONF_AI_INCLUDE_AGTS, [])
    ai_include_items = config_entry.data.get(CONF_AI_INCLUDE_ITEMS, [])

    if (
            sub_device_key != "s"
            and device_id not in exclude_devices
            and hub_id not in exclude_hubs
    ):
        entity_id = generate_entity_id(
            device_type, hub_id, device_id, sub_device_key
        )
        _LOGGER.debug("已生成实体id - 设备号：%s 中枢：%s 设备类型：%s IDX:%s ", str(device_id), str(hub_id),
                      str(device_type), str(sub_device_key))

        if (
                device_type in SUPPORTED_SWTICH_TYPES
                and sub_device_key in SUPPORTED_SUB_SWITCH_TYPES
        ):
            dispatcher_send(
                hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entity_id}", data
            )
        elif (
                device_type in BINARY_SENSOR_TYPES
                and sub_device_key in SUPPORTED_SUB_BINARY_SENSORS
        ):
            dispatcher_send(
                hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entity_id}", data
            )

        elif device_type in COVER_TYPES and sub_device_key == "P1":
            attrs = dict(hass.states.get(entity_id).attributes)
            nval = data["val"]
            ntype = data["type"]
            attrs["current_position"] = nval & 0x7F
            nstat = None
            if ntype % 2 == 0:
                if nval > 0:
                    nstat = "open"
                else:
                    nstat = "closed"
            else:
                if nval & 0x80 == 0x80:
                    nstat = "opening"
                else:
                    nstat = "closing"
            hass.states.set(entity_id, nstat, attrs)
            dispatcher_send(
                hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entity_id}", data
            )
        elif device_type in EV_SENSOR_TYPES:
            attrs = hass.states.get(entity_id).attributes
            hass.states.set(entity_id, data["v"], attrs)
            dispatcher_send(
                hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entity_id}", data
            )
        elif device_type in GAS_SENSOR_TYPES and data["val"] > 0:
            attrs = hass.states.get(entity_id).attributes
            hass.states.set(entity_id, data["val"], attrs)
            dispatcher_send(
                hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entity_id}", data
            )
        elif device_type in SPOT_TYPES or device_type in LIGHT_SWITCH_TYPES:
            _LOGGER.debug("websocket_light_msg: %s ", str(msg))
            value = data["val"]
            idx = sub_device_key

            dispatcher_send(
                hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entity_id}", data
            )

        elif device_type in LIGHT_DIMMER_TYPES:
            attrs = dict(hass.states.get(entity_id).attributes)
            state = hass.states.get(entity_id).state
            _LOGGER.debug("websocket_light_msg: %s ", str(msg))
            _LOGGER.debug("websocket_light_attrs: %s", str(attrs))
            value = data["val"]
            idx = sub_device_key
            if idx in ["P1"]:
                if data["type"] % 2 == 1:
                    attrs[ATTR_BRIGHTNESS] = value
                    hass.states.set(entity_id, STATE_ON, attrs)
                else:
                    hass.states.set(entity_id, STATE_OFF, attrs)
            elif idx in ["P2"]:
                ratio = 1 - (value / 255)
                attrs[ATTR_COLOR_TEMP] = (
                        int((attrs[ATTR_MAX_MIREDS] - attrs[ATTR_MIN_MIREDS]) * ratio)
                        + attrs[ATTR_MIN_MIREDS]
                )
                hass.states.set(entity_id, state, attrs)
                dispatcher_send(
                    hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entity_id}", data
                )

        elif device_type in CLIMATE_TYPES:
            _idx = sub_device_key
            attrs = dict(hass.states.get(entity_id).attributes)
            nstat = hass.states.get(entity_id).state
            if _idx == "O":
                if data["type"] % 2 == 1:
                    nstat = attrs["last_mode"]
                    hass.states.set(entity_id, nstat, attrs)
                else:
                    nstat = climate.const.HVACMode.OFF
                    hass.states.set(entity_id, nstat, attrs)
            if _idx == "P1":
                if data["type"] % 2 == 1:
                    nstat = climate.const.HVACMode.HEAT
                    hass.states.set(entity_id, nstat, attrs)
                else:
                    nstat = climate.const.HVACMode.OFF
                    hass.states.set(entity_id, nstat, attrs)
            if _idx == "P2":
                if data["type"] % 2 == 1:
                    attrs["Heating"] = "true"
                    hass.states.set(entity_id, nstat, attrs)
                else:
                    attrs["Heating"] = "false"
                    hass.states.set(entity_id, nstat, attrs)
            elif _idx == "MODE":
                if data["type"] == 206:
                    if nstat != climate.const.HVACMode.OFF:
                        nstat = LIFESMART_HVAC_STATE_LIST[data["val"]]
                    attrs["last_mode"] = nstat
                    hass.states.set(entity_id, nstat, attrs)
            elif _idx == "F":
                if data["type"] == 206:
                    attrs["fan_mode"] = get_fan_mode(data["val"])
                    hass.states.set(entity_id, nstat, attrs)
            elif _idx == "tT" or _idx == "P3":
                if data["type"] == 136:
                    attrs["temperature"] = data["v"]
                    hass.states.set(entity_id, nstat, attrs)
            elif _idx == "T" or _idx == "P4":
                if data["type"] == 8 or data["type"] == 9:
                    attrs["current_temperature"] = data["v"]
                    hass.states.set(entity_id, nstat, attrs)
            dispatcher_send(
                hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entity_id}", data
            )
        elif device_type in LOCK_TYPES:
            if sub_device_key == "BAT":
                dispatcher_send(
                    hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entity_id}", data
                )
            elif sub_device_key == "EVTLO":
                val = data["val"]
                unlock_method = UNLOCK_METHOD.get(val >> 12, "Unknown")
                unlock_user = val & 0xFFF
                if val == 0:
                    is_unlock_success = False
                else:
                    is_unlock_success = True

                attrs = {
                    "unlocking_method": unlock_method,
                    "unlocking_user": unlock_user,
                    "device_type": device_type,
                    "unlocking_success": is_unlock_success,
                    "last_updated": datetime.datetime.fromtimestamp(
                        data["ts"] / 1000
                    ).strftime("%Y-%m-%d %H:%M:%S"),
                }

                dispatcher_send(
                    hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entity_id}", data
                )
                _LOGGER.debug("状态更新已推送 %s - 设备编号：%s -门锁更新数据:%s ",
                              str(LIFESMART_SIGNAL_UPDATE_ENTITY),
                              str(entity_id), str(data))

        elif device_type in OT_SENSOR_TYPES and sub_device_key in [
            "Z",
            "V",
            "P3",
            "P4",
        ]:
            attrs = hass.states.get(entity_id).attributes
            hass.states.set(entity_id, data["v"], attrs)
            dispatcher_send(
                hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entity_id}", data
            )
        elif device_type in SMART_PLUG_TYPES:
            if sub_device_key == "P1":
                attrs = hass.states.get(entity_id).attributes
                if data["type"] % 2 == 1:
                    hass.states.set(entity_id, STATE_ON, attrs)
                else:
                    hass.states.set(entity_id, STATE_OFF, attrs)
            elif sub_device_key in ["P2", "P3"]:
                attrs = hass.states.get(entity_id).attributes
                hass.states.set(entity_id, data["v"], attrs)
            dispatcher_send(
                hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entity_id}", data
            )
        else:
            _LOGGER.debug("Event is not supported")

    # AI event
    if (
            sub_device_key == "s"
            and device_id in ai_include_items
            and data[HUB_ID_KEY] in ai_include_hubs
    ):
        _LOGGER.info("AI Event: %s", str(msg))
        device_type = data["devtype"]
        hub_id = data[HUB_ID_KEY]
        entity_id = (
                "switch."
                + (
                        device_type + "_" + hub_id + "_" + device_id + "_" + sub_device_key
                ).lower()
        )


async def _async_update_listener(hass, config_entry):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)


class LifeSmartDevice(Entity):
    """LifeSmart base device."""

    def __init__(self, dev, lifesmart_client) -> None:
        """Initialize the switch."""

        self._name = dev[DEVICE_NAME_KEY]
        self._device_name = dev[DEVICE_NAME_KEY]
        self._agt = dev[HUB_ID_KEY]
        self._me = dev[DEVICE_ID_KEY]
        self._devtype = dev["devtype"]
        self._client = lifesmart_client
        attrs = {
            HUB_ID_KEY: self._agt,
            DEVICE_ID_KEY: self._me,
            "devtype": self._devtype,
        }
        self._attributes = attrs

    @property
    def object_id(self):
        """Return LifeSmart device id."""
        return self.entity_id

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    @property
    def name(self):
        """Return LifeSmart device name."""
        return self._name

    @property
    def assumed_state(self):
        """Return true if we do optimistic updates."""
        return False

    @property
    def should_poll(self):
        """check with the entity for an updated state."""
        return False

    async def async_lifesmart_epset(self, type, val, idx):
        """Send command to lifesmart device"""
        agt = self._agt
        me = self._me
        responsecode = await self._client.send_epset_async(type, val, idx, agt, me)
        return responsecode

    async def async_lifesmart_epget(self):
        """Get lifesmart device info"""
        agt = self._agt
        me = self._me
        response = await self._client.get_epget_async(agt, me)
        return response

    async def async_lifesmart_sceneset(self, type, rgbw):
        """Set the scene"""
        agt = self._agt
        id = self._me
        response = self._client.set_scene_async(agt, id)
        return response["code"]


class LifeSmartStatesManager:
    """Instance to manage websocket to get push data from LifeSmart service"""

    def __init__(self, hass, config_entry, ws_url):
        self._hass = hass
        self._config_entry = config_entry
        self._ws_url = ws_url
        self._ws = None
        self._lock = asyncio.Lock()
        self._task = None

    async def connect(self):
        async with self._lock:
            if self._ws is None:
                try:
                    self._ws = await websockets.connect(self._ws_url, ping_interval=None)
                    _LOGGER.debug("Lifesmart HACS: WebSocket connected")

                    # 发送验证数据
                    client = self._hass.data[DOMAIN][self._config_entry.entry_id]["client"]
                    send_data = client.generate_wss_auth()
                    await self._ws.send(send_data)
                    _LOGGER.debug("LifeSmart WebSocket sending auth data")

                except websockets.exceptions.InvalidURI as e:
                    _LOGGER.error("Lifesmart HACS: Invalid WebSocket URL: %s", str(e))
                except websockets.exceptions.InvalidHandshake as e:
                    _LOGGER.error("Lifesmart HACS: WebSocket handshake failed: %s", str(e))
                except Exception as e:
                    _LOGGER.error("Lifesmart HACS: WebSocket connection error: %s", str(e))
                    self._ws = None

    async def disconnect(self):
        async with self._lock:
            if self._ws is not None:
                await self._ws.close()
                self._ws = None
                _LOGGER.warning("Lifesmart HACS: WebSocket disconnected")

    async def _keep_alive(self):
        while True:
            await self.connect()
            if self._ws is None:
                _LOGGER.warning("Lifesmart HACS: WebSocket is not connected, waiting 10s for next retry")
                await asyncio.sleep(10)
                continue

        try:
            last_auth_time = time.time()
            async for message in self._ws:
                _LOGGER.debug("Lifesmart HACS: Received raw message: %s", message)
                if message == "wb closed":
                    _LOGGER.error(
                        "Lifesmart HACS: WebSocket closed without authentication. Check if the authentication process is working correctly.")
                    break

                try:
                    msg = json.loads(message)
                    if msg.get("message") == "success" and msg.get("code") == 0:
                        _LOGGER.info("Lifesmart HACS: WebSocket authentication successful")
                        last_auth_time = time.time()
                    elif msg.get("type") == "io":
                        _LOGGER.debug("Lifesmart HACS: Received IO message: %s", str(msg))
                        asyncio.create_task(data_update_handler(self._hass, self._config_entry, msg))
                    else:
                        _LOGGER.warning("Lifesmart HACS: Received unknown message type: %s", str(msg))
                except json.JSONDecodeError as e:
                    _LOGGER.error("Lifesmart HACS: Failed to parse WebSocket message as JSON: %s", str(e))

                # 每小时重新发送一次验证数据
                if time.time() - last_auth_time > 3600:
                    client = self._hass.data[DOMAIN][self._config_entry.entry_id]["client"]
                    send_data = client.generate_wss_auth()
                    await self._ws.send(send_data)
                    _LOGGER.debug("LifeSmart WebSocket re-sending auth data")

                    try:
                        response = await asyncio.wait_for(self._ws.recv(), timeout=10)
                        msg = json.loads(response)
                        if msg.get("message") == "success" and msg.get("code") == 0:
                            _LOGGER.info("Lifesmart HACS: WebSocket re-authentication successful")
                            last_auth_time = time.time()
                        else:
                            _LOGGER.warning("Lifesmart HACS: Unexpected response to re-auth message: %s", response)
                            break
                    except (asyncio.TimeoutError, json.JSONDecodeError):
                        _LOGGER.warning(
                            "Lifesmart HACS: No valid response to re-auth message within 10 seconds, disconnecting")
                        break

        except websockets.exceptions.ConnectionClosed as e:
            _LOGGER.warning(f"Lifesmart HACS: WebSocket connection closed: code={e.code}, reason={e.reason}")
        except Exception as e:
            _LOGGER.error("Lifesmart HACS: Error in WebSocket communication: %s", str(e))
        finally:
            await self.disconnect()
            _LOGGER.info("Lifesmart HACS: WebSocket disconnected, reconnecting in 10 seconds")
            await asyncio.sleep(10)

    def start(self):
        self._task = asyncio.create_task(self._keep_alive())

    def stop(self):
        if self._task is not None:
            self._task.cancel()
            self._task = None


def get_fan_mode(_fanspeed):
    fanmode = None
    if _fanspeed < 30:
        fanmode = FAN_LOW
    elif _fanspeed < 65 and _fanspeed >= 30:
        fanmode = FAN_MEDIUM
    elif _fanspeed >= 65:
        fanmode = FAN_HIGH
    return fanmode


def get_platform_by_device(device_type, sub_device=None):
    if device_type in SUPPORTED_SWTICH_TYPES:
        return Platform.SWITCH
    elif device_type in BINARY_SENSOR_TYPES:
        return Platform.BINARY_SENSOR
    elif device_type in COVER_TYPES:
        return Platform.COVER
    elif device_type in EV_SENSOR_TYPES + GAS_SENSOR_TYPES + OT_SENSOR_TYPES:
        return Platform.SENSOR
    elif device_type in SPOT_TYPES + LIGHT_SWITCH_TYPES + LIGHT_DIMMER_TYPES:
        return Platform.LIGHT
    elif device_type in CLIMATE_TYPES:
        return Platform.CLIMATE
    elif device_type in LOCK_TYPES and sub_device == "BAT":
        return Platform.SENSOR
    elif device_type in LOCK_TYPES and sub_device == "EVTLO":
        return Platform.BINARY_SENSOR
    elif device_type in SMART_PLUG_TYPES and sub_device == "P1":
        return Platform.SWITCH
    elif device_type in SMART_PLUG_TYPES and sub_device in ["P2", "P3"]:
        return Platform.SENSOR
    return ""


def generate_entity_id(device_type, hub_id, device_id, idx=None):
    hub_id = hub_id.replace("__", "_").replace("-", "_")
    if idx:
        sub_device = idx
    else:
        sub_device = None

    if device_type in [
        *SUPPORTED_SWTICH_TYPES,
        *BINARY_SENSOR_TYPES,
        *EV_SENSOR_TYPES,
        *GAS_SENSOR_TYPES,
        *SPOT_TYPES,
        *LIGHT_SWITCH_TYPES,
        *OT_SENSOR_TYPES,
        *SMART_PLUG_TYPES,
        *LOCK_TYPES,
    ]:
        if sub_device:
            return (
                    get_platform_by_device(device_type, sub_device)
                    + (
                            "."
                            + device_type
                            + "_"
                            + hub_id
                            + "_"
                            + device_id
                            + "_"
                            + sub_device
                    ).lower()
            )
        else:
            return (
                # no sub device (idx)
                    get_platform_by_device(device_type)
                    + ("." + device_type + "_" + hub_id + "_" + device_id).lower()
            )

    elif device_type in COVER_TYPES:
        return (
                Platform.COVER
                + ("." + device_type + "_" + hub_id + "_" + device_id).lower()
        )
    elif device_type in LIGHT_DIMMER_TYPES:
        return (
                Platform.LIGHT
                + ("." + device_type + "_" + hub_id + "_" + device_id + "_P1P2").lower()
        )
    elif device_type in CLIMATE_TYPES:
        return Platform.CLIMATE + (
                "." + device_type + "_" + hub_id + "_" + device_id
        ).lower().replace(":", "_").replace("@", "_")
