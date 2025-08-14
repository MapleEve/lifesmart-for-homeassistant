"""
VersionedDeviceStrategy - 版本化设备解析策略

处理支持多版本的设备，根据设备版本信息选择对应的配置。
从原始mapping_engine的版本化处理逻辑提取。

从原始mapping_engine.py的1111-1177行提取，包括：
- 版本信息提取
- 版本配置选择
- 智能回退机制

由 @MapleEve 创建，基于Phase 2.5关键重构任务
"""

from typing import Dict, Any

from .base_strategy import BaseDeviceStrategy
from .ha_constant_strategy import HAConstantStrategy


class VersionedDeviceStrategy(BaseDeviceStrategy):
    """
    版本化设备解析策略

    处理支持多版本的设备，根据fullCls字段或version字段选择对应配置。
    """

    def __init__(self, ha_constant_strategy: HAConstantStrategy):
        """
        初始化版本化设备策略

        Args:
            ha_constant_strategy: HA常量转换策略实例
        """
        self.ha_constant_strategy = ha_constant_strategy

    def can_handle(
        self, device_type: str, device: Dict[str, Any], raw_config: Dict[str, Any]
    ) -> bool:
        """
        判断是否为版本化设备

        Args:
            device_type: 设备类型
            device: 设备数据
            raw_config: 原始配置

        Returns:
            bool: 是否能处理此设备
        """
        return "versioned" in raw_config or "version_modes" in raw_config

    def resolve_device_mapping(
        self, device: Dict[str, Any], raw_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        解析版本化设备映射

        从原始mapping_engine._resolve_versioned_device方法提取

        Args:
            device: 设备数据字典
            raw_config: 原始设备配置

        Returns:
            解析后的设备配置
        """
        # 获取版本配置和设备版本
        device_version = self._extract_version_from_device(device)
        versions = self._get_version_modes(raw_config)

        if not versions:
            return self.create_error_result("No version configuration found")

        # 选择对应的版本配置
        selected_config = self._get_versioned_config_with_fallback(
            versions, device_version, device.get("devtype", "")
        )

        if not selected_config:
            return self.create_error_result(
                f"No configuration found for version: {device_version}"
            )

        # 使用HA常量转换选中的配置
        return self.ha_constant_strategy.convert_data_to_ha_mapping(selected_config)

    def get_strategy_name(self) -> str:
        return "VersionedDeviceStrategy"

    @property
    def priority(self) -> int:
        return 20  # 较高优先级，处理版本化设备

    def _extract_version_from_device(self, device: Dict[str, Any]) -> str:
        """
        从设备信息中提取版本

        从原始mapping_engine._extract_version_from_fullcls方法提取

        Args:
            device: 设备字典

        Returns:
            版本字符串
        """
        full_cls = device.get("fullCls", "")
        device_type = device.get("devtype", "")

        if full_cls and device_type:
            # 从fullCls中提取版本信息
            if f"{device_type}_V1" in full_cls:
                return "V1"
            elif f"{device_type}_V2" in full_cls:
                return "V2"
            elif f"{device_type}_V3" in full_cls:
                return "V3"

        # 尝试从version字段获取
        return device.get("version", "default")

    def _get_version_modes(self, raw_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取版本配置模式

        Args:
            raw_config: 原始配置

        Returns:
            版本配置字典
        """
        if "version_modes" in raw_config:
            return raw_config["version_modes"]

        versioned = raw_config.get("versioned")
        if isinstance(versioned, dict):
            return versioned.get("versions", {})

        return {}

    def _get_versioned_config_with_fallback(
        self, versions: Dict, device_version: str, device_type: str
    ) -> Dict:
        """
        获取版本化设备配置，支持智能回退机制

        从原始mapping_engine._get_versioned_config_with_fallback方法提取

        Args:
            versions: 版本配置字典
            device_version: 设备版本
            device_type: 设备类型

        Returns:
            选中的版本配置字典
        """
        # 1. 优先使用精确匹配的版本
        if str(device_version) in versions:
            return versions[str(device_version)]

        # 2. 尝试使用default版本
        if "default" in versions:
            return versions["default"]

        # 3. 智能回退：选择第一个可用版本
        if versions:
            first_version_key = next(iter(versions.keys()))
            return versions[first_version_key]

        # 4. 最后兜底：返回空配置
        return {}
