"""
LifeSmart 集成的业务协调辅助函数模块。

此模块专注于业务协调层逻辑，包括实体ID生成、设备类型检查等。
数据转换和平台检测功能已迁移到utils/模块。

重构说明:
- 平台检测功能 -> utils/platform_detection.py
- 数据转换功能 -> utils/conversion.py
- 保留业务协调和实体生成功能
"""

import logging
import re

from homeassistant.const import Platform

from .const import (
    DEVICE_FULLCLS_KEY,
    DEVICE_TYPE_KEY,
    DEVICE_DATA_KEY,
)
# 从utils模块导入转换后的函数
from .utils import (
    get_device_platform_mapping,
)

_LOGGER = logging.getLogger(__name__)


# ====================================================================
# 实体ID生成和管理 (Entity ID Generation and Management)
# ====================================================================
def generate_unique_id(
    hub_id: str,
    device_id: str,
    sub_key: str = None,
    platform: Platform = None,
) -> str:
    """
    为 LifeSmart 设备生成唯一ID。

    此函数为每个平台的每个设备子部件生成一个唯一标识符，用于在Home Assistant中标识实体。
    确保即使设备重命名，实体仍能保持其历史状态和配置。

    Args:
        hub_id: 智慧中心的ID (来自设备的'agt'字段)
        device_id: 设备的唯一ID (来自设备的'me'字段)
        sub_key: 子设备键，如'L1', 'P2'等 (可选)
        platform: Home Assistant平台类型 (可选，用于多平台设备)

    Returns:
        格式化的唯一ID字符串

    Examples:
        generate_unique_id("hub1", "dev1") -> "lifesmart_hub1_dev1"
        generate_unique_id("hub1", "dev1", "L1") -> "lifesmart_hub1_dev1_L1"
        generate_unique_id("hub1", "dev1", "L1", Platform.SWITCH) -> "lifesmart_hub1_dev1_L1_switch"
    """
    # 基础ID由hub和device组成
    unique_id = f"lifesmart_{hub_id}_{device_id}"

    # 添加子键（如果存在）
    if sub_key:
        unique_id = f"{unique_id}_{sub_key}"

    # 为多平台设备添加平台标识
    if platform and isinstance(platform, Platform):
        unique_id = f"{unique_id}_{platform.value}"

    return unique_id


# ====================================================================
# 设备类型检查和版本处理 (Device Type Checking and Version Handling)
# ====================================================================
def is_versioned_device_type(device: dict, expected_version: str = None) -> bool:
    """
    检查设备是否为版本化设备类型。

    某些LifeSmart设备具有多个版本，通过fullCls字段区分。
    例如SL_SW_DM1_V1 vs SL_SW_DM1_V2具有不同的功能集。

    Args:
        device: 设备字典
        expected_version: 期望的版本字符串，如"V1"或"V2" (可选)

    Returns:
        如果设备是版本化设备且匹配期望版本则返回True，否则返回False
    """
    device_type = device.get(DEVICE_TYPE_KEY, "")
    full_cls = device.get(DEVICE_FULLCLS_KEY, "")

    # 如果不是版本化设备类型，返回False
    from .device import VERSIONED_DEVICE_TYPES

    if device_type not in VERSIONED_DEVICE_TYPES:
        return False

    # 如果没有指定期望版本，只要是版本化设备就返回True
    if not expected_version:
        return "_V" in full_cls

    # 检查是否匹配期望的版本
    expected_full_type = f"{device_type}_{expected_version}"
    return expected_full_type in full_cls


def get_device_version(device: dict) -> str:
    """
    获取设备的版本信息。

    Args:
        device: 设备字典

    Returns:
        版本字符串，如"V1"、"V2"，无版本信息时返回空字符串
    """
    device_type = device.get(DEVICE_TYPE_KEY, "")
    full_cls = device.get(DEVICE_FULLCLS_KEY, "")

    from .device import VERSIONED_DEVICE_TYPES

    if device_type not in VERSIONED_DEVICE_TYPES:
        return ""

    # 从fullCls中提取版本信息
    for version in ["V1", "V2", "V3"]:
        if f"{device_type}_{version}" in full_cls:
            return version

    return ""


# ====================================================================
# 设备数据验证和清理 (Device Data Validation and Cleanup)
# ====================================================================
def validate_device_data(device: dict) -> bool:
    """
    验证设备数据的完整性。

    Args:
        device: 设备字典

    Returns:
        如果设备数据有效则返回True，否则返回False
    """
    if not isinstance(device, dict):
        return False

    # 检查必需的字段
    required_fields = [DEVICE_TYPE_KEY, "me", "agt"]
    for field in required_fields:
        if field not in device:
            _LOGGER.warning("Device missing required field: %s", field)
            return False

    # 检查设备数据字段
    device_data = device.get(DEVICE_DATA_KEY)
    if not isinstance(device_data, dict):
        _LOGGER.warning("Device data field is not a dictionary")
        return False

    return True


def clean_device_name(name: str) -> str:
    """
    清理设备名称，移除无效字符。

    Args:
        name: 原始设备名称

    Returns:
        清理后的设备名称
    """
    if not isinstance(name, str):
        return ""

    # 移除控制字符和多余的空格
    name = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", name)
    name = " ".join(name.split())

    # 统一标点符号
    name = name.replace("（", "(").replace("）", ")")

    return name.strip()


# ====================================================================
# 平台兼容性检查 (Platform Compatibility Checking)
# ====================================================================
def get_supported_platforms(device: dict) -> set[Platform]:
    """
    获取设备支持的所有平台。

    Args:
        device: 设备字典

    Returns:
        设备支持的平台集合
    """
    platform_mapping = get_device_platform_mapping(device)
    platforms = set()

    for platform_name in platform_mapping.keys():
        try:
            platform = Platform(platform_name)
            platforms.add(platform)
        except ValueError:
            _LOGGER.warning("Unknown platform: %s", platform_name)

    return platforms


def is_multi_platform_device(device: dict) -> bool:
    """
    检查设备是否为多平台设备。

    Args:
        device: 设备字典

    Returns:
        如果设备支持多个平台则返回True，否则返回False
    """
    platform_mapping = get_device_platform_mapping(device)
    return len(platform_mapping) > 1


# ====================================================================
# 设备状态检查 (Device Status Checking)
# ====================================================================
def is_device_online(device: dict) -> bool:
    """
    检查设备是否在线。

    Args:
        device: 设备字典

    Returns:
        如果设备在线则返回True，否则返回False
    """
    # 检查设备是否有最近的数据更新
    device_data = device.get(DEVICE_DATA_KEY, {})
    if not device_data:
        return False

    # 如果设备有任何IO口数据，认为是在线的
    return len(device_data) > 0


def has_io_data(device: dict, io_key: str) -> bool:
    """
    检查设备是否包含指定IO口的数据。

    Args:
        device: 设备字典
        io_key: IO口键名

    Returns:
        如果包含数据则返回True，否则返回False
    """
    device_data = device.get(DEVICE_DATA_KEY, {})
    return io_key in device_data and device_data[io_key] is not None


# ====================================================================
# 业务逻辑辅助函数 (Business Logic Helper Functions)
# ====================================================================
def should_create_entity(device: dict, platform: Platform, sub_key: str = None) -> bool:
    """
    判断是否应该为设备创建实体。

    Args:
        device: 设备字典
        platform: 平台类型
        sub_key: 子设备键名（可选）

    Returns:
        如果应该创建实体则返回True，否则返回False
    """
    # 验证设备数据
    if not validate_device_data(device):
        return False

    # 检查平台支持
    platform_mapping = get_device_platform_mapping(device)
    if platform.value not in platform_mapping:
        return False

    # 如果指定了子键，检查是否存在对应的IO数据
    if sub_key:
        return has_io_data(device, sub_key)

    return True


def get_entity_name(
    device: dict, sub_key: str = None, platform: Platform = None
) -> str:
    """
    生成实体的显示名称。

    Args:
        device: 设备字典
        sub_key: 子设备键名（可选）
        platform: 平台类型（可选）

    Returns:
        实体显示名称
    """
    base_name = clean_device_name(device.get("name", "Unknown Device"))

    # 如果有子键，添加到名称中
    if sub_key:
        base_name = f"{base_name} {sub_key}"

    # 如果是多平台设备，添加平台名称
    if platform and is_multi_platform_device(device):
        platform_name = platform.value.replace("_", " ").title()
        base_name = f"{base_name} ({platform_name})"

    return base_name
