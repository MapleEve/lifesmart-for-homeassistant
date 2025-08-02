# 顶层 conftest.py - 用于pytest插件配置
# 为了兼容低版本pytest，pytest_plugins必须在根目录conftest.py中定义

# 自动为所有测试加载 Home Assistant 的 pytest 插件
pytest_plugins = "pytest_homeassistant_custom_component"