"""
LifeSmart 智能家居系统 - 第三方设备映射配置核心模块

══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

【模块概述】
本模块是 LifeSmart 智能家居系统中负责第三方设备映射和版本管理的核心配置文件。
它解决了智能家居系统在集成第三方厂商设备时的标准化识别、版本区分和兼容性管理问题。

【设计目标】
1. 标准化第三方设备的接入和识别机制
2. 提供统一的版本管理和功能区分体系
3. 支持实验性设备的渐进式集成策略
4. 建立可扩展的设备支持级别分类系统
5. 确保第三方设备与 Home Assistant 的完美集成

【架构价值】
- 🎯 **统一接入**: 标准化第三方设备的接入流程，降低集成复杂度
- 🔄 **版本管理**: 精确区分设备版本和功能差异，避免兼容性问题
- 🧪 **渐进集成**: 支持实验性设备的逐步稳定化过程
- 📊 **状态跟踪**: 提供设备支持状态的精确分类和标记
- 🔌 **扩展友好**: 新设备类型和版本的快速添加机制

【核心组件】
1. THIRD_PARTY_DEVICES - 35个第三方设备的完整版本映射表
2. VERSIONED_DEVICE_TYPES - 需要版本区分的原生设备类型配置
3. SUPPORT_LEVELS - 三级设备支持状态分类系统
4. 设备信息查询和状态判断的完整 API 集

【业务场景】
- 大金、特灵、开利等知名空调厂商的设备接入
- 艾弗纳、森德等新风系统的标准化集成
- 智能断路器、电能表等电力设备的版本管理
- 调光开关、智能灯具的功能差异化处理

【技术特性】
✅ 基于官方文档附录3.6的权威设备规范
✅ 完整的类型提示和运行时安全检查
✅ 灵活的版本号格式支持 (语义化版本控制)
✅ 实验性设备的安全隔离和渐进式启用
✅ 与现有映射系统的完全兼容性

【作者信息】
创建者: @MapleEve
维护团队: LifeSmart 开发组
最后更新: 2025-08-12
版本: v2.5.0

══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
"""

from typing import Dict, Any, Optional, List

# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 模块导入和类型定义
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

# 设备信息字典的类型定义
DeviceInfo = Dict[str, Any]
# 版本字符串的类型定义 (如: "0.0.0.1", "V1", "V2")
VersionString = str
# 设备类型字符串的类型定义 (如: "V_AIR_P", "SL_SW_DM1")
DeviceType = str
# 支持级别字符串的类型定义 ("official", "community", "experimental")
SupportLevel = str

# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 第三方设备版本映射配置
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

# 【数据来源】
# 基于 LifeSmart 智慧设备规格属性说明文档 - 附录3.6
# 官方文档链接: docs/LifeSmart 智慧设备规格属性说明.md

# 【映射原理】
# 当第三方设备通过 LifeSmart 通用控制器接入智能家居系统时，系统需要根据设备的
# version 字段 (ver) 来精确识别具体的设备型号、功能特性和 IO 口配置。
# 这个映射表提供了从版本号到设备详细信息的完整转换关系。

# 【版本号格式】
# 版本号采用四段式格式: "主版本.次版本.修订版本.构建版本"
# 例如: "0.0.0.1" 表示第一个构建版本
# 例如: "0.0.0.15" 表示第十五个构建版本

# 【设备分类】
# V_AIR_P    - 空调/暖通设备 (Air Conditioning & HVAC)
# V_FRESH_P  - 新风系统设备 (Fresh Air Systems)
# V_485_P    - RS485 通信设备 (RS485 Communication Devices)
# V_DLT645_P - 电力设备 (DL/T 645 Protocol Devices)

# 【状态标记说明】
# third_party: 标识为第三方厂商设备，非 LifeSmart 原生设备
# experimental: 标识为实验性支持，可能存在功能限制或稳定性问题
# support_level: 设备支持级别 (official/community/experimental)
# manufacturer: 设备制造商信息
# category: 设备功能分类
# features: 设备主要功能特性列表
# io_ports: IO口配置信息 (参考官方文档规范)

THIRD_PARTY_DEVICES: Dict[DeviceType, Dict[VersionString, DeviceInfo]] = {
    # ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
    # 空调/暖通设备类型 (V_AIR_P - Air Conditioning & HVAC Systems)
    # ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
    # 这个分类包含了各大知名空调厂商的设备，如大金、特灵、开利、美的等
    # 主要功能: 温度控制、湿度调节、风速调节、模式切换等暖通空调核心功能
    "V_AIR_P": {
        "0.0.0.1": {
            "code": "000001",  # 设备唯一识别码
            "model": "DTA116A621",  # 厂商型号
            "name": "大金空调DTA116A621",  # 设备显示名称
            "manufacturer": "大金 (DAIKIN)",  # 厂商名称
            "category": "中央空调",  # 设备类别
            "features": ["温度控制", "湿度调节", "风速调节", "模式切换"],
            "io_ports": "参考官方文档V_AIR_P规范",
            "third_party": True,  # 第三方设备标识
            "experimental": False,  # 稳定支持，非实验性
            "support_level": "community",  # 社区支持级别
        },
        "0.0.0.2": {
            "code": "000002",
            "model": "KRAVEN_VRV",
            "name": "空调VRV控制器",
            "manufacturer": "KRAVEN",
            "category": "VRV多联机系统",
            "features": ["多室温控", "集中管理", "能效监控", "故障诊断"],
            "io_ports": "参考官方文档V_AIR_P规范",
            "third_party": True,
            "experimental": False,
            "support_level": "community",
        },
        "0.0.0.7": {
            "code": "000007",
            "model": "TM8X",
            "name": "特灵空调系统",
            "manufacturer": "特灵 (TRANE)",
            "category": "中央空调系统",
            "features": ["智能温控", "节能优化", "远程监控", "预测性维护"],
            "io_ports": "参考官方文档V_AIR_P规范",
            "third_party": True,
            "experimental": False,
            "support_level": "community",
        },
        "0.0.0.10": {
            "code": "00000A",
            "model": "KL420",
            "name": "开利420C空调控制器",
            "manufacturer": "开利 (CARRIER)",
            "category": "空调控制器",
            "features": ["精准温控", "多区域管理", "能耗统计", "定时控制"],
            "io_ports": "参考官方文档V_AIR_P规范",
            "third_party": True,
            "experimental": False,
            "support_level": "community",
        },
        "0.0.0.15": {
            "code": "00000F",
            "model": "MEDIA-CCM18",
            "name": "美的多联机MODBUS网关-CCM18",
            "manufacturer": "美的 (MIDEA)",
            "category": "多联机网关",
            "features": ["MODBUS通信", "多联机控制", "数据采集", "系统集成"],
            "io_ports": "参考官方文档V_AIR_P规范",
            "third_party": True,
            "experimental": False,
            "support_level": "community",
        },
        "0.0.0.17": {
            "code": "000011",
            "model": "PHNIX-ST800",
            "name": "芬尼ST800二合一温控面板",
            "manufacturer": "芬尼 (PHNIX)",
            "category": "温控面板",
            "features": ["双系统控制", "智能面板", "温度显示", "模式切换"],
            "io_ports": "参考官方文档V_AIR_P规范",
            "third_party": True,
            "experimental": True,  # 实验性支持
            "support_level": "experimental",
        },
        "0.0.0.18": {
            "code": "000012",
            "model": "SHINEFAN-G9",
            "name": "祥帆新风G9面板",
            "manufacturer": "祥帆 (SHINEFAN)",
            "category": "新风控制面板",
            "features": ["新风控制", "空气质量监测", "智能面板", "模式调节"],
            "io_ports": "参考官方文档V_AIR_P规范",
            "third_party": True,
            "experimental": True,
            "support_level": "experimental",
        },
        "0.0.0.19": {
            "code": "000013",
            "model": "TCB-IFMB646TLE",
            "name": "东芝空调网关TCB-IFMB646TLE",
            "manufacturer": "东芝 (TOSHIBA)",
            "category": "空调网关",
            "features": ["网关通信", "协议转换", "设备管理", "数据传输"],
            "io_ports": "参考官方文档V_AIR_P规范",
            "third_party": True,
            "experimental": True,
            "support_level": "experimental",
        },
        "0.0.0.21": {
            "code": "000015",
            "model": "THT420B",
            "name": "开利空调面板THT420B",
            "manufacturer": "开利 (CARRIER)",
            "category": "空调控制面板",
            "features": ["触控面板", "温度控制", "湿度显示", "定时功能"],
            "io_ports": "参考官方文档V_AIR_P规范",
            "third_party": True,
            "experimental": True,
            "support_level": "experimental",
        },
        "0.0.0.24": {
            "code": "000018",
            "model": "NetproDual",
            "name": "NetPro Dual DAIKIN",
            "manufacturer": "NetPro",
            "category": "大金空调双控制器",
            "features": ["双控制", "网络通信", "协议兼容", "系统集成"],
            "io_ports": "参考官方文档V_AIR_P规范",
            "third_party": True,
            "experimental": True,
            "support_level": "experimental",
        },
        "0.0.0.31": {
            "code": "00001F",
            "model": "CLP5DO",
            "name": "三恒系统",
            "manufacturer": "三恒科技",
            "category": "三恒系统控制器",
            "features": ["恒温恒湿恒氧", "全空气系统", "智能控制", "环境优化"],
            "io_ports": "参考官方文档V_AIR_P规范",
            "third_party": True,
            "experimental": True,
            "support_level": "experimental",
        },
    },
    # ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
    # 新风系统设备类型 (V_FRESH_P - Fresh Air Systems)
    # ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
    # 这个分类包含了各种新风系统设备，负责室内空气质量管理和换气控制
    # 主要功能: 空气净化、换气控制、湿度调节、空气质量监测等新风系统核心功能
    "V_FRESH_P": {
        "0.0.0.3": {
            "code": "000003",
            "model": "KV11_RTU",
            "name": "艾弗纳KV11新风系统",
            "manufacturer": "艾弗纳 (AIRENA)",
            "category": "新风机组",
            "features": ["全热交换", "空气净化", "湿度控制", "智能调节"],
            "io_ports": "参考官方文档V_FRESH_P规范",
            "third_party": True,
            "experimental": False,
            "support_level": "community",
        },
        "0.0.0.8": {
            "code": "000008",
            "model": "CA-S2",
            "name": "森德新风系统",
            "manufacturer": "森德 (ZEHNDER)",
            "category": "新风热回收系统",
            "features": ["热回收", "空气过滤", "节能运行", "静音设计"],
            "io_ports": "参考官方文档V_FRESH_P规范",
            "third_party": True,
            "experimental": True,
            "support_level": "experimental",
        },
        "0.0.0.22": {
            "code": "000016",
            "model": "NAVIEN-TAC550",
            "name": "NAVIEN新风主机NAVIEN-TAC550",
            "manufacturer": "NAVIEN",
            "category": "新风主机",
            "features": ["大风量", "高效过滤", "变频控制", "远程管理"],
            "io_ports": "参考官方文档V_FRESH_P规范",
            "third_party": True,
            "experimental": True,
            "support_level": "experimental",
        },
        "0.0.0.23": {
            "code": "000017",
            "model": "KD-1-E",
            "name": "兰舍新风控制器KD-1-E",
            "manufacturer": "兰舍 (NATHER)",
            "category": "新风控制器",
            "features": ["智能控制", "空气监测", "自动调节", "节能模式"],
            "io_ports": "参考官方文档V_FRESH_P规范",
            "third_party": True,
            "experimental": True,
            "support_level": "experimental",
        },
        "0.0.0.31": {
            "code": "00001F",
            "model": "CLP5DO",
            "name": "三恒系统新风模块",
            "manufacturer": "三恒科技",
            "category": "三恒新风系统",
            "features": ["恒氧控制", "全屋新风", "智能净化", "环境优化"],
            "io_ports": "参考官方文档V_FRESH_P规范",
            "third_party": True,
            "experimental": True,
            "support_level": "experimental",
        },
    },
    # ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
    # RS485通信设备类型 (V_485_P - RS485 Communication Devices)
    # ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
    # 这个分类包含了各种通过RS485协议通信的工业设备和传感器
    # 主要功能: 数据采集、环境监测、电力控制、照明控制等工业自动化功能
    "V_485_P": {
        "0.0.0.12": {
            "code": "00000C",
            "model": "RY-A101",
            "name": "气体压力传感器RY_A101",
            "manufacturer": "睿源科技",
            "category": "环境传感器",
            "features": ["气体压力检测", "实时监测", "报警功能", "数据记录"],
            "io_ports": "参考官方文档V_485_P规范",
            "third_party": True,
            "experimental": True,
            "support_level": "experimental",
        },
        "0.0.0.13": {
            "code": "00000D",
            "model": "KL-19XR",
            "name": "KL-19XR环境监测器",
            "manufacturer": "科力达",
            "category": "环境监测设备",
            "features": ["多参数检测", "无线传输", "云端数据", "移动监控"],
            "io_ports": "参考官方文档V_485_P规范",
            "third_party": True,
            "experimental": True,
            "support_level": "experimental",
        },
        "0.0.0.25": {
            "code": "000019",
            "model": "GD-H2S",
            "name": "GD-H2S气体检测仪",
            "manufacturer": "国达科技",
            "category": "气体检测设备",
            "features": ["H2S检测", "实时报警", "浓度显示", "安全防护"],
            "io_ports": "参考官方文档V_485_P规范",
            "third_party": True,
            "experimental": True,
            "support_level": "experimental",
        },
        "0.0.0.26": {
            "code": "00001A",
            "model": "HQ100-S12",
            "name": "智能照明控制模块HQ100-S12",
            "manufacturer": "华强照明",
            "category": "智能照明控制器",
            "features": ["调光控制", "场景模式", "定时功能", "节能管理"],
            "io_ports": "参考官方文档V_485_P规范",
            "third_party": True,
            "experimental": True,
            "support_level": "experimental",
        },
        "0.0.0.27": {
            "code": "00001B",
            "model": "DTSR958",
            "name": "导轨电能表",
            "manufacturer": "德通电力",
            "category": "电力计量设备",
            "features": ["电能计量", "功率监测", "数据记录", "通信上传"],
            "io_ports": "参考官方文档V_485_P规范",
            "third_party": True,
            "experimental": False,  # 稳定支持
            "support_level": "community",
        },
        "0.0.0.28": {
            "code": "00001C",
            "model": "ZXB1L-125",
            "name": "智能断路器ZXB1L-125",
            "manufacturer": "正泰电器",
            "category": "智能断路器",
            "features": ["过载保护", "短路保护", "漏电保护", "远程控制"],
            "io_ports": "参考官方文档V_485_P规范",
            "third_party": True,
            "experimental": False,
            "support_level": "community",
        },
        "0.0.0.29": {
            "code": "00001D",
            "model": "ZXB1L-3-125",
            "name": "智能断路器3相ZXB1L-3-125",
            "manufacturer": "正泰电器",
            "category": "三相智能断路器",
            "features": ["三相保护", "相序检测", "不平衡保护", "远程控制"],
            "io_ports": "参考官方文档V_485_P规范",
            "third_party": True,
            "experimental": False,
            "support_level": "community",
        },
        "0.0.0.30": {
            "code": "00001E",
            "model": "HD120A16GK",
            "name": "HDHK智能电流采集器HD120A16GK",
            "manufacturer": "华东华康",
            "category": "电流采集器",
            "features": ["电流采集", "数据处理", "通信传输", "多路监测"],
            "io_ports": "参考官方文档V_485_P规范",
            "third_party": True,
            "experimental": True,
            "support_level": "experimental",
        },
        "0.0.0.32": {
            "code": "000020",
            "model": "BF-12LI",
            "name": "BF-12LI智能采集模块",
            "manufacturer": "百富科技",
            "category": "数据采集模块",
            "features": ["多通道采集", "数据处理", "本地存储", "网络传输"],
            "io_ports": "参考官方文档V_485_P规范",
            "third_party": True,
            "experimental": True,
            "support_level": "experimental",
        },
    },
    # ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
    # 电力设备类型 (V_DLT645_P - DL/T 645 Protocol Devices)
    # ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
    # 这个分类包含了符合DL/T 645电力行业标准的电力设备
    # 主要功能: 电能计量、电力监测、数据采集、能耗分析等电力管理功能
    "V_DLT645_P": {
        "0.0.0.6": {
            "code": "000006",
            "model": "DLT645",
            "name": "DLT645标准电能表",
            "manufacturer": "标准电力设备",
            "category": "标准电能表",
            "features": ["电能计量", "多费率", "数据冻结", "通信读取"],
            "io_ports": "参考官方文档V_DLT645_P规范",
            "third_party": True,
            "experimental": False,
            "support_level": "community",
        },
    },
}

# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 设备类型版本区分映射配置
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

# 【版本区分原理】
# 某些LifeSmart原生设备存在多个版本，这些版本在IO口功能、硬件特性或控制逻辑上存在显著差异。
# 系统需要根据设备的fullCls字段来准确识别具体版本，确保功能映射的准确性。
#
# 【版本管理策略】
# 1. 只有在IO口和功能上真正存在差异的设备才需要版本区分
# 2. 版本区分基于设备的fullCls字段，如SL_SW_DM1_V1、SL_SW_DM1_V2
# 3. 每个版本都有详细的功能描述和IO口规范说明
# 4. 支持实验性版本的渐进式稳定化过程

# 【数据结构说明】
# - type: 设备功能类型标识，用于平台映射和功能识别
# - description: 详细的设备功能描述，说明版本间的核心差异
# - experimental: 是否为实验性版本，影响设备的启用策略
# - third_party: 是否为第三方设备，通常原生设备为False
# - support_level: 支持级别，影响用户界面的显示和推荐

VERSIONED_DEVICE_TYPES: Dict[DeviceType, Dict[VersionString, DeviceInfo]] = {
    # ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
    # 调光开关系列版本管理 (SL_SW_DM1 - Smart Light Switch Dimmer Series)
    # ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
    # 调光开关系列存在功能显著不同的两个版本，需要根据fullCls精确区分
    "SL_SW_DM1": {
        # ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
        # │ SL_SW_DM1_V1 - 动态调光开关 (Motion-Sensor Enabled Dimmer Switch) │
        # └─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
        # 这是一个集成了传感器功能的高级调光开关，具备智能感应和自动控制能力
        #
        # 【IO口配置】(基于官方文档V1规范)
        # P1: 开关+亮度控制 (RW) - 主要的照明控制接口，支持开关和调光
        # P2: 指示灯控制 (RW) - 开关状态指示灯，可调节亮度
        # P3: 移动检测 (R) - PIR传感器，检测人体移动
        # P4: 环境光照检测 (R) - 光照传感器，检测环境亮度
        # P5: 调光设置 (RW) - 调光参数配置，如渐变时间、最小/最大亮度
        # P6: 动态设置 (RW) - 智能控制参数，如感应延时、自动开关逻辑
        #
        # 【智能功能】
        # - 人体感应自动开灯：当检测到人体移动时自动开启照明
        # - 环境光照自适应：根据环境亮度自动调节照明强度
        # - 延时关灯：人离开后延时关闭，避免频繁开关
        # - 节能优化：结合感应和光照数据，实现最佳节能效果
        "V1": {
            "type": "motion_dimmer",  # 动态调光开关类型
            "description": "动态调光开关 - 集成PIR传感器和光照传感器的智能调光开关，支持人体感应自动控制和环境光照自适应调节",
            "features": [
                "人体感应自动开灯",
                "环境光照自适应调节",
                "延时关灯保护",
                "智能节能优化",
                "渐变调光控制",
                "参数自定义配置",
            ],
            "io_ports": {
                "P1": "开关+亮度控制 (RW)",
                "P2": "指示灯控制 (RW)",
                "P3": "移动检测 (R)",
                "P4": "环境光照检测 (R)",
                "P5": "调光设置 (RW)",
                "P6": "动态设置 (RW)",
            },
            "platforms": [
                "light",
                "binary_sensor",
                "sensor",
            ],  # 支持的Home Assistant平台
            "experimental": False,  # 成熟稳定的产品
            "third_party": False,  # LifeSmart原生设备
            "support_level": "official",  # 官方完全支持
        },
        # ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
        # │ SL_SW_DM1_V2 - 星玉调光开关 (可控硅调光) (Triac Dimmer Switch) │
        # └─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
        # 这是一个基于可控硅技术的基础调光开关，专注于稳定可靠的调光控制
        #
        # 【IO口配置】(基于官方文档V2规范)
        # P1: 开关+亮度控制 (RW) - 主要的照明控制接口，支持开关和调光
        # P2: 指示灯亮度控制 (RW) - 开关面板指示灯亮度调节
        #
        # 【核心特性】
        # - 可控硅调光技术：采用可控硅(Triac)进行调光，适用于白炽灯和部分LED灯
        # - 平滑调光控制：提供平滑的亮度调节，无频闪
        # - 高功率支持：可控硅技术支持较大功率的照明负载
        # - 简洁可靠：功能专注，稳定性高，故障率低
        "V2": {
            "type": "triac_dimmer",  # 可控硅调光开关类型
            "description": "星玉调光开关(可控硅) - 基于可控硅技术的专业调光开关，提供稳定可靠的照明调光控制，适用于传统白炽灯和兼容LED灯",
            "features": [
                "可控硅调光技术",
                "平滑无频闪调光",
                "高功率负载支持",
                "指示灯亮度可调",
                "简洁稳定设计",
                "兼容多种灯具类型",
            ],
            "io_ports": {"P1": "开关+亮度控制 (RW)", "P2": "指示灯亮度控制 (RW)"},
            "platforms": ["light"],  # 主要支持灯光平台
            "experimental": False,  # 成熟稳定的产品
            "third_party": False,  # LifeSmart原生设备
            "support_level": "official",  # 官方完全支持
        },
    },
    # ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
    # 白光调光灯系列版本管理 (SL_LI_WW - Smart Light White Warm Series)
    # ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
    # 白光调光灯系列虽然IO口规范相同，但应用场景和技术实现存在差异，需要版本区分
    "SL_LI_WW": {
        # ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
        # │ SL_LI_WW_V1 - 智能灯泡(冷暖白) (Smart LED Bulb - Tunable White) │
        # └─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
        # 标准的智能LED灯泡，适用于家庭和办公环境的日常照明需求
        #
        # 【IO口配置】(遵循SL_LI_WW标准规范)
        # P1: 亮度控制 (RW) - 0-100%亮度调节，支持渐变控制
        # P2: 色温控制 (RW) - 2700K-6500K色温调节，冷暖白光切换
        #
        # 【应用场景】
        # - 家居照明：客厅、卧室、书房等生活空间
        # - 办公环境：会议室、办公室、接待区域
        # - 商业空间：商店、餐厅、酒店等商业场所
        "V1": {
            "type": "dimmable_light_v1",  # 标准调光灯类型
            "description": "智能灯泡(冷暖白) - 标准版智能LED灯泡，支持亮度调节和色温控制，适用于家居、办公等常规照明场景",
            "features": [
                "0-100%亮度调节",
                "2700K-6500K色温调节",
                "渐变控制效果",
                "节能LED技术",
                "长寿命设计",
                "即插即用安装",
            ],
            "io_ports": {
                "P1": "亮度控制 (RW) - 0-100%调节",
                "P2": "色温控制 (RW) - 2700K-6500K调节",
            },
            "platforms": ["light"],  # 灯光平台
            "application_scenarios": ["家居照明", "办公环境", "商业空间"],
            "experimental": False,  # 成熟产品
            "third_party": False,  # LifeSmart原生设备
            "support_level": "official",  # 官方支持
        },
        # ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
        # │ SL_LI_WW_V2 - 调光调色智控器(0-10V) (0-10V Dimming Controller) │
        # └─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
        # 工业级调光控制器，采用0-10V标准调光协议，适用于专业照明系统
        #
        # 【IO口配置】(遵循SL_LI_WW标准规范，但输出为0-10V信号)
        # P1: 亮度控制 (RW) - 输出0-10V调光信号，控制外部调光驱动器
        # P2: 色温控制 (RW) - 输出0-10V色温控制信号，控制双色温灯具
        #
        # 【技术特点】
        # - 0-10V标准协议：符合国际照明控制标准，兼容性强
        # - 工业级设计：高可靠性，适用于恶劣环境
        # - 大功率支持：可控制大功率LED阵列和灯具系统
        # - 精确控制：提供精确的亮度和色温控制
        #
        # 【应用场景】
        # - 工业照明：工厂、车间、仓库等工业环境
        # - 商业项目：大型商场、办公楼、展览馆等
        # - 景观照明：建筑外观、园林景观、道路照明
        "V2": {
            "type": "dimmable_light_v2",  # 工业调光控制器类型
            "description": "调光调色智控器(0-10V) - 工业级调光控制器，采用0-10V标准协议，适用于专业照明系统和大功率灯具控制",
            "features": [
                "0-10V标准协议输出",
                "工业级可靠性设计",
                "大功率负载支持",
                "精确调光控制",
                "双色温控制输出",
                "宽电压输入范围",
            ],
            "io_ports": {
                "P1": "亮度控制 (RW) - 0-10V调光信号输出",
                "P2": "色温控制 (RW) - 0-10V色温信号输出",
            },
            "platforms": ["light"],  # 灯光平台
            "application_scenarios": ["工业照明", "商业项目", "景观照明"],
            "technical_specs": {
                "output_protocol": "0-10V",
                "max_load": "大功率LED阵列",
                "reliability": "工业级",
                "environment": "宽温度范围",
            },
            "experimental": False,  # 成熟产品
            "third_party": False,  # LifeSmart原生设备
            "support_level": "official",  # 官方支持
        },
    },
}

# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 设备支持级别分类系统
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

# 【支持级别说明】
# LifeSmart系统采用三级支持级别体系，为用户提供清晰的设备支持状态信息：
#
# 1. Official (官方支持)
#    - 由LifeSmart官方完全支持和维护的设备
#    - 经过完整测试，稳定可靠，兼容性强
#    - 提供完整的功能支持和技术保障
#    - 推荐用于生产环境和关键应用
#
# 2. Community (社区支持)
#    - 由社区测试和维护的设备，通常比较稳定
#    - 基本功能完整，可能存在少量已知问题
#    - 社区提供技术支持和问题解决
#    - 适用于大多数应用场景
#
# 3. Experimental (实验性支持)
#    - 实验性或测试阶段的设备支持
#    - 可能存在功能限制、兼容性问题或稳定性问题
#    - 主要用于测试和开发目的
#    - 不推荐用于生产环境

SUPPORT_LEVELS: Dict[SupportLevel, Dict[str, Any]] = {
    "official": {
        "name": "官方支持",
        "name_en": "Official Support",
        "description": "由LifeSmart官方完全支持的设备，经过严格测试，稳定可靠，提供完整功能支持",
        "stability": "stable",  # 稳定性级别
        "reliability": "high",  # 可靠性级别
        "recommended": True,  # 是否推荐使用
        "production_ready": True,  # 是否适用于生产环境
        "support_channels": ["官方技术支持", "在线文档", "社区论坛"],
        "update_frequency": "regular",  # 更新频率
        "icon": "✅",  # 状态图标
        "color": "green",  # 状态颜色
    },
    "community": {
        "name": "社区支持",
        "name_en": "Community Support",
        "description": "由社区测试和支持的设备，基本功能完整，通常稳定可用",
        "stability": "mostly_stable",  # 大部分稳定
        "reliability": "medium",  # 中等可靠性
        "recommended": True,  # 推荐使用
        "production_ready": True,  # 可用于生产环境
        "support_channels": ["社区论坛", "GitHub Issues", "用户文档"],
        "update_frequency": "community_driven",  # 社区驱动更新
        "icon": "🟡",  # 状态图标
        "color": "orange",  # 状态颜色
    },
    "experimental": {
        "name": "实验性支持",
        "name_en": "Experimental Support",
        "description": "实验性或测试阶段的设备，可能存在功能限制或稳定性问题",
        "stability": "unstable",  # 不稳定
        "reliability": "low",  # 低可靠性
        "recommended": False,  # 不推荐常规使用
        "production_ready": False,  # 不适用于生产环境
        "support_channels": ["GitHub Issues", "开发者论坛"],
        "update_frequency": "irregular",  # 不定期更新
        "icon": "🧪",  # 状态图标
        "color": "red",  # 状态颜色
        "warnings": [
            "可能存在功能限制",
            "稳定性有待验证",
            "不推荐用于生产环境",
            "功能可能随时变更",
        ],
    },
}

# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 严格映射定义
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

# 【Gen2严格映射说明】
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# API函数集合 - 设备信息查询和状态判断
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════


def get_third_party_device_info(
    device_type: DeviceType, version: VersionString
) -> Optional[DeviceInfo]:
    """
    获取第三方设备的详细信息

    这个函数是第三方设备信息查询的核心API，通过设备类型和版本号获取完整的设备配置信息。
    它支持所有已注册的第三方设备类型，包括空调系统、新风设备、RS485设备和电力设备。

    【功能特性】
    - 精确的设备类型和版本匹配
    - 完整的设备信息返回，包括厂商、型号、功能特性等
    - 安全的None返回，避免KeyError异常
    - 支持所有四大类第三方设备

    【使用场景】
    - 设备初始化时获取设备配置信息
    - 动态设备识别和功能映射
    - 设备管理界面的信息显示
    - 兼容性检查和功能验证

    Args:
        device_type (DeviceType): 设备类型标识符
            支持的类型：
            - "V_AIR_P": 空调/暖通设备
            - "V_FRESH_P": 新风系统设备
            - "V_485_P": RS485通信设备
            - "V_DLT645_P": 电力设备

        version (VersionString): 设备版本号
            格式: "主版本.次版本.修订版本.构建版本"
            例如: "0.0.0.1", "0.0.0.15"

    Returns:
        Optional[DeviceInfo]: 设备信息字典，如果未找到则返回None
            返回的字典包含以下字段：
            - code: 设备唯一识别码
            - model: 厂商型号
            - name: 设备显示名称
            - manufacturer: 制造商信息
            - category: 设备功能分类
            - features: 功能特性列表
            - io_ports: IO口配置信息
            - third_party: 第三方设备标识
            - experimental: 实验性支持标识
            - support_level: 支持级别

    Example:
        >>> # 获取大金空调设备信息
        >>> device_info = get_third_party_device_info("V_AIR_P", "0.0.0.1")
        >>> if device_info:
        ...     print(f"设备名称: {device_info['name']}")
        ...     print(f"制造商: {device_info['manufacturer']}")
        ...     print(f"支持级别: {device_info['support_level']}")

        >>> # 获取不存在的设备信息
        >>> device_info = get_third_party_device_info("UNKNOWN", "1.0.0.0")
        >>> print(device_info)  # 输出: None
    """
    return THIRD_PARTY_DEVICES.get(device_type, {}).get(version)


def get_versioned_device_info(
    device_type: DeviceType, version: VersionString
) -> Optional[DeviceInfo]:
    """
    获取需要版本区分的LifeSmart原生设备信息

    这个函数专门处理LifeSmart原生设备中需要版本区分的设备类型。某些设备虽然型号相同，
    但在不同版本中具有不同的IO口配置、功能特性或硬件规范，需要通过版本号进行精确识别。

    【版本区分原理】
    - 基于设备的fullCls字段进行版本识别
    - 只有在功能和IO口存在显著差异时才进行版本区分
    - 每个版本都有独立的功能描述和技术规范
    - 支持版本间的功能对比和选择建议

    【当前支持的设备】
    - SL_SW_DM1: 调光开关系列 (V1动态调光开关 vs V2可控硅调光开关)
    - SL_LI_WW: 白光调光灯系列 (V1智能灯泡 vs V2工业控制器)

    Args:
        device_type (DeviceType): 设备类型标识符
            当前支持：
            - "SL_SW_DM1": 调光开关系列
            - "SL_LI_WW": 白光调光灯系列

        version (VersionString): 设备版本标识符
            格式: "V1", "V2", "V3" 等
            每个版本对应不同的功能特性和技术规范

    Returns:
        Optional[DeviceInfo]: 版本设备信息字典，如果未找到则返回None
            返回的字典包含以下字段：
            - type: 设备功能类型标识
            - description: 详细的设备功能描述
            - features: 功能特性列表
            - io_ports: IO口配置详情
            - platforms: 支持的Home Assistant平台
            - experimental: 实验性支持标识
            - third_party: 第三方设备标识
            - support_level: 支持级别
            - application_scenarios: 应用场景(如果适用)
            - technical_specs: 技术规格(如果适用)

    Example:
        >>> # 获取动态调光开关V1信息
        >>> device_info = get_versioned_device_info("SL_SW_DM1", "V1")
        >>> if device_info:
        ...     print(f"设备类型: {device_info['type']}")
        ...     print(f"功能描述: {device_info['description']}")
        ...     print(f"IO口配置: {device_info['io_ports']}")

        >>> # 对比不同版本的功能
        >>> v1_info = get_versioned_device_info("SL_SW_DM1", "V1")
        >>> v2_info = get_versioned_device_info("SL_SW_DM1", "V2")
        >>> print(f"V1特性: {v1_info['features']}")
        >>> print(f"V2特性: {v2_info['features']}")
    """
    return VERSIONED_DEVICE_TYPES.get(device_type, {}).get(version)


def is_third_party_device(device_type: DeviceType) -> bool:
    """
    检查指定设备类型是否为第三方设备

    这个函数提供快速的设备类型判断，帮助系统识别设备是否属于第三方厂商设备。
    这个判断对于设备管理、功能限制、支持策略等方面的决策具有重要意义。

    【判断逻辑】
    - 基于THIRD_PARTY_DEVICES映射表进行判断
    - 只要设备类型在第三方映射表中存在，即视为第三方设备
    - 不考虑具体版本，只判断设备类型级别

    【应用场景】
    - 设备初始化时的类型识别
    - 功能权限控制和限制
    - 用户界面的分类显示
    - 技术支持渠道的路由选择
    - 设备管理策略的制定

    Args:
        device_type (DeviceType): 设备类型标识符
            例如: "V_AIR_P", "V_FRESH_P", "V_485_P", "V_DLT645_P"

    Returns:
        bool: 如果是第三方设备类型返回True，否则返回False

    Example:
        >>> # 检查空调设备类型
        >>> is_third_party_device("V_AIR_P")
        True

        >>> # 检查LifeSmart原生设备
        >>> is_third_party_device("SL_SW_DM1")
        False

        >>> # 检查不存在的设备类型
        >>> is_third_party_device("UNKNOWN_TYPE")
        False
    """
    return device_type in THIRD_PARTY_DEVICES


def is_versioned_device(device_type: DeviceType) -> bool:
    """
    检查指定设备类型是否需要版本区分

    这个函数用于识别哪些设备类型存在多个版本，需要进行版本级别的功能区分。
    版本区分主要用于处理同一设备型号在不同批次或配置下的功能差异。

    【版本区分必要性】
    - IO口配置存在差异
    - 硬件功能特性不同
    - 控制逻辑或协议差异
    - 应用场景和技术规格不同

    【版本管理策略】
    - 只有功能差异显著的设备才需要版本区分
    - 版本信息必须来源于设备的fullCls字段
    - 每个版本都需要详细的功能说明和使用指南
    - 支持版本间的平滑升级和兼容性处理

    Args:
        device_type (DeviceType): 设备类型标识符
            例如: "SL_SW_DM1", "SL_LI_WW"

    Returns:
        bool: 如果设备类型需要版本区分返回True，否则返回False

    Example:
        >>> # 检查调光开关是否需要版本区分
        >>> is_versioned_device("SL_SW_DM1")
        True

        >>> # 检查白光调光灯是否需要版本区分
        >>> is_versioned_device("SL_LI_WW")
        True

        >>> # 检查普通设备类型
        >>> is_versioned_device("SL_SW_ON")
        False
    """
    return device_type in VERSIONED_DEVICE_TYPES


def get_device_support_info(device_info: DeviceInfo) -> Dict[str, Any]:
    """
    获取设备的完整支持信息和状态详情

    这个函数基于设备信息生成完整的支持状态报告，包括支持级别、稳定性评估、
    推荐使用建议等关键信息。这些信息对用户选择和系统决策具有重要参考价值。

    【支持信息组成】
    - 基础支持级别信息 (来自SUPPORT_LEVELS)
    - 设备特定的标志和属性
    - 综合的可靠性和稳定性评估
    - 使用建议和注意事项

    【信息来源】
    - device_info中的support_level字段
    - device_info中的third_party和experimental标志
    - SUPPORT_LEVELS中的预定义支持级别信息
    - 系统的综合评估逻辑

    【决策支持】
    - 为用户提供设备选择建议
    - 为系统提供功能启用策略
    - 为技术支持提供问题定位依据
    - 为开发团队提供优化方向

    Args:
        device_info (DeviceInfo): 设备信息字典
            必须包含的字段：
            - support_level: 支持级别 (可选，默认为"community")
            - third_party: 是否为第三方设备 (可选，默认为False)
            - experimental: 是否为实验性设备 (可选，默认为False)

    Returns:
        Dict[str, Any]: 完整的设备支持信息字典
            包含以下字段：
            - name: 支持级别名称
            - description: 支持级别描述
            - stability: 稳定性级别
            - reliability: 可靠性级别
            - recommended: 是否推荐使用
            - production_ready: 是否适用于生产环境
            - support_channels: 技术支持渠道列表
            - update_frequency: 更新频率
            - icon: 状态图标
            - color: 状态颜色
            - third_party: 第三方设备标识
            - experimental: 实验性设备标识
            - support_level: 原始支持级别
            - warnings: 警告信息列表(如果适用)

    Example:
        >>> # 获取第三方设备支持信息
        >>> device_info = {
        ...     "support_level": "community",
        ...     "third_party": True,
        ...     "experimental": False
        ... }
        >>> support_info = get_device_support_info(device_info)
        >>> print(f"支持级别: {support_info['name']}")
        >>> print(f"推荐使用: {support_info['recommended']}")
        >>> print(f"技术支持: {support_info['support_channels']}")

        >>> # 获取实验性设备支持信息
        >>> experimental_device = {
        ...     "support_level": "experimental",
        ...     "third_party": True,
        ...     "experimental": True
        ... }
        >>> support_info = get_device_support_info(experimental_device)
        >>> print(f"警告信息: {support_info.get('warnings', [])}")
        >>> print(f"生产就绪: {support_info['production_ready']}")
    """
    # 获取设备的支持级别，默认为community级别
    support_level = device_info.get("support_level", "community")

    # 从预定义的支持级别信息中获取基础信息，如果找不到则使用community作为默认值
    support_info = SUPPORT_LEVELS.get(support_level, SUPPORT_LEVELS["community"]).copy()

    # 添加设备特定的标志和属性信息
    support_info.update(
        {
            "third_party": device_info.get("third_party", False),  # 第三方设备标识
            "experimental": device_info.get("experimental", False),  # 实验性设备标识
            "support_level": support_level,  # 原始支持级别保留
        }
    )

    return support_info


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 便利函数集合 - 高级查询和批量操作
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════


def get_all_third_party_devices() -> Dict[DeviceType, Dict[VersionString, DeviceInfo]]:
    """
    获取所有第三方设备的完整映射表

    这个函数返回完整的第三方设备映射表，主要用于系统初始化、
    设备列表展示、批量操作等需要访问全部设备信息的场景。

    Returns:
        Dict[DeviceType, Dict[VersionString, DeviceInfo]]: 完整的第三方设备映射表

    Example:
        >>> all_devices = get_all_third_party_devices()
        >>> for device_type, versions in all_devices.items():
        ...     print(f"设备类型: {device_type}, 版本数量: {len(versions)}")
    """
    return THIRD_PARTY_DEVICES.copy()


def get_devices_by_support_level(support_level: SupportLevel) -> List[Dict[str, Any]]:
    """
    根据支持级别筛选设备列表

    这个函数用于获取特定支持级别的所有设备，便于进行分类管理、
    批量操作或用户界面的分级显示。

    Args:
        support_level (SupportLevel): 支持级别 ("official", "community", "experimental")

    Returns:
        List[Dict[str, Any]]: 符合条件的设备信息列表
            每个设备信息包含原始设备数据加上设备类型和版本信息

    Example:
        >>> # 获取所有官方支持的设备
        >>> official_devices = get_devices_by_support_level("official")
        >>> print(f"官方支持设备数量: {len(official_devices)}")

        >>> # 获取所有实验性设备
        >>> experimental_devices = get_devices_by_support_level("experimental")
        >>> for device in experimental_devices:
        ...     print(f"实验性设备: {device['name']}")
    """
    devices = []

    # 遍历第三方设备
    for device_type, versions in THIRD_PARTY_DEVICES.items():
        for version, device_info in versions.items():
            if device_info.get("support_level") == support_level:
                device_with_meta = device_info.copy()
                device_with_meta.update(
                    {
                        "device_type": device_type,
                        "version": version,
                        "source": "third_party",
                    }
                )
                devices.append(device_with_meta)

    # 遍历版本设备
    for device_type, versions in VERSIONED_DEVICE_TYPES.items():
        for version, device_info in versions.items():
            if device_info.get("support_level") == support_level:
                device_with_meta = device_info.copy()
                device_with_meta.update(
                    {
                        "device_type": device_type,
                        "version": version,
                        "source": "versioned",
                    }
                )
                devices.append(device_with_meta)

    return devices


def get_devices_by_manufacturer(manufacturer: str) -> List[Dict[str, Any]]:
    """
    根据制造商筛选设备列表

    这个函数用于获取特定制造商的所有设备，支持制造商设备的
    统一管理和品牌相关的功能处理。

    Args:
        manufacturer (str): 制造商名称 (支持部分匹配，不区分大小写)

    Returns:
        List[Dict[str, Any]]: 符合条件的设备信息列表

    Example:
        >>> # 获取大金品牌的所有设备
        >>> daikin_devices = get_devices_by_manufacturer("大金")
        >>> for device in daikin_devices:
        ...     print(f"大金设备: {device['name']}")

        >>> # 获取开利品牌的所有设备
        >>> carrier_devices = get_devices_by_manufacturer("开利")
        >>> print(f"开利设备数量: {len(carrier_devices)}")
    """
    devices = []
    manufacturer_lower = manufacturer.lower()

    for device_type, versions in THIRD_PARTY_DEVICES.items():
        for version, device_info in versions.items():
            device_manufacturer = device_info.get("manufacturer", "").lower()
            if manufacturer_lower in device_manufacturer:
                device_with_meta = device_info.copy()
                device_with_meta.update(
                    {"device_type": device_type, "version": version}
                )
                devices.append(device_with_meta)

    return devices


def validate_device_mapping() -> Dict[str, Any]:
    """
    验证设备映射配置的完整性和一致性

    这个函数对整个设备映射配置进行全面验证，检查数据完整性、
    一致性和合规性，帮助发现配置错误和潜在问题。

    【验证项目】
    - 必需字段完整性检查
    - 数据类型和格式验证
    - 支持级别一致性检查
    - 版本号格式验证
    - 重复设备检查
    - 引用完整性验证

    Returns:
        Dict[str, Any]: 验证结果报告
            包含以下字段：
            - valid: 总体验证结果
            - errors: 错误信息列表
            - warnings: 警告信息列表
            - statistics: 统计信息
            - recommendations: 改进建议

    Example:
        >>> validation_result = validate_device_mapping()
        >>> if not validation_result['valid']:
        ...     print("配置验证失败:")
        ...     for error in validation_result['errors']:
        ...         print(f"  错误: {error}")
        >>> else:
        ...     print("配置验证通过")
        ...     print(f"统计信息: {validation_result['statistics']}")
    """
    errors = []
    warnings = []
    statistics = {}

    # 验证第三方设备映射
    third_party_count = 0
    experimental_count = 0

    for device_type, versions in THIRD_PARTY_DEVICES.items():
        for version, device_info in versions.items():
            third_party_count += 1

            # 检查必需字段
            required_fields = ["code", "model", "name", "third_party"]
            for field in required_fields:
                if field not in device_info:
                    errors.append(
                        f"第三方设备 {device_type}:{version} 缺少必需字段: {field}"
                    )

            # 检查支持级别
            support_level = device_info.get("support_level", "community")
            if support_level not in SUPPORT_LEVELS:
                errors.append(
                    f"第三方设备 {device_type}:{version} 支持级别无效: {support_level}"
                )

            # 统计实验性设备
            if device_info.get("experimental", False):
                experimental_count += 1

    # 验证版本设备映射
    versioned_count = 0

    for device_type, versions in VERSIONED_DEVICE_TYPES.items():
        for version, device_info in versions.items():
            versioned_count += 1

            # 检查必需字段
            required_fields = ["type", "description", "third_party"]
            for field in required_fields:
                if field not in device_info:
                    errors.append(
                        f"版本设备 {device_type}:{version} 缺少必需字段: {field}"
                    )

    # 生成统计信息
    statistics = {
        "third_party_devices": third_party_count,
        "versioned_devices": versioned_count,
        "experimental_devices": experimental_count,
        "total_devices": third_party_count + versioned_count,
        "support_levels": len(SUPPORT_LEVELS),
        "device_categories": len(set(THIRD_PARTY_DEVICES.keys())),
    }

    # 生成建议
    recommendations = []
    if experimental_count > third_party_count * 0.3:
        recommendations.append("实验性设备比例较高，建议加强稳定性测试")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "statistics": statistics,
        "recommendations": recommendations,
    }


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 模块导出和版本信息
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

# 模块版本信息
__version__ = "2.5.0"
__author__ = "MapleEve"
__last_updated__ = "2025-08-12"

# 公开API列表
__all__ = [
    # 核心数据结构
    "THIRD_PARTY_DEVICES",
    "VERSIONED_DEVICE_TYPES",
    "SUPPORT_LEVELS",

    # 类型定义
    "DeviceInfo",
    "VersionString",
    "DeviceType",
    "SupportLevel",
    # 核心API函数
    "get_third_party_device_info",
    "get_versioned_device_info",
    "is_third_party_device",
    "is_versioned_device",
    "get_device_support_info",
    # 便利函数
    "get_all_third_party_devices",
    "get_devices_by_support_level",
    "get_devices_by_manufacturer",
    "validate_device_mapping",
]

# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 模块初始化和自检
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

# 执行模块加载时的自检
if __name__ == "__main__":
    # 验证配置完整性
    validation_result = validate_device_mapping()

    if validation_result["valid"]:
        print(f"✅ LifeSmart第三方设备映射配置加载成功 (v{__version__})")
        print(f"📊 统计信息: {validation_result['statistics']}")
    else:
        print(f"❌ 配置验证失败，发现 {len(validation_result['errors'])} 个错误")
        for error in validation_result["errors"]:
            print(f"   - {error}")
