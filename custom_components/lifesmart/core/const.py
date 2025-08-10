"""由 @MapleEve 实现的 LifeSmart 集成常量模块。

此文件定义了所有与 LifeSmart 平台交互所需的硬编码常量、设备类型代码、API命令码、
以及用于在 Home Assistant 和 LifeSmart 之间转换数据的映射。

维护此文件的准确性和清晰度对于整个集成的稳定和可扩展性至关重要。

重构说明:
此文件已从原const.py重构，移除所有helper函数和DEVICE_MAPPING，
保持单一职责原则，只定义纯常量。

设备映射和helper函数已迁移到:
- devices/mapping.py: 设备配置映射和helper函数
- utils/: 工具函数模块
"""

from homeassistant.const import (
    Platform,
)

from .compatibility import get_platform_constants

_platform_constants = get_platform_constants()
_EVENT_PLATFORM = _platform_constants.get("EVENT")
_VALVE_PLATFORM = _platform_constants.get("VALVE")

# ================= 重要技术说明 (Critical Technical Documentation) =================

"""
⚠️ 重要：LifeSmart设备动态分类和IO口处理技术说明 ⚠️

本集成支持LifeSmart平台的全系列智能设备，包含复杂的动态设备分类逻辑和精确的IO口控制协议。
以下是关键技术要点，修改时务必理解这些规则：

1. 【动态设备分类规则】
   某些设备根据配置参数动态决定功能：
   - SL_P通用控制器：根据P1口工作模式(P1>>24)&0xE决定是开关、窗帘还是传感器
   - SL_NATURE超能面板：根据P5口值(P5&0xFF)决定是开关版(1)还是温控版(3/6)
   - 动态分类实现在core/platform/platform_detection.py中，不能仅依赖设备类型判断

2. 【IO口数据格式和位运算规则】
   LifeSmart使用type和val两个字段表示IO口状态：
   - type字段：奇偶性(type&1)表示开关状态，1=开启/0=关闭
   - val字段：根据设备类型表示亮度、温度、颜色等具体数值
   - 浮点数据：当(type&0x7e)==0x2时，val为IEEE754浮点数的32位整数表示
   - 详细转换逻辑见core/data/conversion.py中的转换函数

3. 【设备版本区分机制】
   部分设备通过fullCls字段区分版本，必须正确识别：
   - SL_SW_DM1_V1: 动态调光开关(带传感器)
   - SL_SW_DM1_V2: 基础调光开关(可控硅)
   - 版本区分逻辑位于core/platform/platform_detection.py

4. 【多平台设备支持】
   单个物理设备可支持多个Home Assistant平台：
   - 如SL_OE_3C: 同时支持switch(开关功能)、sensor(用电量、功率)
   - 平台映射通过core/config/device_specs.py和mapping_engine.py定义
   - 动态平台检测通过core/platform/platform_detection.py实现

5. 【版本兼容性】
   本集成支持HA版本：2022.10.0 to latest
   - 兼容性处理统一在core/compatibility.py中管理
   - 移除了过时的兼容代码，基于最低支持版本优化
   - 平台常量通过get_platform_constants()统一获取
"""

# ================= 核心配置常量 (Core Configuration Constants) =================

# 集成基础信息
DOMAIN = "lifesmart"
MANUFACTURER = "LifeSmart"

# 设备数据结构键名
HUB_ID_KEY = "agt"  # 智慧中心 (网关) 的唯一标识符
DEVICE_ID_KEY = "me"  # 设备的唯一标识符
DEVICE_TYPE_KEY = "devtype"  # 设备的类型代码，用于区分不同种类的设备
DEVICE_FULLCLS_KEY = "fullCls"  # 包含版本号的完整设备类型，用于区分设备版本
DEVICE_NAME_KEY = "name"  # 设备的用户自定义名称
DEVICE_DATA_KEY = "data"  # 包含设备所有IO口状态的字典
DEVICE_VERSION_KEY = "ver"  # 设备的固件或软件版本
SUBDEVICE_INDEX_KEY = "idx"  # 子设备或IO口的索引键，如 'L1', 'P1'

# 配置存储键名
UPDATE_LISTENER = "update_listener"  # 用于在 hass.data 中存储配置更新监听器的键
LIFESMART_STATE_MANAGER = (
    "lifesmart_state_manager"  # 用于在 hass.data 中存储状态管理器的键
)
LIFESMART_SIGNAL_UPDATE_ENTITY = "lifesmart_updated"  # 用于在集成内部进行事件通知的信号

# ================= 配置参数键名 (Configuration Parameter Keys) =================
CONF_LIFESMART_APPKEY = "appkey"
CONF_LIFESMART_APPTOKEN = "apptoken"
CONF_LIFESMART_USERTOKEN = "usertoken"
CONF_LIFESMART_AUTH_METHOD = "auth_method"
CONF_LIFESMART_USERPASSWORD = "userpassword"
CONF_LIFESMART_USERID = "userid"
CONF_EXCLUDE_ITEMS = "exclude"
CONF_EXCLUDE_AGTS = "exclude_agt"
CONF_AI_INCLUDE_AGTS = "ai_include_agt"
CONF_AI_INCLUDE_ITEMS = "ai_include_me"
CONF_LIFESMART_REGION = "region"
CONF_LIFESMART_AUTHCODE = "auth_code"
CONF_LIFESMART_LOCAL_SUPPORT = "enable_local"
CONF_LIFESMART_LOCAL_IP = "local_ip"
CONF_LIFESMART_LOCAL_PORT = "local_port"
CONF_LIFESMART_LOCAL_TIMEOUT = "local_timeout"

# ================= AI 类型常量 (AI Type Constants) =================
CON_AI_TYPE_SCENE = "scene"
CON_AI_TYPE_AIB = "aib"

# ================= IO数据类型常量 (IO Data Type Constants) =================
# 用于判断和处理不同类型的IO数据，如浮点数、异常数据等

IO_TYPE_FLOAT_MASK = 0x7E  # 用于判断是否为浮点类型
IO_TYPE_FLOAT_VALUE = 0x02  # 浮点类型标识
IO_TYPE_EXCEPTION = 0x1E  # 异常数据类型

# IO精度计算相关
IO_TYPE_PRECISION_MASK = 0x78
IO_TYPE_PRECISION_BASE = 0x08
IO_TYPE_PRECISION_BITS = 0x06

# ================= 命令类型常量 (Command Type Constants) =================
# LifeSmart设备的标准控制命令码，用于向设备发送操作指令

CMD_TYPE_ON = 0x81  # 通用开启命令
CMD_TYPE_OFF = 0x80  # 通用关闭命令
CMD_TYPE_PRESS = 0x89  # 点动命令
CMD_TYPE_SET_VAL = 0xCF  # 设置数值/启用功能 (如亮度、窗帘位置、功率门限启用)
CMD_TYPE_SET_CONFIG = 0xCE  # 设置配置/禁用功能 (如空调模式、风速、功率门限禁用)
CMD_TYPE_SET_TEMP_DECIMAL = 0x88  # 设置温度 (值为实际温度*10)
CMD_TYPE_SET_RAW_ON = 0xFF  # 开灯亮度/配置设置开始(颜色、动态、配置值等)
CMD_TYPE_SET_RAW_OFF = 0xFE  # 关灯亮度设置/配置设置停止（颜色、动态、配置值等）
CMD_TYPE_SET_TEMP_FCU = 0x89  # FCU温控器设置温度的特殊命令码

# ================= 服务调用相关常量 (Service Call Constants) =================
SERVICE_SEND_KEYS = "send_keys"  # 发送按键命令服务
SERVICE_SET_STATE = "set_state"  # 设置设备状态服务

ATTR_TYPE = "type"  # 命令类型属性
ATTR_VAL = "val"  # 命令值属性
ATTR_INDEX = "idx"  # 子设备索引属性
ATTR_AZ = "az"  # 区域属性（用于部分第三方设备）

# ================= 认证配置常量 (Authentication Configuration Constants) =================
REGION_MAPPING = {
    "AUTO": "AUTO",
    "cn0": "cn0",
    "cn1": "cn1",
    "cn2": "cn2",
    "us": "us",
    "eur": "eur",
    "jp": "jp",
    "apz": "apz",
}

# 默认配置值
DEFAULT_REGION = "AUTO"
DEFAULT_AUTH_METHOD = "账号密码"
DEFAULT_LOCAL_PORT = 8888
DEFAULT_LOCAL_TIMEOUT = 30

# ================= 网络通信常量 (Network Communication Constants) =================

# WebSocket连接配置
WS_HEARTBEAT_INTERVAL = 30  # 心跳间隔(秒)
WS_RECONNECT_DELAY = 5  # 重连延迟(秒)
WS_MAX_RECONNECT_ATTEMPTS = 10  # 最大重连次数
WS_RECEIVE_TIMEOUT = 30  # WebSocket接收消息超时(秒)
WS_CLOSE_TIMEOUT = 5.0  # WebSocket关闭超时(秒)
WS_HEARTBEAT_TIMEOUT = 5.0  # WebSocket心跳超时(秒)

# HTTP请求配置
HTTP_TIMEOUT = 30  # HTTP请求超时时间(秒)
HTTP_MAX_RETRIES = 3  # HTTP请求最大重试次数

# TCP连接配置
TCP_CONNECT_TIMEOUT = 5  # TCP连接超时(秒)
TCP_READ_TIMEOUT = 10  # TCP读取超时(秒)
TCP_DEFAULT_TIMEOUT = 10  # TCP默认超时(秒)

# 平台实体相关超时
BINARY_SENSOR_BUTTON_RESET_DELAY = 0.5  # 二进制传感器按钮重置延迟(秒)
CONCURRENCY_QUEUE_TIMEOUT = 0.1  # 并发管理队列超时(秒)

# ================= Home Assistant 平台支持 (HA Platform Support) =================
# Home Assistant 支持的平台列表
# Build supported platforms dynamically based on HA version
_BASE_PLATFORMS = {
    Platform.SWITCH,
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.COVER,
    Platform.LIGHT,
    Platform.CLIMATE,
    Platform.BUTTON,  # 新增: 按钮平台
    Platform.FAN,  # 新增: 风扇平台
    Platform.LOCK,  # 新增: 门锁平台
    Platform.CAMERA,  # 新增: 摄像头平台
    Platform.REMOTE,
    Platform.NUMBER,  # 新增: 数值平台
    Platform.AIR_QUALITY,  # 新增: 空气质量平台
    Platform.SIREN,  # 新增: 警报平台
    Platform.SCENE,  # 新增: 场景平台
}

SUPPORTED_PLATFORMS = _BASE_PLATFORMS.copy()

if _EVENT_PLATFORM is not None:
    SUPPORTED_PLATFORMS.add(_EVENT_PLATFORM)  # 新增: 事件平台 (仅限新版本HA)

if _VALVE_PLATFORM is not None:
    SUPPORTED_PLATFORMS.add(_VALVE_PLATFORM)  # 新增: 阀门平台 (仅限支持的HA版本)

# ================= 新增平台相关常量 (New Platform Constants) =================

# 按钮平台相关
BUTTON_PRESS_TIME = 0.1  # 按钮按下持续时间(秒)
BUTTON_DEBOUNCE_TIME = 0.5  # 按钮去抖时间(秒)

# 风扇平台相关
FAN_SPEED_LEVELS = [1, 2, 3, 4, 5]  # 支持的风扇速度级别
FAN_PRESET_MODES = ["auto", "sleep", "natural"]  # 预设模式

# 门锁平台相关
LOCK_TIMEOUT = 30  # 门锁操作超时时间(秒)
LOCK_STATE_LOCKED = 1
LOCK_STATE_UNLOCKED = 0

# 事件平台相关
EVENT_TYPES = {
    "button_press": "按钮按下",
    "motion_detected": "检测到移动",
    "door_opened": "门已打开",
    "door_closed": "门已关闭",
    "alarm_triggered": "警报触发",
}

# 摄像头平台相关
CAMERA_STREAM_TIMEOUT = 10  # 视频流超时时间(秒)
CAMERA_SNAPSHOT_TIMEOUT = 5  # 快照超时时间(秒)

# 数值平台相关
NUMBER_MIN_VALUE = 0
NUMBER_MAX_VALUE = 100
NUMBER_STEP = 1

# 气候平台相关
CLIMATE_DEFAULT_MIN_TEMP = 5  # 默认最低温度(摄氏度)
CLIMATE_DEFAULT_MAX_TEMP = 35  # 默认最高温度(摄氏度)
CLIMATE_HVAC_MIN_TEMP = 10  # HVAC最低温度(摄氏度)
CLIMATE_HVAC_MAX_TEMP = 35  # HVAC最高温度(摄氏度)

# 灯光平台相关
LIGHT_DEFAULT_MIN_KELVIN = 2700  # 默认最低色温(K)
LIGHT_DEFAULT_MAX_KELVIN = 6500  # 默认最高色温(K)

# 空气质量平台相关
AIR_QUALITY_EXCELLENT = 0  # 优
AIR_QUALITY_GOOD = 1  # 良
AIR_QUALITY_FAIR = 2  # 中等
AIR_QUALITY_POOR = 3  # 差
AIR_QUALITY_VERY_POOR = 4  # 很差

# 警报平台相关
SIREN_DURATION = 30  # 警报持续时间(秒)
SIREN_VOLUME_LEVELS = [1, 2, 3, 4, 5]  # 音量级别

# 场景平台相关
SCENE_ACTIVATION_TIME = 2  # 场景激活时间(秒)

# 阀门平台相关
VALVE_OPERATION_TIME = 10  # 阀门操作时间(秒)
VALVE_STATE_OPEN = 1
VALVE_STATE_CLOSED = 0

# Cover平台相关配置已迁移到新架构
# 车库门类型和杜亚类型配置现在位于: core/config/device_specs.py

# ================= 注意：设备类型映射已迁移 =================
#
# 设备类型到平台的映射已迁移到配置层，遵循"所有的东西以doc为准，不要信const"原则：
# - 设备规格定义: core/config/device_specs.py (基于官方文档《LifeSmart智慧设备规格属性说明.md》)
# - 动态平台检测: core/platform/platform_detection.py (运行时检测)
# - 映射引擎转换: core/config/mapping_engine.py (自动生成HA格式)
# - 设备数据处理: core/data/processors/ (数据处理和验证)
#
# 版本兼容性处理已统一移至core/compatibility.py，基于最低支持版本2022.10.0优化。
# 不再在const.py中硬编码设备类型集合，所有设备类型信息应从官方文档获取。
#
# 门锁解锁方式映射
UNLOCK_METHOD = {
    0: "None",
    1: "Password",
    2: "Fingerprint",
    3: "NFC",
    4: "Keys",
    5: "Remote",
    6: "12V Signal",
    7: "App",
    8: "Bluetooth",
    9: "Manual",
    15: "Error",
}

# 服务器区域选项 (用于配置流程)
LIFESMART_REGION_OPTIONS = [
    "cn0",
    "cn1",
    "cn2",
    "us",
    "eur",
    "jp",
    "apz",
    "AUTO",
]
