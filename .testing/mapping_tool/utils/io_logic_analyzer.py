#!/usr/bin/env python3
"""
IO口逻辑分析器 - 增强版设备映射分析
用于验证raw data中IO口的平台分配是否合理

主要功能：
1. 解析detailed_description中的bit位逻辑
2. 识别IO口实际能支持的HA平台类型
3. 验证当前平台分配的合理性
4. 识别过度分配或分配不足的问题
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Set, Any


class LogicPattern(Enum):
    """IO口逻辑模式枚举"""

    TYPE_BIT = "type_bit"  # type&1==1 类型的bit位逻辑
    VAL_RANGE = "val_range"  # val值范围逻辑
    TYPE_VAL_COMBINED = "type_val_combined"  # type和val组合逻辑
    EVENT_TRIGGER = "event_trigger"  # 事件触发逻辑
    STATE_REPORT = "state_report"  # 状态上报逻辑
    COMPLEX_BIT = "complex_bit"  # 复杂bit位组合
    UNKNOWN = "unknown"


@dataclass
class IOCapability:
    """IO口能力描述"""

    io_name: str
    logic_patterns: List[LogicPattern]
    supported_platforms: Set[str]
    read_write: str
    data_type: str
    reason: str  # 支持该平台的原因


@dataclass
class PlatformAllocationIssue:
    """平台分配问题"""

    device_name: str
    io_name: str
    issue_type: str  # "over_allocation", "under_allocation", "misallocation"
    current_platforms: Set[str]
    recommended_platforms: Set[str]
    reason: str
    severity: str  # "critical", "major", "minor"


class IOLogicAnalyzer:
    """IO口逻辑分析器"""

    def __init__(self):
        # 逻辑模式识别的正则表达式
        self.pattern_regexes = {
            LogicPattern.TYPE_BIT: [
                re.compile(r"type\s*&\s*(\d+)\s*==\s*(\d+)", re.IGNORECASE),
                re.compile(r"type\s*的值定义.*?type\s*&\s*(\d+)", re.IGNORECASE),
            ],
            LogicPattern.VAL_RANGE: [
                re.compile(r"val\s*值.*?范围.*?\[(\d+)[，,]\s*(\d+)\]", re.IGNORECASE),
                re.compile(r"val.*?(\d+)[：:][^；]*；", re.IGNORECASE),
                re.compile(r"val\s*的值定义", re.IGNORECASE),
            ],
            LogicPattern.EVENT_TRIGGER: [
                re.compile(r"(事件产生|事件消失|按键事件|触发事件)", re.IGNORECASE),
                re.compile(r"(单击|双击|长按|短按)事件", re.IGNORECASE),
            ],
            LogicPattern.STATE_REPORT: [
                re.compile(r"(状态|温度|湿度|电量|电压).*?(值|百分比)", re.IGNORECASE),
                re.compile(r"表示.*(当前|剩余|实时)", re.IGNORECASE),
            ],
            LogicPattern.COMPLEX_BIT: [
                re.compile(r"bit\s*(\d+)[~-](\d+)", re.IGNORECASE),
                re.compile(r"第\s*(\d+)\s*位", re.IGNORECASE),
            ],
        }

        # 平台能力映射
        self.platform_capabilities = {
            "switch": {
                "keywords": ["开关", "打开", "关闭", "控制"],
                "logic_patterns": [
                    LogicPattern.TYPE_BIT,
                    LogicPattern.TYPE_VAL_COMBINED,
                ],
                "rw_required": "RW",
            },
            "binary_sensor": {
                "keywords": ["状态", "检测", "感应", "事件"],
                "logic_patterns": [
                    LogicPattern.EVENT_TRIGGER,
                    LogicPattern.STATE_REPORT,
                ],
                "rw_required": "R",
            },
            "sensor": {
                "keywords": ["温度", "湿度", "电量", "功率", "电压", "数值", "百分比"],
                "logic_patterns": [LogicPattern.STATE_REPORT, LogicPattern.VAL_RANGE],
                "rw_required": "R",
            },
            "light": {
                "keywords": ["灯", "亮度", "颜色", "RGB", "RGBW", "色温"],
                "logic_patterns": [LogicPattern.TYPE_BIT, LogicPattern.VAL_RANGE],
                "rw_required": "RW",
            },
            "cover": {
                "keywords": ["窗帘", "打开", "关闭", "停止", "位置"],
                "logic_patterns": [LogicPattern.TYPE_BIT, LogicPattern.VAL_RANGE],
                "rw_required": "RW",
            },
            "climate": {
                "keywords": ["温控", "空调", "模式", "温度", "风速"],
                "logic_patterns": [
                    LogicPattern.TYPE_VAL_COMBINED,
                    LogicPattern.VAL_RANGE,
                ],
                "rw_required": "RW",
            },
            "button": {
                "keywords": ["按键", "按钮"],
                "logic_patterns": [LogicPattern.EVENT_TRIGGER],
                "rw_required": "R",
            },
        }

    def analyze_io_logic(self, detailed_description: str) -> List[LogicPattern]:
        """分析IO口的逻辑模式"""
        if not detailed_description:
            return [LogicPattern.UNKNOWN]

        patterns = []

        for pattern_type, regexes in self.pattern_regexes.items():
            for regex in regexes:
                if regex.search(detailed_description):
                    patterns.append(pattern_type)
                    break

        return patterns if patterns else [LogicPattern.UNKNOWN]

    def infer_supported_platforms(self, io_config: Dict[str, Any]) -> IOCapability:
        """推断IO口支持的平台"""
        io_name = io_config.get("name", "")
        description = io_config.get("description", "")
        detailed_description = io_config.get("detailed_description", "")
        rw = io_config.get("rw", "")
        data_type = io_config.get("data_type", "")

        # 分析逻辑模式
        logic_patterns = self.analyze_io_logic(detailed_description)

        # 推断支持的平台
        supported_platforms = set()
        reason_parts = []

        # 基于描述内容推断
        full_text = f"{description} {detailed_description}".lower()

        for platform, config in self.platform_capabilities.items():
            # 检查关键词
            keyword_match = any(keyword in full_text for keyword in config["keywords"])

            # 检查逻辑模式
            pattern_match = any(
                pattern in logic_patterns for pattern in config["logic_patterns"]
            )

            # 检查读写权限
            rw_match = config["rw_required"] in rw or not config["rw_required"]

            if keyword_match and pattern_match and rw_match:
                supported_platforms.add(platform)
                reason_parts.append(f"{platform}: 关键词+逻辑模式+权限匹配")
            elif keyword_match and rw_match:
                supported_platforms.add(platform)
                reason_parts.append(f"{platform}: 关键词+权限匹配")

        # 特殊处理某些情况
        if not supported_platforms:
            # 如果没有明确匹配，基于数据类型推断
            if "binary" in data_type.lower():
                if rw == "RW":
                    supported_platforms.add("switch")
                else:
                    supported_platforms.add("binary_sensor")
                reason_parts.append("基于binary数据类型推断")
            elif any(word in full_text for word in ["温度", "湿度", "电量", "功率"]):
                supported_platforms.add("sensor")
                reason_parts.append("基于传感器关键词推断")

        return IOCapability(
            io_name=io_name,
            logic_patterns=logic_patterns,
            supported_platforms=supported_platforms,
            read_write=rw,
            data_type=data_type,
            reason="; ".join(reason_parts),
        )

    def validate_platform_allocation(
        self,
        device_name: str,
        device_config: Dict[str, Any],
        supported_platforms: Set[str],
    ) -> List[PlatformAllocationIssue]:
        """验证设备的平台分配是否合理"""
        issues = []

        # 分析每个IO口的平台分配
        io_platform_map = {}

        # 提取当前分配到各平台的IO口
        for platform in supported_platforms:
            if platform in device_config:
                platform_config = device_config[platform]
                if isinstance(platform_config, dict):
                    for io_name in platform_config.keys():
                        if io_name not in io_platform_map:
                            io_platform_map[io_name] = set()
                        io_platform_map[io_name].add(platform)

        # 验证每个IO口
        for platform in supported_platforms:
            if platform in device_config:
                platform_config = device_config[platform]
                if isinstance(platform_config, dict):
                    for io_name, io_config in platform_config.items():
                        # 分析IO口能力
                        capability = self.infer_supported_platforms(
                            {
                                "name": io_name,
                                "description": io_config.get("description", ""),
                                "detailed_description": io_config.get(
                                    "detailed_description", ""
                                ),
                                "rw": io_config.get("rw", ""),
                                "data_type": io_config.get("data_type", ""),
                            }
                        )

                        current_platforms = io_platform_map.get(io_name, set())
                        recommended_platforms = capability.supported_platforms

                        # 检查分配问题
                        if not recommended_platforms:
                            continue

                        # 过度分配：分配了不支持的平台
                        over_allocated = current_platforms - recommended_platforms
                        if over_allocated:
                            issues.append(
                                PlatformAllocationIssue(
                                    device_name=device_name,
                                    io_name=io_name,
                                    issue_type="over_allocation",
                                    current_platforms=current_platforms,
                                    recommended_platforms=recommended_platforms,
                                    reason=f"IO口 {io_name} 被分配到不支持的平台: {', '.join(over_allocated)}",
                                    severity="major",
                                )
                            )

                        # 分配不足：应该支持但未分配的平台
                        under_allocated = recommended_platforms - current_platforms
                        if under_allocated:
                            issues.append(
                                PlatformAllocationIssue(
                                    device_name=device_name,
                                    io_name=io_name,
                                    issue_type="under_allocation",
                                    current_platforms=current_platforms,
                                    recommended_platforms=recommended_platforms,
                                    reason=f"IO口 {io_name} 应该支持但未分配的平台: {', '.join(under_allocated)}",
                                    severity="minor",
                                )
                            )

        return issues

    def analyze_bit_logic_capabilities(
        self, detailed_description: str
    ) -> Dict[str, Any]:
        """分析bit位逻辑的多平台支持能力"""
        analysis = {
            "has_bit_logic": False,
            "bit_patterns": [],
            "multi_platform_capable": False,
            "platforms": set(),
        }

        if not detailed_description:
            return analysis

        # 检查是否包含bit位逻辑
        bit_patterns = []

        # type&1 模式
        type_bit_matches = re.findall(
            r"type\s*&\s*(\d+)\s*==\s*(\d+)", detailed_description, re.IGNORECASE
        )
        if type_bit_matches:
            analysis["has_bit_logic"] = True
            for mask, value in type_bit_matches:
                bit_patterns.append(f"type&{mask}=={value}")

        # val值定义模式
        val_patterns = re.findall(r"val.*?(\d+)[：:]([^；]*)", detailed_description)
        if val_patterns:
            for value, desc in val_patterns:
                bit_patterns.append(f"val={value}: {desc}")

        analysis["bit_patterns"] = bit_patterns

        # 判断是否支持多平台
        if len(bit_patterns) > 1:
            analysis["multi_platform_capable"] = True

            # 基于bit位逻辑推断可能的平台组合
            desc_lower = detailed_description.lower()
            if "事件" in desc_lower and ("产生" in desc_lower or "消失" in desc_lower):
                analysis["platforms"].add("binary_sensor")
            if any(word in desc_lower for word in ["单击", "双击", "长按"]):
                analysis["platforms"].add("button")
            if any(word in desc_lower for word in ["打开", "关闭"]):
                analysis["platforms"].add("switch")

        return analysis


class PlatformAllocationValidator:
    """平台分配验证器"""

    def __init__(self, supported_platforms: Set[str]):
        self.supported_platforms = supported_platforms
        self.analyzer = IOLogicAnalyzer()

    def check_commented_platforms(self, const_file_content: str) -> Set[str]:
        """检查被注释的平台"""
        commented_platforms = set()

        # 查找SUPPORTED_PLATFORMS定义
        lines = const_file_content.split("\n")
        in_supported_platforms = False

        for line in lines:
            line = line.strip()
            if "SUPPORTED_PLATFORMS" in line and "{" in line:
                in_supported_platforms = True
                continue

            if in_supported_platforms:
                if "}" in line:
                    break

                # 检查被注释的平台
                if line.startswith("#") and "Platform." in line:
                    platform_match = re.search(r"Platform\.(\w+)", line)
                    if platform_match:
                        platform = platform_match.group(1).lower()
                        commented_platforms.add(platform)

        return commented_platforms

    def validate_device_allocation(
        self, device_name: str, device_config: Dict[str, Any]
    ) -> List[PlatformAllocationIssue]:
        """验证单个设备的平台分配"""
        active_platforms = self.supported_platforms
        return self.analyzer.validate_platform_allocation(
            device_name, device_config, active_platforms
        )

    def generate_allocation_report(
        self, devices_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成平台分配验证报告"""
        all_issues = []
        device_summaries = {}

        for device_name, device_config in devices_data.items():
            issues = self.validate_device_allocation(device_name, device_config)
            all_issues.extend(issues)

            if issues:
                device_summaries[device_name] = {
                    "issue_count": len(issues),
                    "critical_issues": len(
                        [i for i in issues if i.severity == "critical"]
                    ),
                    "major_issues": len([i for i in issues if i.severity == "major"]),
                    "minor_issues": len([i for i in issues if i.severity == "minor"]),
                    "issues": [
                        {
                            "io_name": issue.io_name,
                            "type": issue.issue_type,
                            "severity": issue.severity,
                            "current_platforms": list(issue.current_platforms),
                            "recommended_platforms": list(issue.recommended_platforms),
                            "reason": issue.reason,
                        }
                        for issue in issues
                    ],
                }

        # 统计信息
        issue_types = {}
        severity_counts = {}

        for issue in all_issues:
            issue_types[issue.issue_type] = issue_types.get(issue.issue_type, 0) + 1
            severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1

        return {
            "summary": {
                "total_devices_analyzed": len(devices_data),
                "devices_with_issues": len(device_summaries),
                "total_issues": len(all_issues),
                "issue_types": issue_types,
                "severity_distribution": severity_counts,
            },
            "device_details": device_summaries,
            "recommendations": self._generate_recommendations(all_issues),
        }

    def _generate_recommendations(
        self, issues: List[PlatformAllocationIssue]
    ) -> List[Dict[str, Any]]:
        """生成修复建议"""
        recommendations = []

        # 按严重程度分组
        critical_issues = [i for i in issues if i.severity == "critical"]
        major_issues = [i for i in issues if i.severity == "major"]

        if critical_issues:
            recommendations.append(
                {
                    "priority": "🔴 紧急",
                    "title": "关键平台分配错误",
                    "description": f"发现 {len(critical_issues)} 个关键问题，需要立即修复",
                    "action": "检查并修正错误的平台分配",
                }
            )

        if major_issues:
            recommendations.append(
                {
                    "priority": "🟠 重要",
                    "title": "主要平台分配问题",
                    "description": f"发现 {len(major_issues)} 个主要问题，建议优先处理",
                    "action": "审查过度分配的平台，移除不合适的分配",
                }
            )

        # 常见问题模式分析
        over_allocation_count = len(
            [i for i in issues if i.issue_type == "over_allocation"]
        )
        under_allocation_count = len(
            [i for i in issues if i.issue_type == "under_allocation"]
        )

        if over_allocation_count > under_allocation_count:
            recommendations.append(
                {
                    "priority": "🟡 建议",
                    "title": "减少过度分配",
                    "description": "检测到较多IO口被分配到不支持的平台",
                    "action": "基于IO口的detailed_description审查平台分配的合理性",
                }
            )

        return recommendations
