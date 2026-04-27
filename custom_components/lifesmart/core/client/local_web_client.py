"""LifeSmart 本地 Web API 客户端，由 @MapleEve 初始创建和维护

此模块提供了一个 LifeSmartLocalWebClient 类，用于封装与 LifeSmart 本地 Web API 的所有交互。
它负责构建请求、处理签名、发送命令，并为上层平台（如 switch, light）
提供了一套清晰、易于使用的异步方法来控制设备。
"""

import logging

_LOGGER = logging.getLogger(__name__)


class LifeSmartWebClient:
    """LifeSmart Web API 客户端（兼容性存根）"""

    def __init__(self, *args, **kwargs):
        """初始化Web客户端"""
        pass

    async def async_send_command(self, *args, **kwargs):
        """发送命令（兼容性方法）"""
        pass
