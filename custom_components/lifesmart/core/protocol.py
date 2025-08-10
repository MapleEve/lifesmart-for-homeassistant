"""转发模块：compatibility layer for core.protocol

这是为了测试兼容性而创建的转发模块，将旧的 core.protocol 导入
转发到新的架构位置。
"""

# 从client/protocol.py导入协议相关类
from .client.protocol import (
    LifeSmartProtocol,
    LifeSmartPacketFactory,
)

# 从const.py导入协议常量
from .const import (
    CMD_TYPE_SET_RAW_OFF,
    CMD_TYPE_SET_RAW_ON,
    CMD_TYPE_SET_VAL,
    CMD_TYPE_SET_CONFIG,
)

__all__ = [
    "LifeSmartProtocol",
    "LifeSmartPacketFactory",
    "CMD_TYPE_SET_RAW_OFF",
    "CMD_TYPE_SET_RAW_ON", 
    "CMD_TYPE_SET_VAL",
    "CMD_TYPE_SET_CONFIG",
]