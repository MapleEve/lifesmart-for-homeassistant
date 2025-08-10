"""
LifeSmart集成的自定义异常类。

定义了LifeSmart智能家居系统集成的各类异常：
- 基础异常类：LifeSmartError
- API错误异常：LifeSmartAPIError
- 身份验证失败异常：LifeSmartAuthError

创建者：@MapleEve
技术架构：分层异常处理机制
"""


class LifeSmartError(Exception):
    """
    LifeSmart集成的基础异常类。

    所有LifeSmart集成相关异常的父类。
    """

    pass


class LifeSmartAPIError(LifeSmartError):
    """
    LifeSmart API错误异常（非身份验证错误）。

    当LifeSmart API返回错误时抛出此异常。

    Attributes:
        message: 错误说明
        code: API返回的错误代码
    """

    def __init__(self, message: str, code: int | None = None):
        super().__init__(message)
        self.code = code


class LifeSmartAuthError(LifeSmartAPIError):
    """
    身份验证失败异常。

    这是与登录或令牌问题相关的特定API错误类型。
    """

    pass
