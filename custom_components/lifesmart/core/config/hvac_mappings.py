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

    # ================= 核心温控器HVAC模式映射 =================
    # 核心温控器HVAC模式映射 - 对应基础的F系列设备
    # 数值含义：1=自动模式，2=仅送风，3=制冷，4=制热
    LIFESMART_F_HVAC_MODE_MAP = {
        1: HVACMode.AUTO,  # 自动模式 - 系统自动选择制冷或制热
        2: HVACMode.FAN_ONLY,  # 仅送风模式 - 只有风扇工作，不制冷制热
        3: HVACMode.COOL,  # 制冷模式 - 空调制冷运行
        4: HVACMode.HEAT,  # 制热模式 - 空调制热运行
    }
    # 反向映射：从Home Assistant模式到LifeSmart数值
    REVERSE_F_HVAC_MODE_MAP = {v: k for k, v in LIFESMART_F_HVAC_MODE_MAP.items()}

    # ================= 扩展HVAC模式映射 =================
    # 扩展HVAC模式映射 - 支持更多设备类型和特殊模式
    # 包含地暖、除湿等高级功能，适用于SL_NATURE、FCU等设备
    LIFESMART_HVAC_MODE_MAP = {
        1: HVACMode.AUTO,  # 自动模式 - 智能调节温度
        2: HVACMode.FAN_ONLY,  # 仅送风模式 - 循环空气但不调温
        3: HVACMode.COOL,  # 制冷模式 - 降低室内温度
        4: HVACMode.HEAT,  # 制热模式 - 提高室内温度
        5: HVACMode.DRY,  # 除湿模式 - 降低室内湿度
        7: HVACMode.HEAT,  # SL_NATURE/FCU地暖模式 - 地板辐射采暖
        8: HVACMode.HEAT_COOL,  # SL_NATURE/FCU地暖+空调复合模式 - 同时支持制热制冷
    }
    # 反向映射：Home Assistant到LifeSmart模式转换
    # 注意：制热模式默认映射到标准制热(4)而非地暖(7)
    REVERSE_LIFESMART_HVAC_MODE_MAP = {
        HVACMode.AUTO: 1,  # 自动模式
        HVACMode.FAN_ONLY: 2,  # 仅送风
        HVACMode.COOL: 3,  # 制冷
        HVACMode.HEAT: 4,  # 制热(标准模式)
        HVACMode.DRY: 5,  # 除湿
        HVACMode.HEAT_COOL: 8,  # 制热制冷复合模式
    }

    # ================= 风机盘管模式映射 =================
    # 风机盘管(Fan Coil Unit)模式映射 - CP_AIR系列设备专用
    # 数值含义：0=制冷，1=制热，2=仅送风
    LIFESMART_CP_AIR_HVAC_MODE_MAP = {
        0: HVACMode.COOL,  # 制冷模式 - 冷水循环制冷
        1: HVACMode.HEAT,  # 制热模式 - 热水循环制热
        2: HVACMode.FAN_ONLY,  # 仅送风模式 - 风机运行但不调温
    }
    # 反向映射：Home Assistant到风机盘管模式
    REVERSE_LIFESMART_CP_AIR_HVAC_MODE_MAP = {
        v: k for k, v in LIFESMART_CP_AIR_HVAC_MODE_MAP.items()
    }

    # ================= 风速映射配置 =================

    # 新风设备风速映射 - ACIPM系列新风机专用
    # 数值含义：1=低速，2=中速，3=高速
    LIFESMART_ACIPM_FAN_MAP = {
        FAN_LOW: 1,  # 低速档 - 静音运行，适合夜间
        FAN_MEDIUM: 2,  # 中速档 - 日常通风，平衡噪音和效果
        FAN_HIGH: 3,  # 高速档 - 快速换气，适合人员密集时
    }
    # 反向映射：LifeSmart风速值到Home Assistant风扇模式
    REVERSE_LIFESMART_ACIPM_FAN_MAP = {v: k for k, v in LIFESMART_ACIPM_FAN_MAP.items()}

    # 风机盘管风速映射 - CP_AIR系列设备专用
    # 数值含义：0=自动，1=低速，2=中速，3=高速
    LIFESMART_CP_AIR_FAN_MAP = {
        FAN_AUTO: 0,  # 自动风速 - 系统根据温差自动调节
        FAN_LOW: 1,  # 低速档 - 节能静音模式
        FAN_MEDIUM: 2,  # 中速档 - 标准舒适模式
        FAN_HIGH: 3,  # 高速档 - 快速调温模式
    }
    # 反向映射：LifeSmart风速值到Home Assistant风扇模式
    REVERSE_LIFESMART_CP_AIR_FAN_MAP = {
        v: k for k, v in LIFESMART_CP_AIR_FAN_MAP.items()
    }

    # 超能面板风速映射 - SL_NATURE系列超能面板专用
    # 数值含义：101=自动，15=低速，45=中速，75=高速
    # 注意：使用百分比数值表示风速级别
    LIFESMART_TF_FAN_MAP = {
        FAN_AUTO: 101,  # 自动模式 - 智能风速调节(数值101为特殊标识)
        FAN_LOW: 15,  # 低速档 - 15%风速，静音节能
        FAN_MEDIUM: 45,  # 中速档 - 45%风速，日常使用
        FAN_HIGH: 75,  # 高速档 - 75%风速，快速换气
    }
    # 反向映射：LifeSmart风速百分比到Home Assistant风扇模式
    REVERSE_LIFESMART_TF_FAN_MODE_MAP = {v: k for k, v in LIFESMART_TF_FAN_MAP.items()}

    # V_AIR_P风速映射 - V_AIR_P系列空气处理设备专用
    # 数值含义：15=低速，45=中速，75=高速(百分比风速)
    # 注意：该系列不支持自动模式，仅支持手动三档调节
    LIFESMART_F_FAN_MAP = {
        FAN_LOW: 15,  # 低速档 - 15%风速，夜间模式
        FAN_MEDIUM: 45,  # 中速档 - 45%风速，标准模式
        FAN_HIGH: 75,  # 高速档 - 75%风速，强力模式
    }
    # 反向映射：LifeSmart风速百分比到Home Assistant风扇模式
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
