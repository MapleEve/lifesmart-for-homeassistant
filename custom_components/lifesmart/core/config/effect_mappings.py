"""
LifeSmart 动态效果映射配置
由 @MapleEve 初始创建和维护

包含所有灯光设备的动态效果映射常量。
"""

# 动态效果映射
DYN_EFFECT_MAP = {
    "青草": 0x8218CC80,
    "海浪": 0x8318CC80,
    "深蓝山脈": 0x8418CC80,
    "紫色妖姬": 0x8518CC80,
    "树莓": 0x8618CC80,
    "橙光": 0x8718CC80,
    "秋实": 0x8818CC80,
    "冰淇淋": 0x8918CC80,
    "高原": 0x8020CC80,
    "披萨": 0x8120CC80,
    "果汁": 0x8A20CC80,
    "温暖小屋": 0x8B30CC80,
    "魔力红": 0x9318CC80,
    "光斑": 0x9518CC80,
    "蓝粉知己": 0x9718CC80,
    "晨曦": 0x9618CC80,
    "木槿": 0x9818CC80,
    "缤纷时代": 0x9918CC80,
    "天上人间": 0xA318CC80,
    "魅蓝": 0xA718CC80,
    "炫红": 0xA918CC80,
}

# 量子灯特殊动态效果
QUANTUM_EFFECT_MAP = {
    "马戏团": 0x04810130,
    "北极光": 0x04C40600,
    "黑凤梨": 0x03BC0190,
    "十里桃花": 0x04940800,
    "彩虹糖": 0x05BD0690,
    "云起": 0x04970400,
    "日出印象": 0x01C10A00,
    "马卡龙": 0x049A0E00,
    "光盘时代": 0x049A0000,
    "动感光波": 0x0213A400,
    "圣诞节": 0x068B0900,
    "听音变色": 0x07BD0990,  # 第二代量子灯才支持
}

# 衍生映射
DYN_EFFECT_LIST = list(DYN_EFFECT_MAP.keys())
ALL_EFFECT_MAP = {**DYN_EFFECT_MAP, **QUANTUM_EFFECT_MAP}
ALL_EFFECT_LIST = list(ALL_EFFECT_MAP.keys())

# 导出所有效果映射
__all__ = [
    "DYN_EFFECT_MAP",
    "QUANTUM_EFFECT_MAP",
    "DYN_EFFECT_LIST",
    "ALL_EFFECT_MAP",
    "ALL_EFFECT_LIST",
]
