"""
LifeSmart HVAC 和风扇映射配置
由 @MapleEve 初始创建和维护

包含所有HVAC模式和风扇速度的映射常量，用于不同类型的设备。
"""

# 导入HA常量以确保映射正确
try:
    from homeassistant.components.climate.const import (
        HVACMode,
        FAN_AUTO,
        FAN_HIGH,
        FAN_LOW,
        FAN_MEDIUM,
    )

    # 核心温控器HVAC模式映射
    LIFESMART_F_HVAC_MODE_MAP = {
        1: HVACMode.AUTO,
        2: HVACMode.FAN_ONLY,
        3: HVACMode.COOL,
        4: HVACMode.HEAT,
    }
    REVERSE_F_HVAC_MODE_MAP = {v: k for k, v in LIFESMART_F_HVAC_MODE_MAP.items()}

    # 扩展HVAC模式映射（包含地暖等特殊模式）
    LIFESMART_HVAC_MODE_MAP = {
        1: HVACMode.AUTO,
        2: HVACMode.FAN_ONLY,
        3: HVACMode.COOL,
        4: HVACMode.HEAT,
        5: HVACMode.DRY,
        7: HVACMode.HEAT,  # SL_NATURE/FCU 地暖模式
        8: HVACMode.HEAT_COOL,  # SL_NATURE/FCU 地暖+空调模式
    }
    REVERSE_LIFESMART_HVAC_MODE_MAP = {
        HVACMode.AUTO: 1,
        HVACMode.FAN_ONLY: 2,
        HVACMode.COOL: 3,
        HVACMode.HEAT: 4,  # 默认将制热映射回 4
        HVACMode.DRY: 5,
        HVACMode.HEAT_COOL: 8,
    }

    # 风机盘管模式映射
    LIFESMART_CP_AIR_HVAC_MODE_MAP = {
        0: HVACMode.COOL,
        1: HVACMode.HEAT,
        2: HVACMode.FAN_ONLY,
    }
    REVERSE_LIFESMART_CP_AIR_HVAC_MODE_MAP = {
        v: k for k, v in LIFESMART_CP_AIR_HVAC_MODE_MAP.items()
    }

    # 新风设备风速映射
    LIFESMART_ACIPM_FAN_MAP = {
        FAN_LOW: 1,
        FAN_MEDIUM: 2,
        FAN_HIGH: 3,
    }
    REVERSE_LIFESMART_ACIPM_FAN_MAP = {v: k for k, v in LIFESMART_ACIPM_FAN_MAP.items()}

    # 风机盘管风速映射
    LIFESMART_CP_AIR_FAN_MAP = {
        FAN_AUTO: 0,
        FAN_LOW: 1,
        FAN_MEDIUM: 2,
        FAN_HIGH: 3,
    }
    REVERSE_LIFESMART_CP_AIR_FAN_MAP = {
        v: k for k, v in LIFESMART_CP_AIR_FAN_MAP.items()
    }

    # 超能面板风速映射
    LIFESMART_TF_FAN_MAP = {
        FAN_AUTO: 101,
        FAN_LOW: 15,
        FAN_MEDIUM: 45,
        FAN_HIGH: 75,
    }
    REVERSE_LIFESMART_TF_FAN_MODE_MAP = {v: k for k, v in LIFESMART_TF_FAN_MAP.items()}

    # V_AIR_P风速映射
    LIFESMART_F_FAN_MAP = {
        FAN_LOW: 15,
        FAN_MEDIUM: 45,
        FAN_HIGH: 75,
    }
    REVERSE_LIFESMART_F_FAN_MODE_MAP = {v: k for k, v in LIFESMART_F_FAN_MAP.items()}

except ImportError:
    # Home Assistant不可用时的降级方案 - 使用空映射
    LIFESMART_F_HVAC_MODE_MAP = {}
    REVERSE_F_HVAC_MODE_MAP = {}
    LIFESMART_HVAC_MODE_MAP = {}
    REVERSE_LIFESMART_HVAC_MODE_MAP = {}
    LIFESMART_CP_AIR_HVAC_MODE_MAP = {}
    REVERSE_LIFESMART_CP_AIR_HVAC_MODE_MAP = {}
    LIFESMART_ACIPM_FAN_MAP = {}
    REVERSE_LIFESMART_ACIPM_FAN_MAP = {}
    LIFESMART_CP_AIR_FAN_MAP = {}
    REVERSE_LIFESMART_CP_AIR_FAN_MAP = {}
    LIFESMART_TF_FAN_MAP = {}
    REVERSE_LIFESMART_TF_FAN_MODE_MAP = {}
    LIFESMART_F_FAN_MAP = {}
    REVERSE_LIFESMART_F_FAN_MODE_MAP = {}

# 导出所有HVAC和风扇映射
__all__ = [
    "LIFESMART_F_HVAC_MODE_MAP",
    "REVERSE_F_HVAC_MODE_MAP",
    "LIFESMART_HVAC_MODE_MAP",
    "REVERSE_LIFESMART_HVAC_MODE_MAP",
    "LIFESMART_CP_AIR_HVAC_MODE_MAP",
    "REVERSE_LIFESMART_CP_AIR_HVAC_MODE_MAP",
    "LIFESMART_ACIPM_FAN_MAP",
    "REVERSE_LIFESMART_ACIPM_FAN_MAP",
    "LIFESMART_CP_AIR_FAN_MAP",
    "REVERSE_LIFESMART_CP_AIR_FAN_MAP",
    "LIFESMART_TF_FAN_MAP",
    "REVERSE_LIFESMART_TF_FAN_MODE_MAP",
    "LIFESMART_F_FAN_MAP",
    "REVERSE_LIFESMART_F_FAN_MODE_MAP",
]
