#!/usr/bin/env python3
"""
纯AI文档分析器 - 零依赖版本
完全独立的NLP分析，不依赖homeassistant或其他外部模块
基于官方文档直接进行NLP分析，实时生成对比分析结果
"""

import re
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict


class PlatformType(Enum):
    """Home Assistant平台类型"""

    SWITCH = "switch"
    SENSOR = "sensor"
    BINARY_SENSOR = "binary_sensor"
    LIGHT = "light"
    COVER = "cover"
    CLIMATE = "climate"
    FAN = "fan"
    LOCK = "lock"
    CAMERA = "camera"
    REMOTE = "remote"
    NUMBER = "number"
    BUTTON = "button"
    SCENE = "scene"
    ALARM_CONTROL_PANEL = "alarm_control_panel"
    SIREN = "siren"
    VALVE = "valve"
    AIR_QUALITY = "air_quality"
    DEVICE_TRACKER = "device_tracker"


@dataclass
class IOAnalysisResult:
    """IO口分析结果"""

    io_name: str
    io_description: str
    rw_permission: str
    suggested_platform: PlatformType
    confidence: float
    reasoning: str


@dataclass
class DeviceAnalysisResult:
    """设备分析结果"""

    device_name: str
    ios: List[IOAnalysisResult]
    suggested_platforms: Set[PlatformType]
    overall_confidence: float
    analysis_notes: List[str]


class IOPlatformClassifier:
    """IO口平台分类器 - 使用规则匹配进行分类"""

    # 设备类型优先级映射 - 基于设备名称前缀
    DEVICE_TYPE_PRIORITIES = {
        "SL_SW_": {"switch": 0.9, "light": 0.8},  # 开关设备
        "SL_SF_": {"switch": 0.9, "light": 0.8},  # 流光开关设备
        "SL_SC_": {"sensor": 0.9, "binary_sensor": 0.8},  # 传感器设备
        "SL_LK_": {"lock": 0.95},  # 智能锁设备
        "SL_WH_": {"sensor": 0.9, "binary_sensor": 0.8},  # 水传感器设备
        "SL_P_": {"cover": 0.9},  # 窗帘设备
        "SL_AC_": {"climate": 0.95},  # 空调设备
        "SL_OL_": {"light": 0.95},  # 灯光设备
        "SL_RGBW_": {"light": 0.95},  # RGBW灯光设备
        "SL_LI_": {"light": 0.95},  # 智能灯设备
    }

    # 平台识别规则：关键词 -> (平台, 置信度)
    PLATFORM_RULES = {
        # Switch平台 - 开关控制
        PlatformType.SWITCH: {
            "keywords": [
                "开关",
                "控制",
                "打开",
                "关闭",
                "L1",
                "L2",
                "L3",
                "P1",
                "P2",
                "P3",
                "P4",
                "P5",
                "O",
                "Ctrl1",
                "Ctrl2",
                "Ctrl3",
                "HA1",
                "HA2",
                "HA3",
                "Status1",
                "Status2",
                "Status3",
            ],
            "io_names": ["开关", "控制"],
            "descriptions": ["打开", "关闭", "type&1==1", "type&1==0"],
            "rw_required": "RW",
            "confidence_base": 0.9,
        },
        # Sensor平台 - 传感器读取
        PlatformType.SENSOR: {
            "keywords": [
                "温度",
                "湿度",
                "电量",
                "电压",
                "功率",
                "用电量",
                "亮度",
                "光照",
                "PM2.5",
                "CO2",
                "TVOC",
                "甲醛",
                "燃气",
                "噪音",
                "T",
                "H",
                "V",
                "PM",
                "Z",
                "WA",
                "EE",
                "EP",
            ],
            "io_names": [
                "当前温度",
                "当前湿度",
                "电量",
                "电压",
                "功率",
                "用电量",
                "环境光照",
            ],
            "descriptions": [
                "温度值",
                "湿度值",
                "电压值",
                "功率值",
                "光照值",
                "val",
                "原始",
            ],
            "rw_required": "R",
            "confidence_base": 0.85,
        },
        # Binary Sensor平台 - 二进制传感器
        PlatformType.BINARY_SENSOR: {
            "keywords": [
                "移动检测",
                "门禁",
                "按键状态",
                "防拆",
                "震动",
                "警报音",
                "接近检测",
                "M",
                "G",
                "B",
                "AXS",
                "SR",
                "TR",
            ],
            "excluded_device_types": ["SL_SW_", "SL_SF_"],  # 排除开关设备
            "io_names": [
                "移动检测",
                "当前状态",
                "按键状态",
                "门禁状态",
                "警报音",
                "防拆状态",
            ],
            "descriptions": [
                "检测到移动",
                "打开",
                "关闭",
                "按下",
                "松开",
                "震动",
                "警报",
            ],
            "rw_required": "R",
            "confidence_base": 0.8,
        },
        # Light平台 - 灯光控制
        PlatformType.LIGHT: {
            "keywords": [
                "灯光",
                "颜色",
                "亮度",
                "色温",
                "RGB",
                "RGBW",
                "DYN",
                "指示灯",
                "夜灯",
                "bright",
                "dark",
                "LED",
            ],
            "io_names": [
                "RGB颜色值",
                "RGBW颜色值",
                "动态颜色值",
                "亮度控制",
                "色温控制",
            ],
            "descriptions": ["颜色值", "亮度值", "色温值", "RGB", "RGBW", "动态"],
            "rw_required": "RW",
            "confidence_base": 0.9,
        },
        # Cover平台 - 窗帘控制
        PlatformType.COVER: {
            "keywords": [
                "窗帘",
                "打开窗帘",
                "关闭窗帘",
                "停止",
                "OP",
                "CL",
                "ST",
                "DOOYA",
            ],
            "io_names": ["打开窗帘", "关闭窗帘", "停止", "窗帘状态", "窗帘控制"],
            "descriptions": ["打开窗帘", "关闭窗帘", "停止", "窗帘", "百分比"],
            "rw_required": "RW",
            "confidence_base": 0.95,
        },
        # Climate平台 - 空调/温控
        PlatformType.CLIMATE: {
            "keywords": [
                "空调",
                "温控器",
                "HVAC",
                "制冷模式",
                "制热模式",
                "除湿模式",
                "风速档位",
                "目标温度",
                "MODE",
                "tT",
                "CFG",
                "tF",
            ],
            "required_keywords": ["空调", "温控", "HVAC"],  # 必须包含的关键词
            "excluded_device_types": [
                "SL_SW_",
                "SL_SF_",
                "SL_OL_",
            ],  # 排除开关和灯光设备
            "io_names": ["模式", "风速", "目标温度", "当前温度", "系统配置"],
            "descriptions": [
                "Auto",
                "Cool",
                "Heat",
                "Fan",
                "Dry",
                "制冷",
                "制热",
                "风速",
                "温度",
            ],
            "rw_required": "RW",
            "confidence_base": 0.9,
        },
        # Lock平台 - 门锁
        PlatformType.LOCK: {
            "keywords": [
                "门锁",
                "开锁",
                "电量",
                "告警",
                "实时开锁",
                "BAT",
                "ALM",
                "EVTLO",
                "HISLK",
            ],
            "io_names": ["电量", "告警信息", "实时开锁", "最近开锁信息"],
            "descriptions": ["电量", "告警", "开锁", "密码", "指纹", "机械钥匙"],
            "rw_required": "R",
            "confidence_base": 0.95,
        },
        # Camera平台 - 摄像头
        PlatformType.CAMERA: {
            "keywords": ["摄像头", "移动检测", "摄像头状态", "cam", "CFST"],
            "io_names": ["移动检测", "摄像头状态"],
            "descriptions": ["检测到移动", "摄像头", "外接电源", "旋转云台"],
            "rw_required": "R",
            "confidence_base": 0.9,
        },
    }

    @classmethod
    def classify_io_platform(
        cls,
        io_name: str,
        io_description: str,
        rw_permission: str,
        device_name: str = "",
    ) -> List[IOAnalysisResult]:
        """分类IO口到相应平台"""
        results = []

        for platform_type, rules in cls.PLATFORM_RULES.items():
            # 检查设备类型排除规则
            excluded_types = rules.get("excluded_device_types", [])
            if any(
                device_name.startswith(excluded_type)
                for excluded_type in excluded_types
            ):
                continue

            # 检查必需关键词
            required_keywords = rules.get("required_keywords", [])
            if required_keywords:
                has_required = any(
                    keyword in io_name or keyword in io_description
                    for keyword in required_keywords
                )
                if not has_required:
                    continue

            confidence = cls._calculate_confidence(
                io_name, io_description, rw_permission, rules, device_name
            )

            if confidence > 0.12:  # 进一步降低置信度阈值
                reasoning = cls._generate_reasoning(
                    io_name, io_description, rw_permission, rules, confidence
                )

                results.append(
                    IOAnalysisResult(
                        io_name=io_name,
                        io_description=io_description,
                        rw_permission=rw_permission,
                        suggested_platform=platform_type,
                        confidence=confidence,
                        reasoning=reasoning,
                    )
                )

        # 按置信度降序排序
        results.sort(key=lambda x: x.confidence, reverse=True)
        return results

    @classmethod
    def _get_device_type_priority(cls, device_name: str) -> Dict[str, float]:
        """基于设备名称获取平台优先级"""
        for prefix, priorities in cls.DEVICE_TYPE_PRIORITIES.items():
            if device_name.startswith(prefix):
                return priorities
        return {}

    @classmethod
    def _calculate_confidence(
        cls,
        io_name: str,
        io_description: str,
        rw_permission: str,
        rules: Dict,
        device_name: str = "",
    ) -> float:
        """计算分类置信度"""
        confidence = 0.0

        # 基础置信度
        base_confidence = rules["confidence_base"]

        # 关键词匹配 - 增强版，避免短关键词误匹配
        keyword_matches = 0
        for keyword in rules["keywords"]:
            # 对短关键词（≤3字符）使用更严格的匹配规则
            if len(keyword) <= 3:
                if (
                    keyword == io_name
                    or keyword == io_description
                    or (keyword.upper() == io_name.upper() and len(io_name) <= 5)
                ):
                    keyword_matches += 1
            else:
                if (
                    keyword.lower() in io_name.lower()
                    or keyword.lower() in io_description.lower()
                ):
                    keyword_matches += 1

        if keyword_matches > 0:
            # 提高关键词匹配的权重，特别是对短IO名称
            weight = 0.5 if keyword_matches > 1 else 0.4
            confidence += (
                base_confidence
                * weight
                * min(keyword_matches / len(rules["keywords"]) * 2, 1.0)
            )

        # IO名称匹配
        name_matches = 0
        for name_pattern in rules["io_names"]:
            if name_pattern in io_name:
                name_matches += 1

        if name_matches > 0:
            confidence += (
                base_confidence * 0.3 * min(name_matches / len(rules["io_names"]), 1.0)
            )

        # 描述匹配
        desc_matches = 0
        for desc_pattern in rules["descriptions"]:
            if desc_pattern.lower() in io_description.lower():
                desc_matches += 1

        if desc_matches > 0:
            confidence += (
                base_confidence
                * 0.2
                * min(desc_matches / len(rules["descriptions"]), 1.0)
            )

        # 读写权限匹配
        if (
            rules["rw_required"] == rw_permission
            or rules["rw_required"] in rw_permission
        ):
            confidence += base_confidence * 0.1

        # 设备类型一致性调整 - 基于设备名称前缀
        if device_name:
            device_type_priorities = cls._get_device_type_priority(device_name)

            # 从rules中获取平台类型（需要从PLATFORM_RULES的key推断）
            platform_name = ""
            for platform_type, platform_rules in cls.PLATFORM_RULES.items():
                if platform_rules == rules:
                    platform_name = platform_type.value
                    break

            if platform_name in device_type_priorities:
                # 设备类型匹配，提升置信度
                confidence *= device_type_priorities[platform_name]
            elif device_type_priorities:  # 有设备类型映射但不匹配当前平台
                # 设备类型不匹配，降低置信度
                confidence *= 0.3

        return min(confidence, 1.0)

    @classmethod
    def _generate_reasoning(
        cls,
        io_name: str,
        io_description: str,
        rw_permission: str,
        rules: Dict,
        confidence: float,
    ) -> str:
        """生成分类推理说明"""
        reasons = []

        # 关键词匹配原因
        matched_keywords = [
            kw
            for kw in rules["keywords"]
            if kw.lower() in io_name.lower() or kw.lower() in io_description.lower()
        ]
        if matched_keywords:
            reasons.append(f"匹配关键词: {', '.join(matched_keywords[:3])}")

        # IO名称匹配
        matched_names = [name for name in rules["io_names"] if name in io_name]
        if matched_names:
            reasons.append(f"匹配IO名称: {', '.join(matched_names[:2])}")

        # 读写权限
        if rules["rw_required"] == rw_permission:
            reasons.append(f"读写权限匹配: {rw_permission}")

        return f"置信度{confidence:.2f}: " + " | ".join(reasons)


class DevicePlatformAnalyzer:
    """设备平台分析器 - 综合分析设备的所有IO口"""

    def __init__(self):
        self.io_classifier = IOPlatformClassifier()

    def analyze_device(
        self, device_name: str, ios_data: List[Dict]
    ) -> DeviceAnalysisResult:
        """分析设备的平台分配"""
        io_results = []
        suggested_platforms = set()
        confidence_scores = []
        analysis_notes = []

        for io_data in ios_data:
            io_name = io_data.get("name", "")
            io_description = io_data.get("description", "")
            rw_permission = io_data.get("rw", "R")

            # 分类单个IO口，传递设备名称
            classifications = self.io_classifier.classify_io_platform(
                io_name, io_description, rw_permission, device_name
            )

            if classifications:
                # 选择最高置信度的分类
                best_classification = classifications[0]
                io_results.append(best_classification)
                suggested_platforms.add(best_classification.suggested_platform)
                confidence_scores.append(best_classification.confidence)

                analysis_notes.append(
                    f"IO口'{io_name}' -> {best_classification.suggested_platform.value} "
                    f"(置信度: {best_classification.confidence:.2f})"
                )

        # 设备级别的逻辑验证
        suggested_platforms = self._validate_platform_assignment(
            device_name, suggested_platforms, ios_data
        )

        # 计算总体置信度
        overall_confidence = (
            sum(confidence_scores) / len(confidence_scores)
            if confidence_scores
            else 0.0
        )

        return DeviceAnalysisResult(
            device_name=device_name,
            ios=io_results,
            suggested_platforms=suggested_platforms,
            overall_confidence=overall_confidence,
            analysis_notes=analysis_notes,
        )

    def _validate_platform_assignment(
        self,
        device_name: str,
        suggested_platforms: Set[PlatformType],
        ios_data: List[Dict],
    ) -> Set[PlatformType]:
        """逻辑验证平台分配的合理性"""

        # 开关设备逻辑验证
        if device_name.startswith("SL_SW_") or device_name.startswith("SL_SF_"):
            # 开关设备不应该有 binary_sensor 或 climate
            invalid_platforms = {
                PlatformType.BINARY_SENSOR,
                PlatformType.CLIMATE,
                PlatformType.SENSOR,
            }
            suggested_platforms = suggested_platforms - invalid_platforms

            # 确保包含基础平台
            io_names = [io.get("name", "") for io in ios_data]
            has_switch_ios = any(
                io_name in ["L1", "L2", "L3", "P1", "P2", "P3", "O"]
                for io_name in io_names
            )
            has_light_ios = any(
                "dark" in io_name.lower()
                or "bright" in io_name.lower()
                or "RGB" in io_name.upper()
                for io_name in io_names
            )

            if has_switch_ios:
                suggested_platforms.add(PlatformType.SWITCH)
            if has_light_ios:
                suggested_platforms.add(PlatformType.LIGHT)

        # 传感器设备逻辑验证
        elif device_name.startswith("SL_SC_") or device_name.startswith("SL_WH_"):
            # 传感器设备不应该有 switch 或 light
            invalid_platforms = {PlatformType.SWITCH, PlatformType.LIGHT}
            suggested_platforms = suggested_platforms - invalid_platforms

        # 空调设备逻辑验证
        elif device_name.startswith("SL_AC_"):
            # 空调设备应该主要是climate平台
            suggested_platforms.add(PlatformType.CLIMATE)

        # 灯光设备逻辑验证
        elif device_name.startswith(("SL_OL_", "SL_LI_", "SL_RGBW_")):
            # 灯光设备应该主要是light平台
            suggested_platforms.add(PlatformType.LIGHT)
            invalid_platforms = {PlatformType.BINARY_SENSOR, PlatformType.CLIMATE}
            suggested_platforms = suggested_platforms - invalid_platforms

        return suggested_platforms


class DocumentBasedComparisonAnalyzer:
    """基于文档的对比分析器 - 零依赖版本"""

    def __init__(self):
        # 不依赖任何外部模块，直接实现简单的文档解析
        self.docs_file_path = self._get_docs_path()

    def _get_docs_path(self) -> str:
        """获取官方文档路径"""
        return os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            ),
            "docs",
            "LifeSmart 智慧设备规格属性说明.md",
        )

    def _is_valid_device_name(self, name: str) -> bool:
        """检查设备名称是否有效"""
        if not name or len(name) < 3:
            return False
        return bool(re.match(r"^[A-Z][A-Z0-9_:]+$", name))

    def analyze_and_compare(
        self, existing_allocation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析官方文档并与现有分配对比 - 零依赖版本"""
        print("🚀 开始基于官方文档的零依赖NLP分析...")

        # 1. 解析官方文档 - 自实现简单解析
        print("📖 直接解析官方文档...")
        print(f"📁 文档路径: {self.docs_file_path}")
        print(f"📂 文档文件存在: {os.path.exists(self.docs_file_path)}")

        try:
            doc_devices = self._parse_official_document()
            print(f"✅ 从官方文档提取到 {len(doc_devices)} 个设备")

            if doc_devices:
                print("📋 文档设备示例:")
                for i, (device_name, ios) in enumerate(list(doc_devices.items())[:3]):
                    print(f"   {i+1}. {device_name}: {len(ios)}个IO口")
                    if ios:
                        print(f"      首个IO: {ios[0].get('name', 'N/A')}")

        except Exception as e:
            print(f"❌ 文档解析失败: {e}")
            doc_devices = {}

        # 2. 基于官方文档进行NLP平台分析
        print("🤖 基于官方文档进行NLP平台分析...")
        ai_analysis_results = {}

        for device_name, ios_data in doc_devices.items():
            if self._is_valid_device_name(device_name) and ios_data:
                try:
                    analysis_result = self._analyze_device_platforms(
                        device_name, ios_data
                    )
                    ai_analysis_results[device_name] = analysis_result
                except Exception as e:
                    print(f"⚠️ 设备{device_name}分析失败: {e}")
                    continue

        print(f"✅ NLP分析了 {len(ai_analysis_results)} 个设备")

        # 3. 对比分析
        print("⚖️ 执行NLP分析结果与现有配置的对比...")
        comparison_results = self._compare_allocations(
            existing_allocation, ai_analysis_results
        )
        print(f"📊 生成了 {len(comparison_results)} 个设备的对比结果")

        # 4. 格式化结果
        final_results = self._format_as_agent3_results(
            comparison_results, existing_allocation, ai_analysis_results
        )

        print("✅ 基于官方文档的零依赖分析完成")
        return final_results

    def _parse_official_document(self) -> Dict[str, List[Dict]]:
        """解析官方文档 - 简化版实现"""
        if not os.path.exists(self.docs_file_path):
            print(f"❌ 官方文档文件不存在: {self.docs_file_path}")
            return {}

        try:
            with open(self.docs_file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"❌ 读取官方文档失败: {e}")
            return {}

        device_ios = {}
        lines = content.split("\n")
        current_devices = []
        table_lines_found = 0

        # 简单的表格解析
        for line_no, line in enumerate(lines, 1):
            line = line.strip()

            # 跳过第三方设备部分（标题行）
            if "第三方设备" in line and ("##" in line or "###" in line):
                break

            # 解析表格行
            if line.startswith("|") and "|" in line[1:-1]:
                # 跳过分隔符行（包含----）
                if "----" in line:
                    continue

                table_lines_found += 1
                columns = [col.strip() for col in line.split("|")[1:-1]]

                # 跳过表头行
                if len(columns) >= 5 and (
                    "Devtype" in columns[0] or "**Devtype" in columns[0]
                ):
                    print(f"📝 跳过表头行 {line_no}: {columns[0]}")
                    continue

                if len(columns) >= 5:
                    device_col = columns[0]
                    io_port = columns[1]
                    io_name = columns[2]
                    description = columns[3]
                    permissions = columns[4]

                    # 提取设备名称 - 支持多行设备名
                    if device_col:
                        # 处理HTML换行标签和多个设备名
                        device_names_str = device_col.replace("<br/>", "\n")
                        device_names = device_names_str.split("\n")
                        extracted_devices = []

                        for device_line in device_names:
                            device_matches = re.findall(
                                r"`([A-Z][A-Z0-9_:]+)`", device_line
                            )
                            extracted_devices.extend(device_matches)

                        if extracted_devices:
                            current_devices = extracted_devices
                            for device_name in current_devices:
                                if device_name not in device_ios:
                                    device_ios[device_name] = []
                            print(f"📝 行{line_no}: 提取设备 {current_devices}")

                    # 添加IO口信息到所有当前设备
                    if current_devices and io_port and io_name:
                        # 去除IO端口的反引号
                        clean_io_port = io_port.replace("`", "")

                        for device_name in current_devices:
                            io_info = {
                                "name": clean_io_port,
                                "description": description,
                                "rw": permissions,
                                "io_type": io_name,
                            }
                            device_ios[device_name].append(io_info)
                        print(
                            f"📝 行{line_no}: 添加IO {clean_io_port}({io_name}) 到 {len(current_devices)} 个设备"
                        )

        print(f"📝 总计处理表格行: {table_lines_found}")
        return device_ios

    def _analyze_device_platforms(
        self, device_name: str, ios_data: List[Dict]
    ) -> Dict[str, Any]:
        """基于NLP规则分析设备平台分配"""
        platform_suggestions = set()
        ios_analysis = []

        for io_data in ios_data:
            io_name = io_data.get("name", "")
            io_description = io_data.get("description", "")
            rw_permission = io_data.get("rw", "R")

            # NLP规则分析，传递设备名称
            suggested_platforms = self._classify_io_platform(
                io_name, io_description, rw_permission, device_name
            )

            if suggested_platforms:
                platform_suggestions.update(
                    [p["platform"] for p in suggested_platforms]
                )
                ios_analysis.extend(suggested_platforms)

        return {
            "platforms": list(platform_suggestions),
            "confidence": 0.8,  # 基于规则的固定置信度
            "ios": ios_analysis,
        }

    def _classify_io_platform(
        self,
        io_name: str,
        io_description: str,
        rw_permission: str,
        device_name: str = "",
    ) -> List[Dict]:
        """NLP规则分类IO口到平台"""
        results = []

        # 设备类型排除检查
        def should_exclude_platform(platform: str) -> bool:
            """检查是否应该排除某个平台"""
            if not device_name:
                return False

            # 开关设备不应分类为binary_sensor或climate
            if device_name.startswith(("SL_SW_", "SL_SF_")):
                return platform in ["binary_sensor", "climate", "sensor"]

            # 灯光设备不应分类为binary_sensor或climate
            if device_name.startswith(("SL_OL_", "SL_LI_", "SL_RGBW_")):
                return platform in ["binary_sensor", "climate"]

            return False

        # 开关平台规则
        if any(
            keyword in io_name.upper() or keyword in io_description
            for keyword in ["L1", "L2", "L3", "P1", "P2", "P3", "O", "开关", "控制"]
        ):
            if rw_permission in ["RW", "W"] and not should_exclude_platform("switch"):
                results.append(
                    {
                        "name": io_name,
                        "platform": "switch",
                        "confidence": 0.9,
                        "reasoning": f"开关控制IO口: {io_name}, RW权限",
                    }
                )

        # 传感器平台规则 - 更精确的匹配
        if any(
            keyword in io_name.upper() or keyword in io_description
            for keyword in ["T", "H", "V", "PM", "温度值", "湿度值", "电量", "电压值"]
        ):
            if rw_permission in ["R", "RW"] and not should_exclude_platform("sensor"):
                results.append(
                    {
                        "name": io_name,
                        "platform": "sensor",
                        "confidence": 0.85,
                        "reasoning": f"传感器IO口: {io_name}, 读取权限",
                    }
                )

        # 二进制传感器规则 - 更精确的关键词
        if any(
            keyword in io_name.upper() or keyword in io_description
            for keyword in ["M", "G", "B", "移动检测", "门禁", "按键状态", "防拆"]
        ):
            if not should_exclude_platform("binary_sensor"):
                results.append(
                    {
                        "name": io_name,
                        "platform": "binary_sensor",
                        "confidence": 0.8,
                        "reasoning": f"二进制传感器IO口: {io_name}",
                    }
                )

        # 灯光平台规则 - 支持bright/dark等开关指示灯
        if any(
            keyword in io_name.upper() or keyword in io_description.upper()
            for keyword in ["RGB", "RGBW", "DYN", "BRIGHT", "DARK", "颜色", "亮度"]
        ):
            if rw_permission in ["RW", "W"] and not should_exclude_platform("light"):
                results.append(
                    {
                        "name": io_name,
                        "platform": "light",
                        "confidence": 0.9,
                        "reasoning": f"灯光控制IO口: {io_name}",
                    }
                )

        # 窗帘平台规则
        if any(
            keyword in io_name.upper() or keyword in io_description
            for keyword in ["OP", "CL", "ST", "窗帘", "DOOYA"]
        ):
            if not should_exclude_platform("cover"):
                results.append(
                    {
                        "name": io_name,
                        "platform": "cover",
                        "confidence": 0.95,
                        "reasoning": f"窗帘控制IO口: {io_name}",
                    }
                )

        # 空调平台规则 - 更严格的匹配
        if any(
            keyword in io_name.upper() or keyword in io_description
            for keyword in ["MODE", "tT", "CFG", "空调模式", "风速档位", "目标温度"]
        ):
            if not should_exclude_platform("climate"):
                # 额外检查：必须是真正的空调设备
                if device_name.startswith("SL_AC_") or any(
                    ac_keyword in io_description
                    for ac_keyword in ["空调", "制冷", "制热", "HVAC"]
                ):
                    results.append(
                        {
                            "name": io_name,
                            "platform": "climate",
                            "confidence": 0.9,
                            "reasoning": f"空调控制IO口: {io_name}",
                        }
                    )

        return results

    def _compare_allocations(
        self, existing_allocation: Dict[str, Any], ai_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """对比现有分配和AI分析结果"""
        comparison_results = []

        # 获取所有设备名称
        existing_devices = set(existing_allocation.get("devices", {}).keys())
        ai_devices = set(ai_analysis.keys())
        all_devices = existing_devices | ai_devices

        for device_name in all_devices:
            existing_data = existing_allocation.get("devices", {}).get(device_name)
            ai_data = ai_analysis.get(device_name)

            comparison = self._analyze_device_differences(
                device_name, existing_data, ai_data
            )
            comparison_results.append(comparison)

        return comparison_results

    def _analyze_device_differences(
        self, device_name: str, existing_data: Dict, ai_data: Dict
    ) -> Dict[str, Any]:
        """分析单个设备的差异"""

        # 获取平台信息
        existing_platforms = (
            set(existing_data.get("platforms", [])) if existing_data else set()
        )
        ai_platforms = set(ai_data.get("platforms", [])) if ai_data else set()

        # 计算匹配类型和置信度
        if not existing_data and ai_data:
            match_type = "AI独有建议"
            confidence = ai_data.get("confidence", 0.5)
            differences = ["设备仅存在于AI分析中"]
        elif existing_data and not ai_data:
            match_type = "现有独有"
            confidence = 0.3
            differences = ["设备仅存在于现有配置中"]
        elif existing_platforms == ai_platforms:
            match_type = "完全匹配"
            confidence = ai_data.get("confidence", 0.9)
            differences = []
        elif existing_platforms & ai_platforms:  # 有交集
            match_type = "部分匹配"
            confidence = ai_data.get("confidence", 0.7) * 0.8
            differences = [
                f"平台差异: 现有{existing_platforms} vs AI建议{ai_platforms}"
            ]
        else:  # 完全不同
            match_type = "平台不匹配"
            confidence = ai_data.get("confidence", 0.6) * 0.5
            differences = [
                f"平台完全不匹配: 现有{existing_platforms} vs AI建议{ai_platforms}"
            ]

        # 分析IO口差异
        if existing_data and ai_data:
            existing_ios = set(
                io.get("name", "") for io in existing_data.get("ios", [])
            )
            ai_ios = set(io.get("name", "") for io in ai_data.get("ios", []))

            if existing_ios != ai_ios:
                missing_in_existing = ai_ios - existing_ios
                extra_in_existing = existing_ios - ai_ios

                if missing_in_existing:
                    differences.append(f"现有配置缺少IO口: {list(missing_in_existing)}")
                if extra_in_existing:
                    differences.append(f"现有配置多余IO口: {list(extra_in_existing)}")

        return {
            "device_name": device_name,
            "match_type": match_type,
            "confidence_score": round(confidence, 3),
            "differences": differences,
            "existing_platforms": list(existing_platforms),
            "ai_platforms": list(ai_platforms),
            "existing_ios": (
                [io.get("name", "") for io in existing_data.get("ios", [])]
                if existing_data
                else []
            ),
            "ai_ios": (
                [io.get("name", "") for io in ai_data.get("ios", [])] if ai_data else []
            ),
        }

    def _format_as_agent3_results(
        self,
        comparison_results: List[Dict],
        existing_allocation: Dict,
        ai_analysis: Dict,
    ) -> Dict[str, Any]:
        """格式化为Agent3兼容的结果"""

        # 统计匹配分布
        match_distribution = defaultdict(int)
        perfect_matches = 0

        for result in comparison_results:
            match_type = result["match_type"]
            if match_type == "完全匹配":
                match_distribution["perfect_match"] += 1
                perfect_matches += 1
            elif match_type == "部分匹配":
                match_distribution["partial_match"] += 1
            elif match_type == "平台不匹配":
                match_distribution["platform_mismatch"] += 1
            elif match_type == "AI独有建议":
                match_distribution["ai_only"] += 1
            elif match_type == "现有独有":
                match_distribution["existing_only"] += 1

        total_devices = len(comparison_results)
        perfect_match_rate = (
            (perfect_matches / total_devices * 100) if total_devices > 0 else 0
        )

        # 生成Agent3兼容格式
        agent3_compatible = {
            "analysis_metadata": {
                "tool": "Pure AI Document Analyzer",
                "version": "1.0",
                "timestamp": datetime.now().isoformat(),
                "analysis_flow": "DocumentParser → AI Analysis → Real-time Comparison",
            },
            "agent1_results": {
                "summary": f"提取了{len(existing_allocation.get('devices', {}))}个设备的现有配置",
                "total_devices": len(existing_allocation.get("devices", {})),
                "total_ios": sum(
                    len(d.get("ios", []))
                    for d in existing_allocation.get("devices", {}).values()
                ),
            },
            "agent2_results": {
                "summary": f"AI分析了{len(ai_analysis)}个设备",
                "total_devices": len(ai_analysis),
                "total_ios": sum(len(d.get("ios", [])) for d in ai_analysis.values()),
            },
            "agent3_results": {
                "metadata": {
                    "agent": "Pure AI Document Analyzer",
                    "task": "Real-time comparison analysis between existing config and AI suggestions",
                    "timestamp": datetime.now().isoformat(),
                    "total_devices": total_devices,
                    "comparison_count": total_devices,
                },
                "overall_statistics": {
                    "total_devices": total_devices,
                    "perfect_match_rate": round(perfect_match_rate, 1),
                    "match_distribution": dict(match_distribution),
                },
                "comparison_results": comparison_results,
            },
        }

        return agent3_compatible


class PureAIAnalyzerFactory:
    """纯AI分析器工厂"""

    @staticmethod
    def create_document_analyzer() -> DocumentBasedComparisonAnalyzer:
        """创建基于文档的分析器"""
        return DocumentBasedComparisonAnalyzer()

    @staticmethod
    def create_device_analyzer() -> DevicePlatformAnalyzer:
        """创建设备平台分析器"""
        return DevicePlatformAnalyzer()

    @staticmethod
    def create_io_classifier() -> IOPlatformClassifier:
        """创建IO分类器"""
        return IOPlatformClassifier()


# 主要导出接口
def analyze_document_realtime(existing_allocation: Dict[str, Any]) -> Dict[str, Any]:
    """
    实时分析官方文档并生成Agent3兼容的结果

    Args:
        existing_allocation: 现有设备分配数据

    Returns:
        Agent3兼容格式的分析结果
    """
    analyzer = DocumentBasedComparisonAnalyzer()
    return analyzer.analyze_and_compare(existing_allocation)


# 测试和验证函数
def test_io_classification():
    """测试IO分类功能"""
    classifier = IOPlatformClassifier()

    test_cases = [
        ("L1", "开关控制，type&1==1表示打开", "RW"),
        ("T", "当前环境温度，温度值*10", "R"),
        ("M", "移动检测，0：没有检测到移动，1：有检测到移动", "R"),
        ("RGBW", "RGBW颜色值，bit0~bit7:Blue", "RW"),
        ("OP", "打开窗帘，type&1==1表示打开窗帘", "RW"),
    ]

    for io_name, description, rw in test_cases:
        results = classifier.classify_io_platform(io_name, description, rw)
        print(f"\nIO口: {io_name}")
        print(f"描述: {description}")
        print(f"权限: {rw}")
        print("分类结果:")
        for result in results[:2]:  # 显示前2个最佳匹配
            print(
                f"  {result.suggested_platform.value}: {result.confidence:.2f} - {result.reasoning}"
            )


if __name__ == "__main__":
    # 运行测试
    print("🧪 测试IO分类功能...")
    test_io_classification()
