# 'core'目录是一个核心包

# Import and expose client modules for backward compatibility
from .client import local_tcp_client, openapi_client

# Also expose the module classes directly
from .client.local_tcp_client import LifeSmartTCPClient
from .client.openapi_client import LifeSmartOpenAPIClient

__all__ = [
    "local_tcp_client",
    "openapi_client",
    "LifeSmartTCPClient",
    "LifeSmartOpenAPIClient",
]
