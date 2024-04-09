import asyncio
import logging
import time
import hashlib
import json
import aiohttp

_LOGGER = logging.getLogger(__name__)


class LifeSmartClient:
    """A class for manage LifeSmart API."""

    def __init__(
        self,
        baseurl,
        appkey,
        apptoken,
        usertoken,
        userid,
    ) -> None:
        self._baseurl = baseurl
        self._appkey = appkey
        self._apptoken = apptoken
        self._usertoken = usertoken
        self._userid = userid

    async def get_all_device_async(self):
        """Get all devices belong to current user."""
        url = self.get_api_url() + "/api.EpGetAll"
        tick = int(time.time())
        sdata = "method:EpGetAll," + self.generate_time_and_credential_data(tick)

        send_values = {
            "id": 1,
            "method": "EpGetAll",
            "system": self.generate_system_request_body(tick, sdata),
        }
        header = self.generate_header()
        send_data = json.dumps(send_values)

        response = json.loads(await self.post_async(url, send_data, header))
        _LOGGER.debug("EpGetAll_res: %s", response)
        if response["code"] == 0:
            return response["message"]
        return False

    async def get_all_scene_async(self, agt):
        """Get all scenes belong to current user."""
        url = self.get_api_url() + "/api.SceneGet"
        tick = int(time.time())
        sdata = (
            "method:SceneGet,agt:"
            + agt
            + ","
            + self.generate_time_and_credential_data(tick)
        )
        send_values = {
            "id": 1,
            "method": "SceneGet",
            "params": {
                "agt": agt,
            },
            "system": self.generate_system_request_body(tick, sdata),
        }
        header = self.generate_header()
        send_data = json.dumps(send_values)
        response = json.loads(await self.post_async(url, send_data, header))
        if response["code"] == 0:
            return response["message"]
        return False

    async def set_scene_async(self, agt, id):
        """Set the scene by scene id to LifeSmart"""
        url = self.get_api_url() + "/api.SceneSet"
        tick = int(time.time())
        # keys = str(keys)
        sdata = (
            "method:SceneSet,agt:"
            + agt
            + ",id:"
            + id
            + ","
            + self.generate_time_and_credential_data(tick)
        )
        send_values = {
            "id": 101,
            "method": "SceneSet",
            "params": {
                "agt": agt,
                "id": id,
            },
            "system": self.generate_system_request_body(tick, sdata),
        }
        header = self.generate_header()
        send_data = json.dumps(send_values)

        response = json.loads(await self.post_async(url, send_data, header))
        return response

    async def send_ir_key_async(self, agt, ai, me, category, brand, keys):
        """Send an IR key to a specific device."""
        url = self.get_api_url() + "/irapi.SendKeys"
        tick = int(time.time())
        # keys = str(keys)
        sdata = (
            "method:SendKeys,agt:"
            + agt
            + ",ai:"
            + ai
            + ",brand:"
            + brand
            + ",category:"
            + category
            + ",keys:"
            + keys
            + ",me:"
            + me
            + ","
            + self.generate_time_and_credential_data(tick)
        )
        send_values = {
            "id": 1,
            "method": "SendKeys",
            "params": {
                "agt": agt,
                "me": me,
                "category": category,
                "brand": brand,
                "ai": ai,
                "keys": keys,
            },
            "system": self.generate_system_request_body(tick, sdata),
        }
        header = self.generate_header()
        send_data = json.dumps(send_values)

        response = json.loads(await self.post_async(url, send_data, header))
        return response

    async def send_ir_ackey_async(
        self,
        agt,
        ai,
        me,
        category,
        brand,
        key,
        power,
        mode,
        temp,
        wind,
        swing,
    ):
        """Send an IR AIR Conditioner Key to a specific device."""
        url = self.get_api_url() + "/irapi.SendACKeys"
        tick = int(time.time())
        # keys = str(keys)
        sdata = (
            "method:SendACKeys"
            + ",agt:"
            + agt
            + ",ai:"
            + ai
            + ",brand:"
            + brand
            + ",category:"
            + category
            + ",key:"
            + key
            + ",me:"
            + me
            + ",mode:"
            + str(mode)
            + ",power:"
            + str(power)
            + ",swing:"
            + str(swing)
            + ",temp:"
            + str(temp)
            + ",wind:"
            + str(wind)
            + ","
            + self.generate_time_and_credential_data(tick)
        )
        _LOGGER.debug("sendackey: %s", str(sdata))
        send_values = {
            "id": 1,
            "method": "SendACKeys",
            "params": {
                "agt": agt,
                "me": me,
                "category": category,
                "brand": brand,
                "ai": ai,
                "key": key,
                "power": power,
                "mode": mode,
                "temp": temp,
                "wind": wind,
                "swing": swing,
            },
            "system": self.generate_system_request_body(tick, sdata),
        }
        header = self.generate_header()
        send_data = json.dumps(send_values)

        response = json.loads(await self.post_async(url, send_data, header))
        _LOGGER.debug("sendackey_res: %s", str(response))
        return response

    async def turn_on_light_swith_async(self, idx, agt, me):
        return await self.send_epset_async("0x81", 1, idx, agt, me)

    async def turn_off_light_swith_async(self, idx, agt, me):
        return await self.send_epset_async("0x80", 0, idx, agt, me)

    async def send_epset_async(self, type, val, idx, agt, me):
        """Send a command to sepcific device."""
        url = self.get_api_url() + "/api.EpSet"
        tick = int(time.time())
        sdata = (
            "method:EpSet"
            + ",agt:"
            + agt
            + ",idx:"
            + idx
            + ",me:"
            + me
            + ",type:"
            + type
            + ",val:"
            + str(val)
            + ","
            + self.generate_time_and_credential_data(tick)
        )
        send_values = {
            "id": 1,
            "method": "EpSet",
            "system": self.generate_system_request_body(tick, sdata),
            "params": {"agt": agt, "me": me, "idx": idx, "type": type, "val": val},
        }

        header = self.generate_header()
        send_data = json.dumps(send_values)

        response = json.loads(await self.post_async(url, send_data, header))
        _LOGGER.debug("epset_res: %s", str(response))
        return response["code"]

    async def get_epget_async(self, agt, me):
        """Get device info."""
        url = self.get_api_url() + "/api.EpGet"
        tick = int(time.time())
        sdata = (
            "method:EpGet,agt:"
            + agt
            + ",me:"
            + me
            + ","
            + self.generate_time_and_credential_data(tick)
        )
        send_values = {
            "id": 1,
            "method": "EpGet",
            "system": self.generate_system_request_body(tick, sdata),
            "params": {"agt": agt, "me": me},
        }
        header = self.generate_header()
        send_data = json.dumps(send_values)

        response = json.loads(await self.post_async(url, send_data, header))
        _LOGGER.debug("epget_res: %s", str(response))
        return response["message"]["data"]

    async def get_ir_remote_list_async(self, agt):
        """Get remote list for a specific station"""
        url = self.get_api_url() + "/irapi.GetRemoteList"

        tick = int(time.time())
        sdata = (
            "method:GetRemoteList,agt:"
            + agt
            + ","
            + self.generate_time_and_credential_data(tick)
        )
        send_values = {
            "id": 1,
            "method": "GetRemoteList",
            "params": {"agt": agt},
            "system": self.generate_system_request_body(tick, sdata),
        }
        header = self.generate_header()
        send_data = json.dumps(send_values)

        response = json.loads(await self.post_async(url, send_data, header))
        _LOGGER.debug("GetRemoteList_res: %s", str(response))
        return response["message"]

    async def get_ir_remote_async(self, agt, ai):
        """Get a remote setting for sepcific device."""
        url = self.get_api_url() + "/irapi.GetRemote"

        tick = int(time.time())
        sdata = (
            "method:GetRemote,agt:"
            + agt
            + ",ai:"
            + ai
            + ",needKeys:2"
            + ","
            + self.generate_time_and_credential_data(tick)
        )
        send_values = {
            "id": 1,
            "method": "GetRemote",
            "params": {"agt": agt, "ai": ai, "needKeys": 2},
            "system": self.generate_system_request_body(tick, sdata),
        }
        header = self.generate_header()
        send_data = json.dumps(send_values)

        response = json.loads(await self.post_async(url, send_data, header))
        _LOGGER.debug("get_ir_remote_res: %s", str(response))
        return response["message"]["codes"]

    async def post_async(self, url, data, headers):
        """Async method to make a POST api call"""
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data, headers=headers) as response:
                response_text = await response.text()
                return response_text

    def get_signature(self, data):
        """Generate signature required by LifeSmart API"""
        return hashlib.md5(data.encode(encoding="UTF-8")).hexdigest()

    def get_api_url(self):
        """Generate api URL"""
        return "https://" + self._baseurl + "/app"

    def get_wss_url(self):
        """Generate websocket (wss) URL"""
        return "wss://" + self._baseurl + ":8443/wsapp/"

    def generate_system_request_body(self, tick, data):
        """Generate system node in request body which contain credential and signature"""
        return {
            "ver": "1.0",
            "lang": "en",
            "userid": self._userid,
            "appkey": self._appkey,
            "time": tick,
            "sign": self.get_signature(data),
        }

    def generate_time_and_credential_data(self, tick):
        """Generate default parameter required in body"""

        return (
            "time:"
            + str(tick)
            + ",userid:"
            + self._userid
            + ",usertoken:"
            + self._usertoken
            + ",appkey:"
            + self._appkey
            + ",apptoken:"
            + self._apptoken
        )

    def generate_header(self):
        """Generate default http header required by LifeSmart"""
        return {"Content-Type": "application/json"}

    def generate_wss_auth(self):
        """Generate authentication message with signature for wss connection"""
        tick = int(time.time())
        sdata = "method:WbAuth," + self.generate_time_and_credential_data(tick)

        send_values = {
            "id": 1,
            "method": "WbAuth",
            "system": self.generate_system_request_body(tick, sdata),
        }
        send_data = json.dumps(send_values)
        return send_data
