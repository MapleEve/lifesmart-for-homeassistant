"""
数据处理器 - 纯数据处理架构
由 @MapleEve 初始创建和维护

此模块实现各种字段的纯数据处理功能，符合正确的数据流原则：
客户端数据 → 数据处理器(提取值) → 映射配置 → 平台实体 → HA

核心功能:
- ALM位掩码处理：提取bit位状态
- EVTLO门锁事件处理：提取有价值的门锁数据
- O(1)性能，无文档解析
- 配置驱动架构，配置在config层
- 符合Clean Architecture原则
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from homeassistant.components.binary_sensor import BinarySensorDeviceClass

from ...config.alm_config import ALM_BIT_CONFIG, get_alm_bit_config, get_all_alm_bits
from ...config.lock_event_config import (
    EVTLO_DATA_CONFIG,
    get_all_evtlo_configs,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class ALMBitResult:
    """ALM位处理结果"""

    bit_position: int
    is_active: bool
    name: str
    description: str
    device_class: Optional[BinarySensorDeviceClass] = None
    friendly_name: Optional[str] = None


@dataclass
class EVTLODataResult:
    """EVTLO数据处理结果"""

    data_key: str
    value: Any
    name: str
    description: str
    platform: str
    friendly_name: Optional[str] = None
    device_class: Optional[Any] = None


class ALMDataProcessor:
    """ALM数据处理器 - 纯数据处理架构

    专注于数据转换，不解析文档，符合正确的数据流原则：
    客户端数据 → 数据处理器(提取bit状态) → 配置(ALM_BIT_CONFIG) → 平台实体 → HA

    特点:
    - O(1)性能，直接bit位操作
    - 配置驱动架构，配置在config层
    - 纯数据处理，不解析文字
    - 符合Clean Architecture
    """

    def process_alm_value(self, alm_value: int) -> List[ALMBitResult]:
        """处理ALM数值，提取所有bit状态

        这是核心数据处理方法，直接处理数值数据，不解析文档。

        Args:
            alm_value: ALM字段的原始整数值

        Returns:
            所有已定义bit位的处理结果列表
        """
        results = []

        # 遍历所有已配置的bit位
        for bit_position in ALM_BIT_CONFIG.keys():
            # 直接bit位操作，O(1)性能
            is_active = self.extract_bit_value(alm_value, bit_position)

            # 获取配置
            bit_config = ALM_BIT_CONFIG[bit_position]

            # 创建结果
            result = ALMBitResult(
                bit_position=bit_position,
                is_active=is_active,
                name=bit_config["name"],
                description=bit_config["description"],
                device_class=bit_config["device_class"],
                friendly_name=bit_config["friendly_name"],
            )
            results.append(result)

        return results

    def process_single_bit(
        self, alm_value: int, bit_position: int
    ) -> Optional[ALMBitResult]:
        """处理单个bit位

        Args:
            alm_value: ALM字段的原始整数值
            bit_position: 要处理的bit位置

        Returns:
            bit处理结果或None(如果bit位置未定义)
        """
        # 检查bit位置是否有效
        bit_config = get_alm_bit_config(bit_position)
        if not bit_config:
            return None

        # 提取bit状态
        is_active = self.extract_bit_value(alm_value, bit_position)

        # 创建结果
        return ALMBitResult(
            bit_position=bit_position,
            is_active=is_active,
            name=bit_config["name"],
            description=bit_config["description"],
            device_class=bit_config["device_class"],
            friendly_name=bit_config["friendly_name"],
        )

    def extract_bit_value(self, raw_value: int, bit_position: int) -> bool:
        """从原始值中提取特定bit位的状态

        这是核心的bit位操作，O(1)性能。

        Args:
            raw_value: 原始整数值
            bit_position: bit位置(0-31)

        Returns:
            bit位的状态(True/False)
        """
        try:
            return bool((raw_value >> bit_position) & 1)
        except (TypeError, ValueError):
            return False

    def generate_alm_subdevices(
        self, io_port: str = "ALM"
    ) -> Dict[str, Dict[str, Any]]:
        """生成ALM虚拟子设备配置

        基于预定义的ALM配置生成虚拟子设备。

        Args:
            io_port: IO口名称，默认为"ALM"

        Returns:
            虚拟子设备配置字典，格式: {子设备键: 配置}
        """
        virtual_subdevices = {}

        # 直接使用配置，无需解析
        for bit_position, bit_config in get_all_alm_bits().items():
            # 生成虚拟子设备键: ALM_bit0, ALM_bit1, etc.
            virtual_key = f"{io_port}_bit{bit_position}"

            # 生成子设备配置
            subdevice_config = {
                "description": bit_config["description"],
                "rw": "R",
                "data_type": "alm_binary_sensor",
                "conversion": "alm_bit_extraction",
                "detailed_description": bit_config["detail"],
                "device_class": bit_config["device_class"],
                "friendly_name": bit_config["friendly_name"],
                # ALM特定的元数据
                "_is_alm_subdevice": True,
                "_source_io_port": io_port,
                "_bit_position": bit_position,
                "_bit_name": bit_config["name"],
            }

            virtual_subdevices[virtual_key] = subdevice_config

        return virtual_subdevices


# 全局ALM数据处理器实例
alm_data_processor = ALMDataProcessor()


def is_alm_io_port(io_port: str) -> bool:
    """检查是否为ALM IO口"""
    return io_port.upper() == "ALM"


def process_alm_data(alm_value: int) -> List[ALMBitResult]:
    """处理ALM数据的便捷函数

    Args:
        alm_value: ALM字段的原始整数值

    Returns:
        ALM bit处理结果列表
    """
    return alm_data_processor.process_alm_value(alm_value)


def get_alm_subdevices() -> Dict[str, Dict[str, Any]]:
    """获取ALM子设备配置的便捷函数

    Returns:
        ALM虚拟子设备配置字典
    """
    return alm_data_processor.generate_alm_subdevices()


class EVTLODataProcessor:
    """门锁事件数据处理器 - 纯数据处理架构

    专注于EVTLO数据转换，只实现有真实用户价值的功能。
    不解析文档，符合正确的数据流原则：
    客户端数据 → 数据处理器(提取有用信息) → 配置(EVTLO_DATA_CONFIG) → 平台实体 → HA

    特点:
    - 只实现有价值的功能：门锁状态、用户编号、开锁方式、双开检测
    - O(1)性能，直接bit位操作
    - 配置驱动架构，配置在config层
    - 避免过度拆分（不生成无用的颜色分量）
    - 符合Clean Architecture
    """

    def process_evtlo_value(self, val: int, type_val: int) -> List[EVTLODataResult]:
        """处理EVTLO数值，提取有用的门锁数据

        只处理真正有用户价值的信息，避免无意义拆分。

        Args:
            val: EVTLO字段的val值
            type_val: EVTLO字段的type值

        Returns:
            有价值的EVTLO数据处理结果列表
        """
        results = []

        # 遍历所有已配置的有价值数据
        for data_key, config in EVTLO_DATA_CONFIG.items():
            # 提取对应的值
            value = self.extract_data_value(data_key, val, type_val, config)
            if value is not None:
                result = EVTLODataResult(
                    data_key=data_key,
                    value=value,
                    name=config["name"],
                    description=config["description"],
                    platform=config["platform"],
                    friendly_name=config["friendly_name"],
                    device_class=config.get("device_class"),
                )
                results.append(result)

        return results

    def extract_data_value(
        self, data_key: str, val: int, type_val: int, config: Dict[str, Any]
    ) -> Any:
        """从原始数据中提取特定数据项的值

        这是核心的数据提取方法，O(1)性能。

        Args:
            data_key: 数据键名
            val: 原始val值
            type_val: 原始type值
            config: 数据配置

        Returns:
            提取的数据值
        """
        extraction_logic = config.get("extraction_logic")
        extraction_params = config.get("extraction_params", {})

        if extraction_logic == "type_bit_0":
            # 门锁状态: type&1
            return bool(type_val & 1)

        elif extraction_logic == "bit_range":
            # 位范围提取（用户编号）
            start_bit = extraction_params.get("start_bit", 0)
            end_bit = extraction_params.get("end_bit", 0)
            bit_mask = (1 << (end_bit - start_bit + 1)) - 1
            return (val >> start_bit) & bit_mask

        elif extraction_logic == "bit_range_mapped":
            # 位范围提取并映射（开锁方式）
            start_bit = extraction_params.get("start_bit", 0)
            end_bit = extraction_params.get("end_bit", 0)
            mapping = extraction_params.get("mapping", {})

            bit_mask = (1 << (end_bit - start_bit + 1)) - 1
            extracted_value = (val >> start_bit) & bit_mask
            return mapping.get(extracted_value, f"未知({extracted_value})")

        elif extraction_logic == "dual_unlock_detection":
            # 双开模式检测: 检查bit16~31是否有值
            upper_16_bits = (val >> 16) & 0xFFFF
            return upper_16_bits > 0

        return None

    def generate_evtlo_subdevices(
        self, io_port: str = "EVTLO"
    ) -> Dict[str, Dict[str, Any]]:
        """生成EVTLO虚拟子设备配置

        只生成有价值的子设备，避免无意义拆分。

        Args:
            io_port: IO口名称，默认为"EVTLO"

        Returns:
            虚拟子设备配置字典
        """
        virtual_subdevices = {}

        for data_key, config in get_all_evtlo_configs().items():
            # 生成虚拟子设备键: EVTLO_lock_status, EVTLO_user_id, etc.
            virtual_key = f"{io_port}_{data_key}"

            # 生成子设备配置
            subdevice_config = {
                "description": config["description"],
                "rw": "R",
                "data_type": f"evtlo_{config['platform']}",
                "conversion": "evtlo_data_extraction",
                "detailed_description": config["description"],
                "device_class": config.get("device_class"),
                "friendly_name": config["friendly_name"],
                # EVTLO特定的元数据
                "_is_evtlo_subdevice": True,
                "_source_io_port": io_port,
                "_data_key": data_key,
                "_platform": config["platform"],
                "_extraction_logic": config["extraction_logic"],
                "_extraction_params": config.get("extraction_params"),
            }

            virtual_subdevices[virtual_key] = subdevice_config

        return virtual_subdevices


# 全局数据处理器实例
evtlo_data_processor = EVTLODataProcessor()


def is_evtlo_io_port(io_port: str) -> bool:
    """检查是否为EVTLO IO口"""
    return io_port.upper() == "EVTLO"


def process_evtlo_data(val: int, type_val: int) -> List[EVTLODataResult]:
    """处理EVTLO数据的便捷函数

    Args:
        val: EVTLO字段的val值
        type_val: EVTLO字段的type值

    Returns:
        EVTLO数据处理结果列表
    """
    return evtlo_data_processor.process_evtlo_value(val, type_val)


def get_evtlo_subdevices() -> Dict[str, Dict[str, Any]]:
    """获取EVTLO子设备配置的便捷函数

    Returns:
        EVTLO虚拟子设备配置字典
    """
    return evtlo_data_processor.generate_evtlo_subdevices()
