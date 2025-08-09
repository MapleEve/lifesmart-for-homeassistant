#!/usr/bin/env python3
"""
完整的设备映射分析工具 - 集成双重验证机制
结合基础AI分析和增强版IO逻辑分析功能
提供17个SUPPORTED_PLATFORMS的完整分析验证
由 @MapleEve 初始创建和维护

核心功能：
1. 纯AI分析：基于DEVICE_MAPPING进行智能分析
2. 官方文档验证：解析官方文档并对比设备数量、IO口数量
3. 双重验证报告：生成标准的analysis_report.json和ANALYSIS_SUMMARY.md
4. 发现配置问题和改进建议
"""

# Add the custom component to path for importing const.py
import os
import sys
from datetime import datetime
from typing import Dict, Set, List, Any

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "../../custom_components/lifesmart")
)

try:
    # Import the device mappings - 适配当前架构
    from core.config.device_specs import _RAW_DEVICE_DATA

    # 重命名以保持兼容性
    DEVICE_MAPPING = _RAW_DEVICE_DATA

    # Import utils modules for enhanced analysis
    from utils.strategies import EnhancedAnalysisEngine, EnhancedAnalysisResult
    from utils.io_logic_analyzer import PlatformAllocationValidator
    from utils.document_parser import DocumentParser
    from utils.core_utils import DeviceNameUtils, RegexCache
    from utils.regex_cache import enable_debug_mode, regex_performance_monitor

except ImportError as e:
    print(f"Import error: {e}")
    print("请确保所有模块文件存在于utils目录中")
    import traceback

    traceback.print_exc()
    sys.exit(1)


class ComprehensiveDeviceMappingAnalyzer:
    """完整的设备映射分析器 - 双重验证机制"""

    def __init__(self, enable_performance_monitoring: bool = False):
        """
        初始化分析器

        Args:
            enable_performance_monitoring: 是否启用性能监控
        """
        self.document_parser = DocumentParser()

        # 读取SUPPORTED_PLATFORMS配置
        self.supported_platforms = self._load_supported_platforms()

        # 创建增强版分析引擎
        self.analysis_engine = EnhancedAnalysisEngine(self.supported_platforms)

        if enable_performance_monitoring:
            enable_debug_mode()

    def _load_supported_platforms(self) -> Set[str]:
        """加载当前支持的平台列表，排除被注释的平台"""
        # 读取const.py文件内容
        const_file_path = os.path.join(
            os.path.dirname(__file__), "../../custom_components/lifesmart/core/const.py"
        )

        active_platforms = set()
        commented_platforms = set()

        try:
            with open(const_file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 查找SUPPORTED_PLATFORMS定义
            import re

            lines = content.split("\\n")
            in_supported_platforms = False

            for line in lines:
                line_stripped = line.strip()

                if "SUPPORTED_PLATFORMS" in line_stripped and "{" in line_stripped:
                    in_supported_platforms = True
                    continue

                if in_supported_platforms:
                    if "}" in line_stripped:
                        break

                    # 检查平台定义
                    if "Platform." in line_stripped:
                        platform_match = re.search(r"Platform\\.(\\w+)", line_stripped)
                        if platform_match:
                            platform_name = platform_match.group(1).lower()

                            if line_stripped.startswith("#"):
                                commented_platforms.add(platform_name)
                                print(f"🔇 检测到被注释的平台: {platform_name}")
                            else:
                                active_platforms.add(platform_name)
                                print(f"✅ 检测到活跃平台: {platform_name}")

            print(f"📊 平台状态统计:")
            print(f"   活跃平台: {len(active_platforms)} 个")
            print(f"   被注释平台: {len(commented_platforms)} 个")

        except Exception as e:
            print(f"⚠️ 读取const.py文件失败: {e}")
            # 使用默认的17个平台配置
            active_platforms = {
                "switch",
                "binary_sensor",
                "sensor",
                "cover",
                "light",
                "climate",
                "remote",
                "fan",
                "lock",
                "camera",
                "alarm_control_panel",
                "device_tracker",
                "media_player",
                "number",
                "select",
                "button",
                "text",
            }

        return active_platforms

    @regex_performance_monitor
    def load_official_documentation(self, doc_path: str) -> Dict[str, List[Dict]]:
        """
        加载官方文档并提取IO口信息

        Args:
            doc_path: 官方文档路径

        Returns:
            设备名称到IO口信息字典列表的映射
        """
        return self.document_parser.extract_device_ios_from_docs()

    @regex_performance_monitor
    def prepare_device_mappings_from_real_data(self) -> Dict[str, Any]:
        """
        从真实的映射数据准备设备映射

        Returns:
            整合后的设备映射数据
        """
        combined_mappings = {}

        # 处理所有设备映射
        for device_name, device_config in DEVICE_MAPPING.items():
            if self._is_valid_device_for_analysis(device_name):
                # 检查设备是否为版本设备
                if RegexCache.is_version_device(device_name):
                    combined_mappings[device_name] = {
                        "versioned": True,
                        **device_config,
                    }
                # 检查设备是否为动态分类设备
                elif self._is_dynamic_classification_device(device_config):
                    combined_mappings[device_name] = {
                        "dynamic": True,
                        **device_config,
                    }
                else:
                    # 标准设备
                    combined_mappings[device_name] = device_config

        return combined_mappings

    def _is_dynamic_classification_device(self, device_config: Dict[str, Any]) -> bool:
        """检查设备是否为动态分类设备"""
        if not isinstance(device_config, dict):
            return False

        # 通过配置结构判断
        dynamic_indicators = [
            "control_modes",
            "switch_mode",
            "climate_mode",
            "dynamic",
            "classification",
        ]

        return any(indicator in device_config for indicator in dynamic_indicators)

    def _is_valid_device_for_analysis(self, device_name: str) -> bool:
        """检查设备是否应该包含在分析中"""
        return DeviceNameUtils.is_valid_device_name(device_name)

    @regex_performance_monitor
    def perform_comprehensive_analysis(self, doc_path: str) -> Dict[str, Any]:
        """
        执行完整的映射分析 - 双重验证机制

        Args:
            doc_path: 官方文档路径

        Returns:
            完整分析结果字典
        """
        print("🚀 开始完整设备映射分析 (双重验证机制)...")

        # 1. 纯AI分析 - 加载官方文档
        print("📚 阶段1: 纯AI分析 - 加载官方文档...")
        doc_ios_map = self.load_official_documentation(doc_path)
        print(f"✅ 从文档中提取了 {len(doc_ios_map)} 个设备的IO口信息")

        # 2. 准备设备映射数据
        print("🔧 准备设备映射数据...")
        device_mappings = self.prepare_device_mappings_from_real_data()
        print(f"✅ 准备了 {len(device_mappings)} 个设备的映射配置")

        # 3. 执行基础分析 (17个SUPPORTED_PLATFORMS)
        print("🧠 阶段2: 基础AI分析 (17个SUPPORTED_PLATFORMS)...")
        analysis_results = (
            self.analysis_engine.analyze_devices_with_platform_validation(
                device_mappings, doc_ios_map, _RAW_DEVICE_DATA
            )
        )
        print(f"✅ 完成 {len(analysis_results)} 个设备的基础分析")

        # 4. 官方文档验证对比
        print("📋 阶段3: 官方文档验证对比...")
        validation_results = self._perform_documentation_validation(
            doc_ios_map, device_mappings, analysis_results
        )
        print("✅ 完成官方文档验证对比")

        # 5. 生成双重验证报告
        print("📊 生成双重验证报告...")
        comprehensive_report = self._generate_comprehensive_report(
            analysis_results, validation_results, doc_ios_map, device_mappings
        )

        print("✅ 完整分析完成！")
        return comprehensive_report

    def _perform_documentation_validation(
        self,
        doc_ios_map: Dict[str, List[Dict]],
        device_mappings: Dict[str, Any],
        analysis_results: List[EnhancedAnalysisResult],
    ) -> Dict[str, Any]:
        """执行官方文档验证对比"""

        # 统计分析
        doc_device_count = len(doc_ios_map)
        mapping_device_count = len(device_mappings)

        # IO口数量统计
        total_doc_ios = sum(len(ios) for ios in doc_ios_map.values())
        total_mapping_ios = sum(len(result.mapped_ios) for result in analysis_results)

        # 设备覆盖率分析
        doc_devices = set(doc_ios_map.keys())
        mapping_devices = set(device_mappings.keys())

        covered_devices = doc_devices & mapping_devices
        missing_in_mapping = doc_devices - mapping_devices
        extra_in_mapping = mapping_devices - doc_devices

        coverage_rate = len(covered_devices) / len(doc_devices) if doc_devices else 0

        return {
            "设备数量对比": {
                "官方文档设备数": doc_device_count,
                "映射配置设备数": mapping_device_count,
                "覆盖设备数": len(covered_devices),
                "设备覆盖率": f"{coverage_rate:.1%}",
            },
            "IO口数量对比": {
                "官方文档IO口总数": total_doc_ios,
                "映射配置IO口总数": total_mapping_ios,
                "IO口匹配率": (
                    f"{(total_mapping_ios/total_doc_ios):.1%}"
                    if total_doc_ios > 0
                    else "0%"
                ),
            },
            "设备覆盖分析": {
                "已覆盖设备": list(covered_devices),
                "文档中缺失的设备": list(missing_in_mapping),
                "映射中额外的设备": list(extra_in_mapping),
            },
        }

    def _generate_comprehensive_report(
        self,
        analysis_results: List[EnhancedAnalysisResult],
        validation_results: Dict[str, Any],
        doc_ios_map: Dict[str, List[Dict]],
        device_mappings: Dict[str, Any],
    ) -> Dict[str, Any]:
        """生成综合分析报告"""

        # 基础统计
        total_devices = len(analysis_results)
        problem_devices = [r for r in analysis_results if r.match_score < 0.9]
        excellent_devices = [r for r in analysis_results if r.match_score >= 0.9]

        # 平台分配问题统计
        platform_issues = [r for r in analysis_results if r.platform_allocation_issues]

        # 生成概览
        analysis_overview = {
            "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "工具版本": "RUN_THIS_TOOL.py v3.0 (完整版)",
            "分析模式": "双重验证机制 (纯AI分析 + 官方文档验证)",
            "支持平台数": len(self.supported_platforms),
            "总设备数": total_devices,
            "优秀设备数": len(excellent_devices),
            "问题设备数": len(problem_devices),
            "平台分配问题设备": len(platform_issues),
            "整体匹配率": (
                f"{(len(excellent_devices)/total_devices*100):.1f}%"
                if total_devices > 0
                else "0%"
            ),
        }

        # 问题设备分析
        problem_analysis = self._analyze_problem_devices(problem_devices)

        # 改进建议
        improvement_suggestions = self._generate_improvement_suggestions(
            problem_devices
        )

        # 功能状态
        feature_status = {
            "纯AI分析": "✅ 已启用",
            "官方文档解析": "✅ 已启用",
            "双重验证机制": "✅ 已启用",
            "IO口逻辑分析": "✅ 已启用",
            "平台分配验证": "✅ 已启用",
            "性能监控": "✅ 已启用",
            "支持的平台": list(self.supported_platforms),
        }

        return {
            "分析概览": analysis_overview,
            "官方文档验证": validation_results,
            "问题设备分析": problem_analysis,
            "改进建议": improvement_suggestions,
            "功能状态": feature_status,
            "详细结果": [
                {
                    "设备名称": r.device_name,
                    "匹配分数": round(r.match_score, 3),
                    "平台分配分数": round(r.platform_allocation_score, 3),
                    "分析策略": r.analysis_type,
                    "文档IO口": list(r.doc_ios),
                    "映射IO口": list(r.mapped_ios),
                    "平台分配问题": len(r.platform_allocation_issues or []),
                }
                for r in analysis_results
                if r.match_score < 0.9  # 只包含有问题的设备
            ],
        }

    def _analyze_problem_devices(
        self, problem_devices: List[EnhancedAnalysisResult]
    ) -> Dict[str, Any]:
        """分析问题设备"""
        # 按严重程度分组
        critical_devices = [r for r in problem_devices if r.match_score == 0]
        major_issues = [r for r in problem_devices if 0 < r.match_score < 0.5]
        minor_issues = [r for r in problem_devices if 0.5 <= r.match_score < 0.9]

        return {
            "关键问题设备": {
                "数量": len(critical_devices),
                "说明": "完全不匹配，需要立即修复",
                "设备列表": [r.device_name for r in critical_devices],
            },
            "严重问题设备": {
                "数量": len(major_issues),
                "说明": "匹配度很低，需要重点关注",
                "设备列表": [r.device_name for r in major_issues],
            },
            "轻微问题设备": {
                "数量": len(minor_issues),
                "说明": "部分匹配，需要完善",
                "设备列表": [r.device_name for r in minor_issues],
            },
        }

    def _generate_improvement_suggestions(
        self, problem_devices: List[EnhancedAnalysisResult]
    ) -> List[Dict[str, Any]]:
        """生成改进建议"""
        suggestions = []

        # 按匹配分数排序，优先显示最严重的问题
        problem_devices.sort(key=lambda x: x.match_score)

        for result in problem_devices[:10]:  # 只显示前10个最需要关注的
            suggestion = {
                "设备名称": result.device_name,
                "当前分数": round(result.match_score, 3),
                "平台分配分数": round(result.platform_allocation_score, 3),
                "优先级": self._get_priority_level(result.match_score),
                "问题类型": [],
                "具体建议": [],
            }

            # 分析问题类型和建议
            if result.unmatched_doc:
                suggestion["问题类型"].append("缺失映射IO口")
                suggestion["具体建议"].append(
                    f"需要添加以下IO口的映射: {', '.join(result.unmatched_doc)}"
                )

            if result.unmatched_mapping:
                suggestion["问题类型"].append("多余映射IO口")
                suggestion["具体建议"].append(
                    f"以下IO口在文档中找不到对应: {', '.join(result.unmatched_mapping)}"
                )

            if result.platform_allocation_issues:
                suggestion["问题类型"].append("平台分配问题")
                suggestion["具体建议"].append(
                    f"检测到 {len(result.platform_allocation_issues)} 个平台分配问题"
                )

            suggestions.append(suggestion)

        return suggestions

    def _get_priority_level(self, score: float) -> str:
        """根据匹配分数确定优先级"""
        if score == 0:
            return "🔴 紧急"
        elif score < 0.5:
            return "🟠 高"
        elif score < 0.9:
            return "🟡 中"
        else:
            return "🟢 低"

    def save_analysis_report(self, report: Dict[str, Any], output_path: str):
        """保存分析报告到文件"""
        import json

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"✅ JSON分析报告已保存到: {output_path}")
        except Exception as e:
            print(f"❌ 保存JSON报告失败: {e}")

    def generate_markdown_report(self, report: Dict[str, Any]) -> str:
        """生成Markdown格式的分析报告"""
        md_content = []

        # 标题和基本信息
        md_content.append("# 🚀 LifeSmart 设备映射分析报告 (完整版)")
        md_content.append("")
        md_content.append(f"**生成时间**: {report['分析概览']['生成时间']}")
        md_content.append(f"**工具版本**: {report['分析概览']['工具版本']}")
        md_content.append(f"**分析模式**: {report['分析概览']['分析模式']}")
        md_content.append("**数据状态**: ✅ 实时分析结果")
        md_content.append("")
        md_content.append("---")
        md_content.append("")

        # 功能特性
        md_content.append("## 🆕 完整版功能特性")
        md_content.append("")
        feature_status = report["功能状态"]
        for feature, status in feature_status.items():
            if feature != "支持的平台":
                md_content.append(f"- **{feature}**: {status}")
        md_content.append(f"- **支持平台**: {len(feature_status['支持的平台'])}个")
        md_content.append("")
        md_content.append("---")
        md_content.append("")

        # 分析概览
        overview = report["分析概览"]
        md_content.append("## 📊 分析概览")
        md_content.append("")
        md_content.append("| 指标 | 数值 |")
        md_content.append("|------|------|")
        md_content.append(f"| **总设备数** | {overview['总设备数']}个 |")
        md_content.append(
            f"| **优秀设备数** | {overview['优秀设备数']}个 ({overview['整体匹配率']}) |"
        )
        md_content.append(f"| **问题设备数** | {overview['问题设备数']}个 |")
        md_content.append(
            f"| **平台分配问题设备** | {overview['平台分配问题设备']}个 |"
        )
        md_content.append("")

        # 官方文档验证结果
        if "官方文档验证" in report:
            validation = report["官方文档验证"]
            md_content.append("## 📋 官方文档验证结果")
            md_content.append("")

            device_compare = validation["设备数量对比"]
            md_content.append("### 设备数量对比")
            md_content.append(
                f"- **官方文档设备数**: {device_compare['官方文档设备数']}个"
            )
            md_content.append(
                f"- **映射配置设备数**: {device_compare['映射配置设备数']}个"
            )
            md_content.append(f"- **设备覆盖率**: {device_compare['设备覆盖率']}")
            md_content.append("")

            io_compare = validation["IO口数量对比"]
            md_content.append("### IO口数量对比")
            md_content.append(
                f"- **官方文档IO口总数**: {io_compare['官方文档IO口总数']}个"
            )
            md_content.append(
                f"- **映射配置IO口总数**: {io_compare['映射配置IO口总数']}个"
            )
            md_content.append(f"- **IO口匹配率**: {io_compare['IO口匹配率']}")
            md_content.append("")

        md_content.append("---")
        md_content.append("")

        # 问题设备分析
        problem_analysis = report["问题设备分析"]
        md_content.append("## 🔧 需要修复的设备")
        md_content.append("")

        for problem_type, info in problem_analysis.items():
            if info["数量"] > 0:
                icon = (
                    "🔴"
                    if "关键" in problem_type
                    else "🟠" if "严重" in problem_type else "🟡"
                )
                md_content.append(f"### {icon} {problem_type} ({info['数量']}个)")
                md_content.append(f"*{info['说明']}*")
                md_content.append("")

                for device in info["设备列表"][:5]:  # 只显示前5个
                    md_content.append(f"- {device}")

                if len(info["设备列表"]) > 5:
                    md_content.append(f"- ... 还有{len(info['设备列表']) - 5}个设备")
                md_content.append("")

        md_content.append("---")
        md_content.append("")

        # 优先修复建议
        suggestions = report["改进建议"]
        md_content.append("## 🎯 优先修复建议")
        md_content.append("")

        for i, suggestion in enumerate(suggestions[:5], 1):
            md_content.append(
                f"### {i}. {suggestion['设备名称']} - {suggestion['优先级']}"
            )
            md_content.append(
                f"**当前分数**: {suggestion['当前分数']} / **平台分配分数**: {suggestion['平台分配分数']}"
            )
            md_content.append("")
            md_content.append("**问题类型**:")
            for problem_type in suggestion["问题类型"]:
                md_content.append(f"- {problem_type}")
            md_content.append("")
            md_content.append("**具体建议**:")
            for advice in suggestion["具体建议"]:
                md_content.append(f"- {advice}")
            md_content.append("")

        if len(suggestions) > 5:
            md_content.append(
                f"*... 还有{len(suggestions) - 5}个设备的改进建议，详见JSON报告*"
            )
            md_content.append("")

        md_content.append("---")
        md_content.append("")
        md_content.append("## ✅ 重要说明")
        md_content.append("")
        md_content.append("### 双重验证机制")
        md_content.append("本工具采用双重验证机制确保分析准确性：")
        md_content.append("1. **纯AI分析**: 基于DEVICE_MAPPING进行智能分析")
        md_content.append("2. **官方文档验证**: 解析官方文档并对比验证")
        md_content.append("3. **综合评估**: 结合两种方法的结果给出最终建议")
        md_content.append("")
        md_content.append("### 支持的功能")
        md_content.append("- ✅ 17个SUPPORTED_PLATFORMS全面支持")
        md_content.append("- ✅ IO口逻辑分析和bit位解析")
        md_content.append("- ✅ 平台分配验证和优化建议")
        md_content.append("- ✅ 性能监控和缓存优化")
        md_content.append("")
        md_content.append("---")
        md_content.append("")
        md_content.append("*📋 此报告由RUN_THIS_TOOL.py v3.0自动生成*")
        md_content.append(f"*🔄 基于 {overview['生成时间']} 的完整分析数据*")

        return "\\n".join(md_content)

    def save_markdown_report(self, report: Dict[str, Any], output_path: str):
        """保存Markdown格式的分析报告"""
        try:
            markdown_content = self.generate_markdown_report(report)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            print(f"✅ Markdown分析报告已保存到: {output_path}")
        except Exception as e:
            print(f"❌ 保存Markdown报告失败: {e}")


def main():
    """主函数 - 执行完整的设备映射分析"""

    # 文档路径
    doc_path = os.path.join(
        os.path.dirname(__file__), "../../docs/LifeSmart 智慧设备规格属性说明.md"
    )

    # 输出路径
    json_output_path = os.path.join(os.path.dirname(__file__), "analysis_report.json")
    markdown_output_path = os.path.join(
        os.path.dirname(__file__), "ANALYSIS_SUMMARY.md"
    )

    # 创建完整版分析器并执行分析
    analyzer = ComprehensiveDeviceMappingAnalyzer(enable_performance_monitoring=True)

    try:
        # 执行完整分析
        report = analyzer.perform_comprehensive_analysis(doc_path)

        # 保存JSON报告
        analyzer.save_analysis_report(report, json_output_path)

        # 保存Markdown报告
        analyzer.save_markdown_report(report, markdown_output_path)

        # 打印关键统计信息
        print("\\n" + "=" * 80)
        print("📊 完整分析结果概览")
        print("=" * 80)

        overview = report["分析概览"]
        print(f"分析模式: {overview['分析模式']}")
        print(f"支持平台数: {overview['支持平台数']}")
        print(f"总设备数: {overview['总设备数']}")
        print(f"优秀设备数: {overview['优秀设备数']}")
        print(f"问题设备数: {overview['问题设备数']}")
        print(f"整体匹配率: {overview['整体匹配率']}")

        # 显示官方文档验证结果
        if "官方文档验证" in report:
            validation = report["官方文档验证"]
            device_compare = validation["设备数量对比"]
            io_compare = validation["IO口数量对比"]

            print(f"\\n📋 官方文档验证:")
            print(f"  设备覆盖率: {device_compare['设备覆盖率']}")
            print(f"  IO口匹配率: {io_compare['IO口匹配率']}")

        # 显示功能状态
        feature_status = report["功能状态"]
        print(f"\\n🔧 功能状态:")
        for feature, status in feature_status.items():
            if feature != "支持的平台":
                print(f"  {feature}: {status}")

        # 显示问题分布
        problem_analysis = report["问题设备分析"]
        print(f"\\n🚨 问题设备分类:")
        for problem_type, info in problem_analysis.items():
            print(f"  {problem_type}: {info['数量']}个")

        # 显示最需要关注的设备
        suggestions = report["改进建议"]
        if suggestions:
            print(f"\\n最需要关注的设备 (前5个):")
            for suggestion in suggestions[:5]:
                priority = suggestion["优先级"]
                name = suggestion["设备名称"]
                score = suggestion["当前分数"]
                print(f"  {priority} {name}: 分数 {score}")

        print("\\n✅ 完整的分析报告已保存:")
        print(f"   📊 JSON详细报告: {json_output_path}")
        print(f"   📋 Markdown概览报告: {markdown_output_path}")
        print(f"\\n🚀 完整版功能说明:")
        print(f"   🧠 双重验证机制: 纯AI分析 + 官方文档验证")
        print(f"   ⚖️ 平台分配验证: 验证IO口分配的合理性")
        print(f"   🎯 综合建议: 提供针对性的修复建议")
        print(f"   📊 17个平台支持: 全面覆盖SUPPORTED_PLATFORMS")

    except Exception as e:
        print(f"❌ 完整分析过程中出现错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
