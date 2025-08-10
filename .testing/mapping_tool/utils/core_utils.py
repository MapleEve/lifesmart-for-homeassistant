#!/usr/bin/env python3
"""
优化的核心工具模块 - 集中化的IO提取和常用工具
消除代码重复，提供高性能的通用功能
"""

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, Set, List, Any, Optional

try:
    from regex_cache import RegexCache, regex_performance_monitor
except ImportError:
    # Fallback if regex_cache is not available
    from typing import Pattern

    class RegexCache:
        VERSION_PATTERN = re.compile(r"_V\d+$")
        P_IO_PATTERN = re.compile(r"^P\d+$")
        DEVICE_NAME_PATTERN = re.compile(r"([A-Z][A-Z0-9_]*[:A-Z0-9_]*|cam)")
        HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
        BASE_PATTERN_REGEX = re.compile(r"^([A-Z]+)/?([A-Z]*)")

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
        def is_p_io_port(cls, io_name: str) -> bool:
            return cls.P_IO_PATTERN.match(io_name) is not None

        @classmethod
        def extract_device_name(cls, text: str) -> Optional[str]:
            match = cls.DEVICE_NAME_PATTERN.search(text)
            return match.group(1) if match else None

        @classmethod
        def clean_io_port_name(cls, io_port: str) -> str:
            return cls.HTML_TAG_PATTERN.sub("", io_port).strip()

        @classmethod
        def is_invalid_device_name(cls, name: str) -> bool:
            """检查是否为无效的设备名称"""
            if not name or len(name) <= 1:
                return True

            # 检查是否为纯数字标点
            if re.match(r"^[0-9：；，\.\s\-~]+$", name):
                return True

            # 检查各种无效格式
            invalid_patterns = [
                r"^[0-9]+：[^；]*；?$",
                r"^[0-9]+~[0-9]+:[^；]*；?$",
                r"^[0-9]+:[^；]*；?$",
                r"^[A-Z]+:[A-Z]+$",
            ]

            return any(re.match(pattern, name) for pattern in invalid_patterns)

        @classmethod
        def remove_version_suffix(cls, device_name: str) -> str:
            """移除版本后缀"""
            return cls.VERSION_PATTERN.sub("", device_name)

        @classmethod
        def extract_base_pattern(cls, doc_io: str):
            """从文档IO中提取基础模式 - fallback实现"""
            from typing import Optional, Tuple

            match = cls.BASE_PATTERN_REGEX.match(doc_io)
            if match:
                base1 = match.group(1)
                base2 = match.group(2) or base1
                return base1, base2
            return None, None

    def regex_performance_monitor(func):
        return func


@dataclass(frozen=True)
class IOPort:
    """IO口数据结构"""

    name: str
    rw: str
    description: str
    io_type: str = ""


# Note: OptimizedRegexPatterns is now replaced by RegexCache
# This class is kept for backward compatibility but delegates to RegexCache
class OptimizedRegexPatterns:
    """向后兼容的正则表达式模式类 - 委托给RegexCache"""

    @classmethod
    def is_version_device(cls, device_name: str) -> bool:
        """检查是否为版本设备"""
        return RegexCache.is_version_device(device_name)

    @classmethod
    def is_p_series_io(cls, io_name: str) -> bool:
        """检查是否为P系列IO口"""
        return RegexCache.is_p_io_port(io_name)

    @classmethod
    def extract_device_name(cls, text: str) -> Optional[str]:
        """提取设备名称"""
        return RegexCache.extract_device_name(text)

    @classmethod
    def clean_html_tags(cls, text: str) -> str:
        """清理HTML标签"""
        return RegexCache.clean_io_port_name(text)

    # 向后兼容的属性访问
    VERSION_PATTERN = property(lambda self: RegexCache.VERSION_PATTERN)
    IO_PORT_PATTERN = property(lambda self: RegexCache.P_IO_PATTERN)
    DEVICE_NAME_PATTERN = property(lambda self: RegexCache.DEVICE_NAME_PATTERN)
    NUMBER_COLON_PATTERN = property(lambda self: RegexCache.NUMBER_COLON_PATTERN)
    NUMBER_RANGE_PATTERN = property(lambda self: RegexCache.NUMBER_RANGE_PATTERN)
    ALPHA_COLON_PATTERN = property(lambda self: RegexCache.LETTER_COLON_PATTERN)
    HTML_TAG_PATTERN = property(lambda self: RegexCache.HTML_TAG_PATTERN)
    WILDCARD_MATCH_PATTERN = property(lambda self: RegexCache.BASE_PATTERN_REGEX)


class IOExtractor:
    """统一的IO口提取器 - 消除代码重复"""

    # 标准IO口名称集合 - 使用集合提供O(1)查找性能
    STANDARD_IO_NAMES = frozenset(
        {
            "L1",
            "L2",
            "L3",  # 开关系列
            "A",
            "A2",
            "T",
            "V",
            "TR",  # 传感器系列
            "M",
            "SR",
            "KP",
            "EPA",  # 控制系列
            "EE",
            "EP",
            "EQ",  # 扩展系列
            "bright",
            "dark",  # 指示灯系列
            "bright1",
            "bright2",
            "bright3",
            "dark1",
            "dark2",
            "dark3",
            "eB1",
            "eB2",
            "eB3",
            "eB4",  # 扩展按键系列
            "O",
            "B",  # 基础开关
            "CL",
            "OP",
            "ST",  # 窗帘控制
            "RGBW",
            "RGB",
            "DYN",  # 灯光控制
            "H",
            "Z",
            "WA",
            "G",
            "AXS",  # 传感器特殊口
            # 温控器和空调相关IO口
            "MODE",
            "F",
            "tT",  # 模式、风速、目标温度
            # 门锁相关IO口
            "ALM",
            "HISLK",
            "EVTOP",
            "EVTLO",
            "BAT",
            "EVTBEL",
            # 空气净化器相关IO口
            "PM",
            "FL",
            "UV",
            "RM",
            # 新风系统相关IO口
            "F1",
            "F2",
            # 其他常见IO口
            "CFST",  # 摄像头状态
            # V_485_P 复合IO口名称
            "H2SPPM",
            "SMOKE",
            "TVOC",
            "COPPM",
            "NH3PPM",
            "PHM",
            "O2VOL",
            "CH20PPM",
            "CO2PPM",
        }
    )

    @classmethod
    def is_valid_io_name(cls, name: str) -> bool:
        """检查是否为有效的IO口名称格式 - 优化版本"""
        if not name or not isinstance(name, str):
            return False

        # P系列IO口快速检查
        if RegexCache.is_p_io_port(name):
            return True

        # 通配符IO口检查 (如 EE*, EPF*, EF*, EI*, EV*, L* 等)
        if name.endswith("*") and len(name) >= 2:
            base_name = name[:-1]  # 移除 *
            # 检查基础名称是否为有效的IO口格式
            if base_name.isalpha() and base_name.isupper():
                return True

        # 特定通配符格式 (如 PMx, Lx)
        if name.endswith("x") and len(name) >= 2:
            base_name = name[:-1]  # 移除 x
            if base_name.isalpha() and base_name.isupper():
                return True

        # 标准IO名称检查 - O(1)时间复杂度
        return name in cls.STANDARD_IO_NAMES

    @classmethod
    def extract_mapped_ios(cls, device_mapping: Dict[str, Any]) -> Set[str]:
        """从设备映射中提取IO口列表 - 优化版本"""
        mapped_ios = set()

        # 1. 处理动态分类设备
        if device_mapping.get("dynamic", False):
            mapped_ios.update(cls._extract_dynamic_ios(device_mapping))
            return mapped_ios

        # 2. 处理版本设备
        if device_mapping.get("versioned", False):
            mapped_ios.update(cls._extract_versioned_ios(device_mapping))
            return mapped_ios

        # 3. 处理标准设备结构
        mapped_ios.update(cls._extract_standard_ios(device_mapping))
        return mapped_ios

    @classmethod
    def _extract_dynamic_ios(cls, device_mapping: Dict[str, Any]) -> Set[str]:
        """提取动态设备的IO口 - 支持复杂嵌套结构"""
        mapped_ios = set()

        for key, value in device_mapping.items():
            if key in ["dynamic", "description", "name"] or not isinstance(value, dict):
                continue

            # 处理模式配置 (如 switch_mode, climate_mode 等)
            if key.endswith("_mode"):
                mapped_ios.update(cls._extract_mode_ios(value))
            # 处理控制模式配置 (如 control_modes)
            elif key == "control_modes":
                mapped_ios.update(cls._extract_control_modes_ios(value))
            # 处理直接平台配置
            elif key in [
                "climate",
                "switch",
                "sensor",
                "binary_sensor",
                "light",
                "cover",
            ]:
                mapped_ios.update(cls._extract_platform_ios(value))
            # 处理其他配置
            else:
                # 提取io字段
                if "io" in value:
                    io_list = value["io"]
                    if isinstance(io_list, str) and cls.is_valid_io_name(io_list):
                        mapped_ios.add(io_list)
                    elif isinstance(io_list, list):
                        mapped_ios.update(filter(cls.is_valid_io_name, io_list))

                # 提取sensor_io字段
                if "sensor_io" in value and isinstance(value["sensor_io"], list):
                    mapped_ios.update(filter(cls.is_valid_io_name, value["sensor_io"]))

                # 递归处理嵌套结构
                mapped_ios.update(cls._extract_nested_ios(value))

        return mapped_ios

    @classmethod
    def _extract_mode_ios(cls, mode_config: Dict[str, Any]) -> Set[str]:
        """提取模式配置中的IO口"""
        mapped_ios = set()

        # 提取io字段
        if "io" in mode_config:
            io_list = mode_config["io"]
            if isinstance(io_list, str) and cls.is_valid_io_name(io_list):
                mapped_ios.add(io_list)
            elif isinstance(io_list, list):
                mapped_ios.update(filter(cls.is_valid_io_name, io_list))

        # 提取sensor_io字段
        if "sensor_io" in mode_config and isinstance(mode_config["sensor_io"], list):
            mapped_ios.update(filter(cls.is_valid_io_name, mode_config["sensor_io"]))

        # 提取各平台配置中的IO口
        for platform in [
            "climate",
            "switch",
            "sensor",
            "binary_sensor",
            "light",
            "cover",
        ]:
            if platform in mode_config:
                mapped_ios.update(cls._extract_platform_ios(mode_config[platform]))

        return mapped_ios

    @classmethod
    def _extract_control_modes_ios(cls, control_modes: Dict[str, Any]) -> Set[str]:
        """提取控制模式中的IO口"""
        mapped_ios = set()

        for mode_name, mode_config in control_modes.items():
            if isinstance(mode_config, dict):
                # 提取每个模式的平台IO口
                for platform in [
                    "climate",
                    "switch",
                    "sensor",
                    "binary_sensor",
                    "light",
                    "cover",
                ]:
                    if platform in mode_config:
                        mapped_ios.update(
                            cls._extract_platform_ios(mode_config[platform])
                        )

        return mapped_ios

    @classmethod
    def _extract_platform_ios(cls, platform_config: Dict[str, Any]) -> Set[str]:
        """从平台配置中提取IO口"""
        mapped_ios = set()

        if isinstance(platform_config, dict):
            for potential_io in platform_config.keys():
                if cls.is_valid_io_name(potential_io):
                    mapped_ios.add(potential_io)

        return mapped_ios

    @classmethod
    def _extract_nested_ios(cls, config: Dict[str, Any]) -> Set[str]:
        """递归提取嵌套结构中的IO口"""
        mapped_ios = set()

        for key, value in config.items():
            if isinstance(value, dict):
                # 检查是否为平台配置
                if key in [
                    "climate",
                    "switch",
                    "sensor",
                    "binary_sensor",
                    "light",
                    "cover",
                ]:
                    mapped_ios.update(cls._extract_platform_ios(value))
                # 递归处理其他嵌套字典
                else:
                    mapped_ios.update(cls._extract_nested_ios(value))

        return mapped_ios

    @classmethod
    def _extract_versioned_ios(cls, device_mapping: Dict[str, Any]) -> Set[str]:
        """提取版本设备的IO口 - 支持新的 version_modes 结构"""
        mapped_ios = set()

        # 跳过版本相关的元数据
        excluded_keys = {"versioned", "version_config", "name", "description"}

        # 处理新的 version_modes 结构
        if "version_modes" in device_mapping:
            version_modes = device_mapping["version_modes"]
            if isinstance(version_modes, dict):
                # 遍历每个版本 (V1, V2, etc.)
                for version_name, version_config in version_modes.items():
                    if isinstance(version_config, dict):
                        # 从每个版本的配置中提取IO口
                        for key, value in version_config.items():
                            if key in excluded_keys or not isinstance(value, dict):
                                continue

                            # 处理平台配置
                            if key in [
                                "climate",
                                "switch",
                                "sensor",
                                "binary_sensor",
                                "light",
                                "cover",
                            ]:
                                mapped_ios.update(cls._extract_platform_ios(value))
                            else:
                                # 递归处理其他结构
                                mapped_ios.update(cls._extract_nested_ios(value))
        else:
            # 处理旧格式的版本设备
            for key, value in device_mapping.items():
                if key in excluded_keys or not isinstance(value, dict):
                    continue

                # 直接处理平台配置
                if key in [
                    "climate",
                    "switch",
                    "sensor",
                    "binary_sensor",
                    "light",
                    "cover",
                ]:
                    mapped_ios.update(cls._extract_platform_ios(value))
                else:
                    # 可能是其他结构，递归处理
                    mapped_ios.update(cls._extract_nested_ios(value))

        return mapped_ios

    @classmethod
    def _extract_standard_ios(cls, device_mapping: Dict[str, Any]) -> Set[str]:
        """提取标准设备的IO口"""
        mapped_ios = set()

        # 处理新的详细结构
        if "platforms" in device_mapping:
            for platform_ios in device_mapping["platforms"].values():
                if isinstance(platform_ios, list):
                    mapped_ios.update(filter(cls.is_valid_io_name, platform_ios))
                elif isinstance(platform_ios, str) and cls.is_valid_io_name(
                    platform_ios
                ):
                    mapped_ios.add(platform_ios)
        else:
            # 向后兼容旧结构
            excluded_keys = {"versioned", "dynamic", "detailed_platforms", "name"}

            for platform, platform_ios in device_mapping.items():
                if platform in excluded_keys:
                    continue

                if isinstance(platform_ios, dict):
                    for potential_io in platform_ios.keys():
                        if cls.is_valid_io_name(potential_io):
                            mapped_ios.add(potential_io)
                elif isinstance(platform_ios, list):
                    mapped_ios.update(filter(cls.is_valid_io_name, platform_ios))
                elif isinstance(platform_ios, str) and cls.is_valid_io_name(
                    platform_ios
                ):
                    mapped_ios.add(platform_ios)

        return mapped_ios


class MatchingAlgorithms:
    """优化的匹配算法 - 缓存和批处理"""

    @staticmethod
    @lru_cache(maxsize=256)
    @regex_performance_monitor
    def match_wildcard_io(mapping_io: str, doc_io: str) -> bool:
        """通配符IO口匹配 - 使用RegexCache优化"""
        # 直接相等
        if mapping_io == doc_io:
            return True

        # 处理通配符匹配
        if mapping_io.endswith("*"):
            base_pattern = mapping_io[:-1]
            if doc_io.startswith(base_pattern):
                return True

        # 反向匹配：文档通配符 -> 映射具体
        if "(x取值为数字)" in doc_io or "x(x取值为数字)" in doc_io:
            base1, base2 = RegexCache.extract_base_pattern(doc_io)
            if base1:
                return any(
                    mapping_io.startswith(base) or mapping_io == base
                    for base in [base1, base2]
                    if base
                )

        return False

    @staticmethod
    def calculate_batch_match_scores(
        doc_ios_list: List[Set[str]], mapped_ios_list: List[Set[str]]
    ) -> List[Dict[str, Any]]:
        """批量计算匹配分数 - 性能优化"""
        results = []

        for doc_ios, mapped_ios in zip(doc_ios_list, mapped_ios_list):
            matched_pairs = []
            unmatched_doc = set(doc_ios)
            unmatched_mapping = set(mapped_ios)

            # 使用集合操作优化匹配过程
            for doc_io in list(unmatched_doc):
                for mapped_io in list(unmatched_mapping):
                    if MatchingAlgorithms.match_wildcard_io(mapped_io, doc_io):
                        matched_pairs.append((doc_io, mapped_io))
                        unmatched_doc.discard(doc_io)
                        unmatched_mapping.discard(mapped_io)
                        break

            # 计算匹配分数
            total_ios = len(doc_ios) + len(mapped_ios)
            match_score = (len(matched_pairs) * 2 / total_ios) if total_ios > 0 else 1.0

            results.append(
                {
                    "matched_pairs": matched_pairs,
                    "unmatched_doc": list(unmatched_doc),
                    "unmatched_mapping": list(unmatched_mapping),
                    "match_score": match_score,
                }
            )

        return results


class DeviceNameUtils:
    """设备名称处理工具"""

    # 特殊设备名称 - 使用frozenset优化查找
    # 这些设备名称虽然包含 _V 但不是版本设备，而是独立的真实设备
    SPECIAL_REAL_DEVICES = frozenset({"SL_P_V2", "SL_SC_BB_V2", "MSL_IRCTL"})
    EXCLUDED_PATTERNS = frozenset(
        {"D", "T", "IO", "RW", "NAME", "IDX", "TYPE", "Type", "val", "Bit", "F"}
    )

    @classmethod
    def is_valid_device_name(cls, device_name: str) -> bool:
        """检查是否为有效的设备名称"""
        if not device_name or len(device_name) <= 1:
            return False

        # 特殊真实设备检查
        if device_name in cls.SPECIAL_REAL_DEVICES:
            return True

        # 版本设备检查
        if RegexCache.is_version_device(device_name):
            return False

        # 排除模式检查
        if device_name in cls.EXCLUDED_PATTERNS:
            return False

        # 格式检查
        if device_name.startswith("**"):
            return False

        # 数字和标点符号检查 - 使用RegexCache优化
        if RegexCache.is_invalid_device_name(device_name):
            return False

        # 类型相关检查
        device_lower = device_name.lower()
        if any(keyword in device_lower for keyword in ["evtype", "type"]):
            return False

        # 允许的设备名格式
        return (
            device_name.startswith(("SL_", "V_", "ELIQ_", "OD_", "LSCAM:"))
            or device_name == "cam"
        )

    @classmethod
    def sort_by_official_order(
        cls, devices: List[str], official_order: Dict[str, int]
    ) -> List[str]:
        """根据官方文档章节顺序排序设备列表 - 优化版本"""

        def get_device_priority(device: str) -> int:
            # 处理版本设备
            base_device = RegexCache.remove_version_suffix(device)
            # 处理摄像头前缀设备
            if device.startswith("LSCAM:"):
                base_device = "LSCAM"
            return official_order.get(base_device, 9999)

        # 使用稳定排序算法
        return sorted(devices, key=lambda d: (get_device_priority(d), d))


class DocumentCleaner:
    """文档内容清理工具"""

    @staticmethod
    def clean_io_port(io_port: str) -> str:
        """清理IO口名称 - 移除HTML标签和Markdown格式符号"""
        if not io_port:
            return ""

        # 首先移除HTML标签
        cleaned = RegexCache.clean_io_port_name(io_port)

        # 移除Markdown格式的反引号
        cleaned = cleaned.strip("`")

        return cleaned.strip()

    @staticmethod
    def is_valid_io_content(io_port: str) -> bool:
        """检查IO口内容是否有效 - 专门为IO口设计的验证逻辑"""
        if not io_port or len(io_port) > 30:
            return False

        # 过滤表格数据说明文字 - 包含冒号和中文的描述性文字
        if ":" in io_port and any(ord(char) > 127 for char in io_port):
            return False

        # 过滤波浪号范围描述 (如 "1~3:1~3档；")
        if "~" in io_port and ("档" in io_port or "：" in io_port):
            return False

        # 过滤纯中文描述，但保留包含英文/数字/括号的合法IO口格式
        if len(io_port) > 3:
            # 检查是否只包含中文字符（排除合法的IO口格式如 Lx(x取值为数字)）
            has_english = any(char.isascii() and char.isalpha() for char in io_port)
            has_number = any(char.isdigit() for char in io_port)
            has_brackets = "(" in io_port or ")" in io_port

            # 如果包含英文字母、数字或括号，不认为是纯中文描述
            if not (has_english or has_number or has_brackets):
                if all(ord(char) > 127 for char in io_port if char.isalpha()):
                    return False

        # 过滤含有分号和中文的描述文字
        if "；" in io_port or "，" in io_port:
            return False

        # 单字母IO口是合法的 (O, T, V, H, Z, M, G, etc.)
        if len(io_port) == 1 and io_port.isalpha():
            return True

        # P系列IO口 (P1, P2, etc.)
        if re.match(r"^P\d+$", io_port):
            return True

        # 开关系列IO口 (L1, L2, L3, etc.)
        if re.match(r"^L\d+$", io_port):
            return True

        # 指示灯系列 (dark, bright, dark1, bright1, etc.)
        if re.match(r"^(dark|bright)\d*$", io_port):
            return True

        # 扩展按键系列 (eB1, eB2, etc.)
        if re.match(r"^eB\d+$", io_port):
            return True

        # 通配符IO口 (EE/EEx(x取值为数字), PMx等)
        if re.match(r"^[A-Z]+(/[A-Z]+x)?\(x取值为数字\)$", io_port):
            return True

        # 其他常见IO口模式 (PMx, etc.)
        if re.match(r"^[A-Z]+x$", io_port):
            return True

        # 复合IO口名称但需要进一步验证
        if len(io_port) >= 2:
            # 允许英文字母、数字、下划线、斜杠、括号，以及中文字符（用于通配符说明）
            if re.match(r"^[A-Za-z0-9_/()\u4e00-\u9fff]+$", io_port):
                return True

        return False
