"""
ALM位掩码配置 - 配置层专用
由 @MapleEve 初始创建和维护

此文件包含门锁ALM字段的位掩码定义配置。
将配置从数据处理器中分离出来，实现配置驱动的架构。
"""

from typing import Any, Optional

from homeassistant.components.binary_sensor import BinarySensorDeviceClass

# ALM字段位掩码定义配置
ALM_BIT_CONFIG: dict[int, dict[str, Any]] = {
    0: {
        "name": "error_alarm",
        "description": "错误报警",
        "detail": "输入错误密码或指纹或卡片超过10次就报警",
        "device_class": BinarySensorDeviceClass.PROBLEM,
        "friendly_name": "错误报警",
    },
    1: {
        "name": "hijack_alarm",
        "description": "劫持报警",
        "detail": "输入防劫持密码或防劫持指纹开锁就报警",
        "device_class": BinarySensorDeviceClass.SAFETY,
        "friendly_name": "劫持报警",
    },
    2: {
        "name": "tamper_alarm",
        "description": "防撬报警",
        "detail": "锁被撬开",
        "device_class": BinarySensorDeviceClass.TAMPER,
        "friendly_name": "防撬报警",
    },
    3: {
        "name": "key_alarm",
        "description": "机械钥匙报警",
        "detail": "使用机械钥匙开锁",
        "device_class": BinarySensorDeviceClass.LOCK,
        "friendly_name": "机械钥匙报警",
    },
    4: {
        "name": "low_battery",
        "description": "低电压报警",
        "detail": "电池电量不足",
        "device_class": BinarySensorDeviceClass.BATTERY,
        "friendly_name": "低电量报警",
    },
    5: {
        "name": "motion_alarm",
        "description": "异动告警",
        "detail": "异动告警",
        "device_class": BinarySensorDeviceClass.MOTION,
        "friendly_name": "异动告警",
    },
    6: {
        "name": "doorbell",
        "description": "门铃",
        "detail": "门铃",
        "device_class": BinarySensorDeviceClass.SOUND,
        "friendly_name": "门铃",
    },
    7: {
        "name": "fire_alarm",
        "description": "火警",
        "detail": "火警",
        "device_class": BinarySensorDeviceClass.SMOKE,
        "friendly_name": "火警",
    },
    8: {
        "name": "intrusion_alarm",
        "description": "入侵告警",
        "detail": "入侵告警",
        "device_class": BinarySensorDeviceClass.SAFETY,
        "friendly_name": "入侵告警",
    },
    11: {
        "name": "factory_reset",
        "description": "恢复出厂告警",
        "detail": "恢复出厂告警",
        "device_class": BinarySensorDeviceClass.PROBLEM,
        "friendly_name": "恢复出厂告警",
    },
}


def get_alm_bit_config(bit_position: int) -> Optional[dict[str, Any]]:
    """获取指定位的配置

    Args:
        bit_position: 位位置(0-31)

    Returns:
        位配置字典或None
    """
    return ALM_BIT_CONFIG.get(bit_position)


def get_all_alm_bits() -> dict[int, dict[str, Any]]:
    """获取所有ALM位配置"""
    return ALM_BIT_CONFIG.copy()


def is_valid_alm_bit(bit_position: int) -> bool:
    """检查是否为有效的ALM位"""
    return bit_position in ALM_BIT_CONFIG
