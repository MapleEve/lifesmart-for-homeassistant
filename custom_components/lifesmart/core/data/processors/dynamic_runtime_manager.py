"""
LifeSmart 动态设备运行时管理器
由 @MapleEve 初始创建和维护

此模块负责管理动态分类设备的运行时状态变化，
包括设备模式切换、实体的动态添加/移除等功能。

主要功能:
- 监控动态分类设备的关键参数变化
- 重新评估设备模式并触发平台切换
- 管理实体的动态添加和移除
- 确保状态一致性
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Callable

_LOGGER = logging.getLogger(__name__)


@dataclass
class DeviceModeChangeEvent:
    """设备模式变化事件"""

    device_id: str
    device_type: str
    old_mode: Optional[str]
    new_mode: Optional[str]
    changed_parameters: Dict[str, Any]
    timestamp: datetime


@dataclass
class DynamicDeviceState:
    """动态设备状态追踪"""

    device_id: str
    device_type: str
    current_mode: Optional[str]
    supported_platforms: Set[str]
    active_entities: Dict[str, List[str]]  # platform -> entity_ids
    last_evaluation: datetime
    watch_parameters: Set[str]  # 需要监控的参数，如 ["P1", "P5"]


class DynamicDeviceRuntimeManager:
    """动态设备运行时管理器"""

    def __init__(self, mapping_engine, hass=None):
        """
        初始化运行时管理器

        Args:
            mapping_engine: 映射引擎实例
            hass: Home Assistant实例（可选）
        """
        self.mapping_engine = mapping_engine
        self.hass = hass

        # 动态设备状态跟踪
        self.tracked_devices: Dict[str, DynamicDeviceState] = {}

        # 模式变化回调
        self.mode_change_callbacks: List[Callable] = []

        # 支持的动态设备类型
        self.supported_dynamic_types = {"SL_NATURE", "SL_P", "SL_JEMA"}

        # 避免频繁重新评估的防抖机制
        self.evaluation_debounce = timedelta(seconds=5)

        _LOGGER.debug("Dynamic device runtime manager initialized")

    def register_device(self, device: Dict[str, Any]) -> bool:
        """
        注册需要动态管理的设备

        Args:
            device: 设备信息字典

        Returns:
            True if registered successfully
        """
        device_id = device.get("devid", "")
        device_type = device.get("devtype", "")

        if not device_id or device_type not in self.supported_dynamic_types:
            return False

        # 获取设备配置
        from ..config.device_specs import DEVICE_SPECS_DATA

        raw_config = DEVICE_SPECS_DATA.get(device_type, {})

        if not raw_config.get("dynamic", False):
            return False

        # 确定需要监控的参数
        watch_params = self._extract_watch_parameters(raw_config)

        # 进行初始评估
        current_mode = self._evaluate_device_mode(device, raw_config)
        supported_platforms = self._get_supported_platforms(raw_config, current_mode)

        # 创建设备状态跟踪
        device_state = DynamicDeviceState(
            device_id=device_id,
            device_type=device_type,
            current_mode=current_mode,
            supported_platforms=supported_platforms,
            active_entities={},
            last_evaluation=datetime.now(),
            watch_parameters=watch_params,
        )

        self.tracked_devices[device_id] = device_state

        _LOGGER.info(
            "Registered dynamic device %s (%s) in mode: %s",
            device_id,
            device_type,
            current_mode,
        )
        return True

    def update_device_data(
        self, device_id: str, new_data: Dict[str, Any]
    ) -> Optional[DeviceModeChangeEvent]:
        """
        更新设备数据并检查是否需要模式切换

        Args:
            device_id: 设备ID
            new_data: 新的设备数据

        Returns:
            模式变化事件（如果发生了变化）
        """
        if device_id not in self.tracked_devices:
            return None

        device_state = self.tracked_devices[device_id]

        # 防抖机制：避免频繁评估
        now = datetime.now()
        if now - device_state.last_evaluation < self.evaluation_debounce:
            return None

        # 检查关键参数是否发生变化
        changed_params = self._detect_parameter_changes(device_state, new_data)

        if not changed_params:
            return None

        # 重新评估设备模式
        from ..config.device_specs import DEVICE_SPECS_DATA

        raw_config = DEVICE_SPECS_DATA.get(device_state.device_type, {})

        device = {
            "devid": device_id,
            "devtype": device_state.device_type,
            "data": new_data,
        }

        new_mode = self._evaluate_device_mode(device, raw_config)
        old_mode = device_state.current_mode

        # 更新评估时间
        device_state.last_evaluation = now

        # 检查是否发生模式变化
        if new_mode != old_mode:
            # 更新设备状态
            device_state.current_mode = new_mode
            device_state.supported_platforms = self._get_supported_platforms(
                raw_config, new_mode
            )

            # 创建变化事件
            change_event = DeviceModeChangeEvent(
                device_id=device_id,
                device_type=device_state.device_type,
                old_mode=old_mode,
                new_mode=new_mode,
                changed_parameters=changed_params,
                timestamp=now,
            )

            _LOGGER.warning(
                f"Device {device_id} mode changed: {old_mode} -> {new_mode}"
            )

            # 通知回调
            self._notify_mode_change(change_event)

            return change_event

        return None

    def get_current_platforms(self, device_id: str) -> Set[str]:
        """
        获取设备当前支持的平台

        Args:
            device_id: 设备ID

        Returns:
            支持的平台集合
        """
        if device_id in self.tracked_devices:
            return self.tracked_devices[device_id].supported_platforms.copy()
        return set()

    def get_device_mode(self, device_id: str) -> Optional[str]:
        """
        获取设备当前模式

        Args:
            device_id: 设备ID

        Returns:
            当前模式或None
        """
        if device_id in self.tracked_devices:
            return self.tracked_devices[device_id].current_mode
        return None

    def register_mode_change_callback(
        self, callback: Callable[[DeviceModeChangeEvent], None]
    ):
        """
        注册模式变化回调函数

        Args:
            callback: 回调函数
        """
        self.mode_change_callbacks.append(callback)

    def _extract_watch_parameters(self, raw_config: Dict) -> Set[str]:
        """
        从配置中提取需要监控的参数

        Args:
            raw_config: 原始设备配置

        Returns:
            需要监控的参数集合
        """
        watch_params = set()

        # 从条件表达式中提取参数
        if "switch_mode" in raw_config:
            condition = raw_config["switch_mode"].get("condition", "")
            if self.mapping_engine.device_classifier:
                params = self.mapping_engine.device_classifier.get_supported_variables(
                    condition
                )
                watch_params.update(params)

        if "climate_mode" in raw_config:
            condition = raw_config["climate_mode"].get("condition", "")
            if self.mapping_engine.device_classifier:
                params = self.mapping_engine.device_classifier.get_supported_variables(
                    condition
                )
                watch_params.update(params)

        if "control_modes" in raw_config:
            for mode_config in raw_config["control_modes"].values():
                condition = mode_config.get("condition", "")
                if condition and self.mapping_engine.device_classifier:
                    params = (
                        self.mapping_engine.device_classifier.get_supported_variables(
                            condition
                        )
                    )
                    watch_params.update(params)

        return watch_params

    def _evaluate_device_mode(self, device: Dict, raw_config: Dict) -> Optional[str]:
        """
        评估设备模式

        Args:
            device: 设备信息
            raw_config: 原始配置

        Returns:
            设备模式
        """
        if self.mapping_engine.device_classifier:
            return self.mapping_engine.device_classifier.classify_device(
                raw_config, device.get("data", {})
            )
        return None

    def _get_supported_platforms(
        self, raw_config: Dict, mode: Optional[str]
    ) -> Set[str]:
        """
        根据模式获取支持的平台

        Args:
            raw_config: 原始配置
            mode: 当前模式

        Returns:
            支持的平台集合
        """
        if not mode:
            return set()

        platforms = set()

        # SL_NATURE风格
        if mode == "switch_mode" and "switch_mode" in raw_config:
            switch_config = raw_config["switch_mode"]
            if switch_config.get("io"):
                platforms.add("switch")
            if switch_config.get("sensor_io"):
                platforms.add("sensor")

        elif mode == "climate_mode" and "climate_mode" in raw_config:
            climate_config = raw_config["climate_mode"].get("climate", {})
            for platform in climate_config.keys():
                if platform != "climate":  # climate是配置键，不是平台名
                    platforms.add(platform)
            platforms.add("climate")  # 总是包含climate平台

        # SL_P/SL_JEMA风格
        elif "control_modes" in raw_config and mode in raw_config["control_modes"]:
            mode_config = raw_config["control_modes"][mode]
            for platform in mode_config.keys():
                if platform != "condition":
                    platforms.add(platform)

        return platforms

    def _detect_parameter_changes(
        self, device_state: DynamicDeviceState, new_data: Dict
    ) -> Dict[str, Any]:
        """
        检测关键参数是否发生变化

        Args:
            device_state: 设备状态
            new_data: 新数据

        Returns:
            变化的参数字典
        """
        changed_params = {}

        # TODO: 需要与之前的数据进行比较
        # 这里简化处理，只要有监控参数的数据更新就认为可能发生变化
        for param in device_state.watch_parameters:
            if param in new_data:
                changed_params[param] = new_data[param]

        return changed_params

    def _notify_mode_change(self, event: DeviceModeChangeEvent):
        """
        通知所有注册的回调函数

        Args:
            event: 模式变化事件
        """
        for callback in self.mode_change_callbacks:
            try:
                callback(event)
            except Exception as e:
                _LOGGER.error(f"Mode change callback failed: {e}")


# 全局运行时管理器实例（延迟初始化）
_runtime_manager: Optional[DynamicDeviceRuntimeManager] = None


def get_runtime_manager(
    mapping_engine=None, hass=None
) -> Optional[DynamicDeviceRuntimeManager]:
    """
    获取全局运行时管理器实例

    Args:
        mapping_engine: 映射引擎（首次调用时需要）
        hass: Home Assistant实例（可选）

    Returns:
        运行时管理器实例
    """
    global _runtime_manager

    if _runtime_manager is None and mapping_engine is not None:
        _runtime_manager = DynamicDeviceRuntimeManager(mapping_engine, hass)

    return _runtime_manager
