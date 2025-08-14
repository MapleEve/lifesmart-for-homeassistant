"""LifeSmart 集成的服务管理。

此模块负责注册和处理 LifeSmart 集成提供的所有服务调用，
包括红外命令发送、场景触发和点动开关等功能。

由 @MapleEve 创建，作为集成架构重构的一部分。
"""

import logging

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import PlatformNotReady, HomeAssistantError

from .core.client_base import LifeSmartClientBase
from .core.const import DEVICE_ID_KEY, HUB_ID_KEY, SUBDEVICE_INDEX_KEY, DOMAIN

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
            self.hass.services.async_register(
                DOMAIN, "send_ir_keys", self._send_ir_keys
            )
        if not self.hass.services.has_service(DOMAIN, "send_ackeys"):
            self.hass.services.async_register(DOMAIN, "send_ackeys", self._send_ackeys)
        if not self.hass.services.has_service(DOMAIN, "trigger_scene"):
            self.hass.services.async_register(
                DOMAIN, "trigger_scene", self._trigger_scene
            )
        if not self.hass.services.has_service(DOMAIN, "press_switch"):
            self.hass.services.async_register(
                DOMAIN, "press_switch", self._press_switch
            )
        _LOGGER.info("LifeSmart 服务已注册完成。")

    async def _send_ir_keys(self, call: ServiceCall) -> None:
        """处理发送红外按键的服务调用。

        Args:
            call: 服务调用对象，包含必要的参数
        """
        try:
            # 处理ai和idx参数（二选一）
            ai = call.data.get("ai")
            idx = call.data.get("idx")

            if not ai and not idx:
                raise HomeAssistantError(
                    "发送红外按键失败：'ai' 和 'idx' 参数必须提供其中一个"
                )
            await self.client.async_send_ir_key(
                call.data[HUB_ID_KEY],
                call.data[DEVICE_ID_KEY],
                call.data["category"],
                call.data["brand"],
                call.data["keys"],
                ai or "",  # ai参数，可能为空
                idx or "",  # idx参数，可能为空
            )
            _LOGGER.info("红外命令发送成功: %s", call.data)
        except PlatformNotReady as e:
            _LOGGER.warning("红外命令发送功能暂时不可用: %s", e)
        except HomeAssistantError as e:
            _LOGGER.error("发送红外命令时发生Home Assistant错误: %s", e)
        except Exception as e:
            _LOGGER.error("发送红外命令失败: %s", e)

    async def _send_ackeys(self, call: ServiceCall) -> None:
        """处理发送空调按键的服务调用。

        Args:
            call: 服务调用对象，包含空调相关参数
        """
        try:
            # 处理ai和idx参数（二选一）
            ai = call.data.get("ai")
            idx = call.data.get("idx")

            if not ai and not idx:
                _LOGGER.error("发送空调按键失败：'ai' 和 'idx' 参数必须提供其中一个")
                return
            # 准备空调控制选项
            ac_options = {
                "agt": call.data[HUB_ID_KEY],
                "me": call.data[DEVICE_ID_KEY],
                "category": call.data["category"],
                "brand": call.data["brand"],
                "key": call.data.get("key")
                or call.data.get("keys"),  # 支持key和keys参数
                "power": call.data["power"],
                "mode": call.data["mode"],
                "temp": call.data["temp"],
                "wind": call.data["wind"],
                "swing": call.data["swing"],
            }

            # 只在有值时才添加ai和idx参数
            if ai:
                ac_options["ai"] = ai
            if idx:
                ac_options["idx"] = idx

            # 处理可选的keyDetail参数
            if "keyDetail" in call.data:
                ac_options["keyDetail"] = call.data["keyDetail"]

            # 使用红外控制接口发送空调命令
            await self.client.async_ir_control(call.data[DEVICE_ID_KEY], ac_options)
            _LOGGER.info("空调红外命令发送成功: %s", call.data)
        except PlatformNotReady as e:
            _LOGGER.warning("空调红外控制功能暂时不可用: %s", e)
        except HomeAssistantError as e:
            _LOGGER.error("发送空调红外命令时发生Home Assistant错误: %s", e)
        except Exception as e:
            _LOGGER.error("发送空调红外命令失败: %s", e)

    async def _trigger_scene(self, call: ServiceCall) -> None:
        """处理触发场景的服务调用。

        Args:
            call: 服务调用对象，包含场景相关参数
        """
        agt = call.data.get(HUB_ID_KEY)
        scene_name = call.data.get("name")
        scene_id = call.data.get("id")

        if not agt:
            raise HomeAssistantError("触发场景失败：'agt' 参数不能为空。")

        if not scene_name and not scene_id:
            raise HomeAssistantError(
                "触发场景失败：'name' 和 'id' 参数必须提供其中一个。"
            )

        try:
            if scene_id:
                # 优先使用场景ID
                _LOGGER.info(
                    "正在通过服务调用触发场景: Hub=%s, SceneID=%s", agt, scene_id
                )
                await self.client.async_set_scene(agt, scene_id)
            else:
                # 使用场景名称
                _LOGGER.info(
                    "正在通过服务调用触发场景: Hub=%s, SceneName=%s", agt, scene_name
                )
                await self.client.async_set_scene(agt, scene_name)

            _LOGGER.info("场景触发成功。")
        except PlatformNotReady as e:
            _LOGGER.warning("场景触发功能暂时不可用: %s", e)
        except HomeAssistantError as e:
            _LOGGER.error("触发场景时发生Home Assistant错误: %s", e)
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
        except PlatformNotReady as e:
            _LOGGER.warning("点动开关功能暂时不可用: %s", e)
        except HomeAssistantError as e:
            _LOGGER.error("点动开关时发生Home Assistant错误: %s", e)
        except Exception as e:
            _LOGGER.error("点动开关失败: %s", e)
