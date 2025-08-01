"""LifeSmart 集成的服务管理。

此模块负责注册和处理 LifeSmart 集成提供的所有服务调用，
包括红外命令发送、场景触发和点动开关等功能。

由 @MapleEve 创建，作为集成架构重构的一部分。
"""

import logging

from homeassistant.core import HomeAssistant, ServiceCall

from .const import DEVICE_ID_KEY, HUB_ID_KEY, SUBDEVICE_INDEX_KEY, DOMAIN
from .core.client_base import LifeSmartClientBase

_LOGGER = logging.getLogger(__name__)


class LifeSmartServiceManager:
    """LifeSmart 服务管理器。

    负责注册和处理 LifeSmart 集成提供的所有服务。
    """

    def __init__(self, hass: HomeAssistant, client: LifeSmartClientBase) -> None:
        """初始化服务管理器。

        Args:
            hass: Home Assistant 核心实例
            client: LifeSmart 客户端实例
        """
        self.hass = hass
        self.client = client

    def register_services(self) -> None:
        """注册所有 LifeSmart 服务。"""
        # 只在服务不存在时注册，避免多个配置条目时的冲突
        if not self.hass.services.has_service(DOMAIN, "send_ir_keys"):
            self.hass.services.async_register(DOMAIN, "send_ir_keys", self._send_ir_keys)
        if not self.hass.services.has_service(DOMAIN, "trigger_scene"):
            self.hass.services.async_register(DOMAIN, "trigger_scene", self._trigger_scene)
        if not self.hass.services.has_service(DOMAIN, "press_switch"):
            self.hass.services.async_register(DOMAIN, "press_switch", self._press_switch)
        _LOGGER.info("LifeSmart 服务已注册完成。")

    async def _send_ir_keys(self, call: ServiceCall) -> None:
        """处理发送红外按键的服务调用。

        Args:
            call: 服务调用对象，包含必要的参数
        """
        try:
            await self.client.async_send_ir_key(
                call.data[HUB_ID_KEY],
                call.data["ai"],
                call.data[DEVICE_ID_KEY],
                call.data["category"],
                call.data["brand"],
                call.data["keys"],
            )
            _LOGGER.info("红外命令发送成功: %s", call.data)
        except Exception as e:
            _LOGGER.error("发送红外命令失败: %s", e)

    async def _trigger_scene(self, call: ServiceCall) -> None:
        """处理触发场景的服务调用。

        Args:
            call: 服务调用对象，包含场景相关参数
        """
        agt = call.data.get(HUB_ID_KEY)
        scene_id = call.data.get("id")

        if not agt or not scene_id:
            _LOGGER.error("触发场景失败：'agt' 和 'id' 参数不能为空。")
            return

        try:
            _LOGGER.info("正在通过服务调用触发场景: Hub=%s, SceneID=%s", agt, scene_id)
            await self.client.async_set_scene(agt, scene_id)
            _LOGGER.info("场景触发成功。")
        except Exception as e:
            _LOGGER.error("触发场景失败: %s", e)

    async def _press_switch(self, call: ServiceCall) -> None:
        """处理点动开关的服务调用。

        Args:
            call: 服务调用对象，包含实体和持续时间参数
        """
        entity_id = call.data.get("entity_id")
        duration = call.data.get("duration", 1000)  # 默认点动1秒

        if not entity_id:
            _LOGGER.error("点动开关失败：'entity_id' 参数不能为空。")
            return

        entity = self.hass.states.get(entity_id)
        if not entity:
            _LOGGER.error("未找到实体: %s", entity_id)
            return

        # 从实体属性中获取设备信息
        agt = entity.attributes.get(HUB_ID_KEY)
        me = entity.attributes.get(DEVICE_ID_KEY)
        idx = entity.attributes.get(SUBDEVICE_INDEX_KEY)

        if not all([agt, me, idx]):
            _LOGGER.error("实体 %s 缺少必要的属性 (agt, me, idx)。", entity_id)
            return

        try:
            await self.client.press_switch_async(idx, agt, me, duration)
            _LOGGER.info("点动开关成功: %s (持续时间: %dms)", entity_id, duration)
        except Exception as e:
            _LOGGER.error("点动开关失败: %s", e)
