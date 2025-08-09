"""
门锁事件配置 - 配置层专用
由 @MapleEve 初始创建和维护

此文件包含门锁EVTLO字段的配置定义。
只实现真正有用户价值的功能，避免过度拆分。
"""

from typing import Dict, Any, Optional

from homeassistant.components.binary_sensor import BinarySensorDeviceClass

# 开锁方式映射
UNLOCK_METHODS: Dict[int, str] = {
    0: "未定义",
    1: "密码",
    2: "指纹",
    3: "NFC",
    4: "机械钥匙",
    5: "远程开锁",
    7: "APP开启",
    8: "蓝牙开锁",
    9: "手动开锁",
    15: "出错",
}

# 有价值的EVTLO数据提取配置
EVTLO_DATA_CONFIG: Dict[str, Dict[str, Any]] = {
    "lock_status": {
        "name": "门锁状态",
        "description": "门锁开关状态",
        "extraction_logic": "type_bit_0",
        "platform": "lock",
        "friendly_name": "门锁",
    },
    "user_id": {
        "name": "用户编号",
        "description": "开锁用户编号",
        "extraction_logic": "bit_range",
        "extraction_params": {"start_bit": 0, "end_bit": 11},
        "platform": "sensor",
        "friendly_name": "用户编号",
    },
    "unlock_method": {
        "name": "开锁方式",
        "description": "开锁方式",
        "extraction_logic": "bit_range_mapped",
        "extraction_params": {
            "start_bit": 12,
            "end_bit": 15,
            "mapping": UNLOCK_METHODS,
        },
        "platform": "sensor",
        "friendly_name": "开锁方式",
    },
    "dual_unlock": {
        "name": "双开模式",
        "description": "是否为双开模式",
        "extraction_logic": "dual_unlock_detection",
        "platform": "binary_sensor",
        "device_class": BinarySensorDeviceClass.LOCK,
        "friendly_name": "双开模式",
    },
}


def get_evtlo_config(data_key: str) -> Optional[Dict[str, Any]]:
    """获取指定EVTLO数据的配置

    Args:
        data_key: 数据键名

    Returns:
        数据配置字典或None
    """
    return EVTLO_DATA_CONFIG.get(data_key)


def get_all_evtlo_configs() -> Dict[str, Dict[str, Any]]:
    """获取所有EVTLO配置"""
    return EVTLO_DATA_CONFIG.copy()


def get_unlock_method_name(method_code: int) -> str:
    """获取开锁方式名称

    Args:
        method_code: 开锁方式代码

    Returns:
        开锁方式名称
    """
    return UNLOCK_METHODS.get(method_code, f"未知({method_code})")
