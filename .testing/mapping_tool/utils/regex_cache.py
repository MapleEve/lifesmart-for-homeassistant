#!/usr/bin/env python3
"""
正则表达式缓存模块
提供预编译的正则表达式模式，避免重复编译，提升性能
"""

import re
from functools import lru_cache
from typing import Pattern, Optional, Tuple


class RegexCache:
    """正则表达式缓存管理器"""

    # 常用模式预编译
    VERSION_PATTERN = re.compile(r"_V\d+$")
    P_IO_PATTERN = re.compile(r"^P\d+$")
    DEVICE_NAME_PATTERN = re.compile(r"([A-Z][A-Z0-9_]*[:A-Z0-9_]*|cam)")

    # 设备清理模式
    DEVICE_SPLIT_PATTERN = re.compile(r"<br\s*/?>\s*|/")
    MARKDOWN_PATTERN = re.compile(r"^[0-9：；，\.\s\-~]+$")
    NUMBER_COLON_PATTERN = re.compile(r"^[0-9]+：[^；]*；?$")
    NUMBER_RANGE_PATTERN = re.compile(r"^[0-9]+~[0-9]+:[^；]*；?$")
    NUMBER_SIMPLE_PATTERN = re.compile(r"^[0-9]+:[^；]*；?$")
    LETTER_COLON_PATTERN = re.compile(r"^[A-Z]+:[A-Z]+$")

    # IO口清理模式
    IO_SPLIT_PATTERN = re.compile(r"[,\s]+")
    HTML_TAG_PATTERN = re.compile(r"<[^>]+>")

    # 通配符匹配模式
    BASE_PATTERN_REGEX = re.compile(r"^([A-Z]+)/?([A-Z]*)")
    WILDCARD_DOC_PATTERN = re.compile(r"/.*x.*取值为数字")
    WILDCARD_SIMPLE_PATTERN = re.compile(r"x.*取值为数字")

    @classmethod
    @lru_cache(maxsize=128)
    def get_compiled_pattern(cls, pattern: str, flags: int = 0) -> Pattern:
        """获取编译后的正则表达式模式，使用LRU缓存"""
        return re.compile(pattern, flags)

    @classmethod
    def is_version_device(cls, device_name: str) -> bool:
        """
        检查是否为版本设备

        修复：SL_SC_BB_V2, SL_P_V2 等不是版本设备，而是独立设备
        真正的版本设备应该在配置中有 version_modes 或 versioned 字段
        """
        # 已知的真实版本设备列表（基于配置中的 version_modes 或 versioned 字段）
        known_versioned_devices = {
            "SL_SW_DM1",  # 动态调光开关，有 version_modes 配置
            "SL_LI_WW",  # 调光调色控制器，有 version_modes 配置
        }

        # 只有在已知版本设备列表中的才被认为是版本设备
        return device_name in known_versioned_devices

    @classmethod
    def remove_version_suffix(cls, device_name: str) -> str:
        """移除版本后缀"""
        return cls.VERSION_PATTERN.sub("", device_name)

    @classmethod
    def is_p_io_port(cls, io_name: str) -> bool:
        """检查是否为P系列IO口"""
        return cls.P_IO_PATTERN.match(io_name) is not None

    @classmethod
    def extract_device_name(cls, text: str) -> Optional[str]:
        """从文本中提取设备名称"""
        match = cls.DEVICE_NAME_PATTERN.search(text)
        return match.group(1) if match else None

    @classmethod
    def split_device_names(cls, device_col: str) -> list[str]:
        """分割设备名称列表"""
        return cls.DEVICE_SPLIT_PATTERN.split(device_col)

    @classmethod
    def is_invalid_device_name(cls, name: str) -> bool:
        """检查是否为无效的设备名称"""
        if not name or len(name) <= 1:
            return True

        # 检查是否为纯数字标点
        if cls.MARKDOWN_PATTERN.match(name):
            return True

        # 检查各种无效格式
        invalid_patterns = [
            cls.NUMBER_COLON_PATTERN,
            cls.NUMBER_RANGE_PATTERN,
            cls.NUMBER_SIMPLE_PATTERN,
            cls.LETTER_COLON_PATTERN,
        ]

        return any(pattern.match(name) for pattern in invalid_patterns)

    @classmethod
    def clean_io_port_name(cls, io_port: str) -> str:
        """清理IO口名称"""
        # 移除反引号和空格
        clean_port = io_port.strip("`").strip()

        # 移除HTML标签
        clean_port = cls.HTML_TAG_PATTERN.sub("", clean_port).strip()

        # 移除末尾反引号
        clean_port = clean_port.rstrip("`")

        return clean_port

    @classmethod
    def split_io_ports(cls, io_port: str) -> list[str]:
        """分割IO口列表"""
        return cls.IO_SPLIT_PATTERN.split(io_port)

    @classmethod
    def match_wildcard_pattern(cls, pattern: str, text: str) -> bool:
        """匹配通配符模式"""
        if pattern.endswith("*"):
            base = pattern[:-1]
            # 构建动态模式
            wildcard_pattern = cls.get_compiled_pattern(
                rf"^{re.escape(base)}/.*x.*取值为数字|^{re.escape(base)}x.*取值为数字"
            )
            return wildcard_pattern.match(text) is not None or text.startswith(base)
        return False

    @classmethod
    def extract_base_pattern(cls, doc_io: str) -> Tuple[Optional[str], Optional[str]]:
        """从文档IO中提取基础模式"""
        match = cls.BASE_PATTERN_REGEX.match(doc_io)
        if match:
            base1 = match.group(1)
            base2 = match.group(2) or base1
            return base1, base2
        return None, None


# 提供便捷的模块级函数
def is_version_device(device_name: str) -> bool:
    """检查是否为版本设备"""
    return RegexCache.is_version_device(device_name)


def remove_version_suffix(device_name: str) -> str:
    """移除版本后缀"""
    return RegexCache.remove_version_suffix(device_name)


def is_p_io_port(io_name: str) -> bool:
    """检查是否为P系列IO口"""
    return RegexCache.is_p_io_port(io_name)


def extract_device_name(text: str) -> Optional[str]:
    """从文本中提取设备名称"""
    return RegexCache.extract_device_name(text)


def clean_io_port_name(io_port: str) -> str:
    """清理IO口名称"""
    return RegexCache.clean_io_port_name(io_port)


def split_io_ports(io_port: str) -> list[str]:
    """分割IO口列表"""
    return RegexCache.split_io_ports(io_port)


def match_wildcard_pattern(pattern: str, text: str) -> bool:
    """匹配通配符模式"""
    return RegexCache.match_wildcard_pattern(pattern, text)


# 性能统计装饰器
def regex_performance_monitor(func):
    """正则表达式性能监控装饰器"""

    def wrapper(*args, **kwargs):
        import time

        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        # 如果启用了调试模式，记录性能
        if hasattr(RegexCache, "_debug_mode") and RegexCache._debug_mode:
            print(
                f"🔧 {func.__name__} 执行时间: {(end_time - start_time) * 1000:.2f}ms"
            )

        return result

    return wrapper


# 启用调试模式的函数
def enable_debug_mode():
    """启用正则表达式性能调试模式"""
    RegexCache._debug_mode = True


def disable_debug_mode():
    """禁用正则表达式性能调试模式"""
    RegexCache._debug_mode = False
