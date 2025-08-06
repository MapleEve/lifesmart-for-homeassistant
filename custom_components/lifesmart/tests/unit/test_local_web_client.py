"""LifeSmart 本地 Web 客户端模块测试。"""

import logging

from custom_components.lifesmart.core import local_web_client


class TestLocalWebClientModule:
    """本地 Web 客户端模块测试用例。"""

    def test_module_imports(self):
        """测试模块是否可以成功导入。"""
        assert local_web_client is not None

    def test_logger_creation(self):
        """测试日志记录器是否正确创建。"""
        assert local_web_client._LOGGER is not None
        assert isinstance(local_web_client._LOGGER, logging.Logger)
        assert (
            local_web_client._LOGGER.name
            == "custom_components.lifesmart.core.local_web_client"
        )

    def test_module_docstring(self):
        """测试模块是否有适当的文档。"""
        assert local_web_client.__doc__ is not None
        assert "LifeSmart 本地 Web API 客户端" in local_web_client.__doc__
        assert "LifeSmartLocalWebClient" in local_web_client.__doc__
