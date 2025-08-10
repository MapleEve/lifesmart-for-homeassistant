#!/usr/bin/env python3
"""
映射对比器 - 独立AI分析结果 vs 项目mapping配置
提供真正独立的对比基准，发现有意义的差异
"""

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Any

# 添加项目路径以导入设备配置
project_root = (
    Path(__file__).parent.parent.parent.parent / "custom_components/lifesmart"
)
sys.path.insert(0, str(project_root))

# 尝试多种方式导入项目配置
PROJECT_DATA_AVAILABLE = False
DEVICE_SPECS_DATA = {}

try:
    # 方式1: 直接导入
    from core.config.device_specs import DEVICE_SPECS_DATA

    PROJECT_DATA_AVAILABLE = True
except ImportError:
    try:
        # 方式2: 通过mapping.py导入
        from core.config.mapping import DEVICE_MAPPING

        DEVICE_SPECS_DATA = DEVICE_MAPPING
        PROJECT_DATA_AVAILABLE = True
    except ImportError:
        try:
            # 方式3: 直接读取文件
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "device_specs", str(project_root / "core/config/device_specs.py")
            )
            if spec and spec.loader:
                device_specs_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(device_specs_module)
                if hasattr(device_specs_module, "DEVICE_SPECS_DATA"):
                    DEVICE_SPECS_DATA = device_specs_module.DEVICE_SPECS_DATA
                    PROJECT_DATA_AVAILABLE = True
                elif hasattr(device_specs_module, "_RAW_DEVICE_DATA"):
                    DEVICE_SPECS_DATA = device_specs_module._RAW_DEVICE_DATA
                    PROJECT_DATA_AVAILABLE = True
        except Exception as e:
            print(f"导入项目配置时出错: {e}")


@dataclass
class ComparisonResult:
    """对比结果"""

    device_type: str
    io_name: str
    ai_recommendation: List[str]
    project_actual: List[str]
    difference_type: str  # "major", "minor", "missing_ai", "missing_project"
    ai_confidence: float
    ai_reasoning: str
    impact_score: float  # 影响分数 (0-1)


class MappingComparator:
    """映射对比器"""

    def __init__(self):
        self.ha_platform_priority = {
            # HA平台优先级权重 - 用于计算影响分数
            "switch": 0.9,  # 开关是最基础的控制
            "light": 0.85,  # 灯光控制很重要
            "sensor": 0.8,  # 传感器数据重要
            "binary_sensor": 0.75,  # 状态检测重要
            "climate": 0.7,  # 空调控制
            "cover": 0.65,  # 窗帘控制
            "fan": 0.6,  # 风扇控制
            "lock": 0.55,  # 锁具控制
            "number": 0.5,  # 数值设置
            "button": 0.45,  # 按钮操作
            "valve": 0.4,  # 阀门控制
            "air_quality": 0.35,  # 空气质量
            "siren": 0.3,  # 警报器
            "remote": 0.25,  # 遥控器
            "camera": 0.2,  # 摄像头
        }

    def compare_analysis_with_project(self, ai_analysis_file: str) -> Dict[str, Any]:
        """对比独立AI分析结果与项目配置"""

        if not PROJECT_DATA_AVAILABLE:
            return {
                "error": "无法导入项目配置数据",
                "suggestion": "请检查项目路径和导入设置",
            }

        # 读取独立AI分析结果
        with open(ai_analysis_file, "r", encoding="utf-8") as f:
            ai_results = json.load(f)

        # 执行对比分析
        comparison_results = []

        for section_name, devices in ai_results.items():
            for device_data in devices:
                device_type = device_data["device_type"]

                # 获取项目配置
                project_config = DEVICE_SPECS_DATA.get(device_type, {})

                for io_data in device_data["ios"]:
                    io_name = io_data["io_name"]
                    ai_platforms = io_data["recommended_platforms"][:3]  # 取前3个推荐
                    ai_confidence = io_data["confidence"]
                    ai_reasoning = io_data["reasoning"]

                    # 从项目配置中提取该IO的实际平台分配
                    project_platforms = self._extract_project_platforms(
                        project_config, io_name
                    )

                    # 计算差异
                    if project_platforms or ai_platforms:
                        comparison = self._analyze_difference(
                            device_type,
                            io_name,
                            ai_platforms,
                            project_platforms,
                            ai_confidence,
                            ai_reasoning,
                        )
                        if comparison:
                            comparison_results.append(comparison)

        # 生成对比报告
        return self._generate_comparison_report(comparison_results)

    def _extract_project_platforms(
        self, project_config: Dict[str, Any], io_name: str
    ) -> List[str]:
        """从项目配置中提取指定IO的平台分配"""
        platforms = []

        # 检查项目配置中的各个平台
        for platform, platform_config in project_config.items():
            if platform in ["name", "description", "versioned", "dynamic"]:
                continue

            if isinstance(platform_config, dict) and io_name in platform_config:
                platforms.append(platform)

        return platforms

    def _analyze_difference(
        self,
        device_type: str,
        io_name: str,
        ai_platforms: List[str],
        project_platforms: List[str],
        ai_confidence: float,
        ai_reasoning: str,
    ) -> ComparisonResult:
        """分析单个IO的差异"""

        ai_set = set(ai_platforms)
        project_set = set(project_platforms)

        # 确定差异类型
        if not project_platforms:
            diff_type = "missing_project"  # 项目中缺失
        elif not ai_platforms:
            diff_type = "missing_ai"  # AI分析中缺失
        elif ai_set == project_set:
            return None  # 完全匹配，无差异
        elif ai_set & project_set:
            diff_type = "minor"  # 部分重叠
        else:
            diff_type = "major"  # 完全不同

        # 计算影响分数
        impact_score = self._calculate_impact_score(
            ai_platforms, project_platforms, ai_confidence
        )

        return ComparisonResult(
            device_type=device_type,
            io_name=io_name,
            ai_recommendation=ai_platforms,
            project_actual=project_platforms,
            difference_type=diff_type,
            ai_confidence=ai_confidence,
            ai_reasoning=ai_reasoning,
            impact_score=impact_score,
        )

    def _calculate_impact_score(
        self, ai_platforms: List[str], project_platforms: List[str], confidence: float
    ) -> float:
        """计算差异的影响分数"""
        # 基础影响分数 = AI置信度
        base_impact = confidence

        # 平台重要性加权
        ai_importance = max(
            [self.ha_platform_priority.get(p, 0.1) for p in ai_platforms] or [0.1]
        )
        project_importance = max(
            [self.ha_platform_priority.get(p, 0.1) for p in project_platforms] or [0.1]
        )

        # 重要性差异越大，影响分数越高
        importance_diff = abs(ai_importance - project_importance)

        # 最终影响分数
        impact_score = base_impact * (0.7 + 0.3 * importance_diff)

        return min(1.0, impact_score)

    def _generate_comparison_report(
        self, comparisons: List[ComparisonResult]
    ) -> Dict[str, Any]:
        """生成对比报告"""

        # 按影响分数排序
        comparisons.sort(key=lambda x: x.impact_score, reverse=True)

        # 统计信息
        total = len(comparisons)
        major_diffs = len([c for c in comparisons if c.difference_type == "major"])
        minor_diffs = len([c for c in comparisons if c.difference_type == "minor"])
        missing_project = len(
            [c for c in comparisons if c.difference_type == "missing_project"]
        )
        missing_ai = len([c for c in comparisons if c.difference_type == "missing_ai"])

        # 平台分布统计
        ai_platform_stats = {}
        project_platform_stats = {}

        for comp in comparisons:
            for platform in comp.ai_recommendation:
                ai_platform_stats[platform] = ai_platform_stats.get(platform, 0) + 1
            for platform in comp.project_actual:
                project_platform_stats[platform] = (
                    project_platform_stats.get(platform, 0) + 1
                )

        # 高影响差异 (前20个)
        high_impact_diffs = [
            {
                "device_type": c.device_type,
                "io_name": c.io_name,
                "ai_recommendation": c.ai_recommendation,
                "project_actual": c.project_actual,
                "difference_type": c.difference_type,
                "impact_score": round(c.impact_score, 3),
                "ai_confidence": round(c.ai_confidence, 3),
                "ai_reasoning": c.ai_reasoning,
            }
            for c in comparisons[:20]
        ]

        # 各类差异的设备统计
        device_diff_stats = {}
        for comp in comparisons:
            device = comp.device_type
            if device not in device_diff_stats:
                device_diff_stats[device] = {
                    "major": 0,
                    "minor": 0,
                    "missing_project": 0,
                    "missing_ai": 0,
                }
            device_diff_stats[device][comp.difference_type] += 1

        return {
            "summary": {
                "total_differences": total,
                "major_differences": major_diffs,
                "minor_differences": minor_diffs,
                "missing_in_project": missing_project,
                "missing_in_ai": missing_ai,
                "difference_rate": round(
                    total / max(1, len(DEVICE_SPECS_DATA)) * 100, 2
                ),
            },
            "platform_distribution": {
                "ai_recommendations": dict(
                    sorted(ai_platform_stats.items(), key=lambda x: x[1], reverse=True)
                ),
                "project_actual": dict(
                    sorted(
                        project_platform_stats.items(), key=lambda x: x[1], reverse=True
                    )
                ),
            },
            "high_impact_differences": high_impact_diffs,
            "device_statistics": dict(
                sorted(
                    device_diff_stats.items(),
                    key=lambda x: sum(x[1].values()),
                    reverse=True,
                )[:10]
            ),
            "recommendations": self._generate_recommendations(comparisons),
        }

    def _generate_recommendations(
        self, comparisons: List[ComparisonResult]
    ) -> List[str]:
        """生成优化建议"""
        recommendations = []

        # 高影响差异建议
        high_impact = [c for c in comparisons if c.impact_score >= 0.8]
        if high_impact:
            recommendations.append(
                f"🔴 发现{len(high_impact)}个高影响差异，建议优先处理这些IO的平台分配"
            )

        # 缺失项目配置建议
        missing_project = [
            c for c in comparisons if c.difference_type == "missing_project"
        ]
        if missing_project:
            recommendations.append(
                f"📝 发现{len(missing_project)}个IO在项目中缺失配置，建议添加这些IO的平台支持"
            )

        # 主要差异建议
        major_diffs = [c for c in comparisons if c.difference_type == "major"]
        if major_diffs:
            recommendations.append(
                f"⚡ 发现{len(major_diffs)}个主要平台分配差异，建议重新评估这些IO的平台适用性"
            )

        # 高置信度AI建议
        high_confidence_ai = [
            c
            for c in comparisons
            if c.ai_confidence >= 0.9
            and c.difference_type in ["major", "missing_project"]
        ]
        if high_confidence_ai:
            recommendations.append(
                f"🎯 发现{len(high_confidence_ai)}个高置信度AI建议与项目不符，这些建议值得考虑采纳"
            )

        return recommendations


def main():
    """主函数"""
    comparator = MappingComparator()

    # AI分析结果文件路径
    ai_analysis_file = "/Volumes/LocalRAW/lifesmart-HACS-for-hass/.testing/mapping_tool/independent_ai_analysis.json"

    if not os.path.exists(ai_analysis_file):
        print("❌ 未找到独立AI分析结果文件")
        print("请先运行独立文档分析器生成AI分析结果")
        return

    print("🔄 开始对比独立AI分析结果与项目配置...")
    print(f"📊 项目数据状态: {'✅ 可用' if PROJECT_DATA_AVAILABLE else '❌ 不可用'}")
    if PROJECT_DATA_AVAILABLE:
        print(f"📋 项目设备数量: {len(DEVICE_SPECS_DATA)}")

    # 执行对比分析
    comparison_report = comparator.compare_analysis_with_project(ai_analysis_file)

    if "error" in comparison_report:
        print(f"❌ 对比分析失败: {comparison_report['error']}")
        return

    # 显示对比结果
    summary = comparison_report["summary"]
    print(f"✅ 对比分析完成！")
    print(f"📊 差异统计:")
    print(f"  - 总差异数: {summary['total_differences']}")
    print(f"  - 主要差异: {summary['major_differences']}")
    print(f"  - 次要差异: {summary['minor_differences']}")
    print(f"  - 项目缺失: {summary['missing_in_project']}")
    print(f"  - AI缺失: {summary['missing_in_ai']}")
    print(f"  - 差异率: {summary['difference_rate']}%")

    # 显示前几个高影响差异
    print(f"\n🔍 前10个高影响差异:")
    for i, diff in enumerate(comparison_report["high_impact_differences"][:10], 1):
        print(f"  {i}. {diff['device_type']}.{diff['io_name']}")
        print(f"     AI推荐: {diff['ai_recommendation']}")
        print(f"     项目实际: {diff['project_actual']}")
        print(f"     影响分数: {diff['impact_score']}")
        print(f"     差异类型: {diff['difference_type']}")

    # 显示建议
    print(f"\n💡 优化建议:")
    for rec in comparison_report["recommendations"]:
        print(f"  {rec}")

    # 保存详细对比报告
    output_file = "/Volumes/LocalRAW/lifesmart-HACS-for-hass/.testing/mapping_tool/mapping_comparison_report.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(comparison_report, f, ensure_ascii=False, indent=2)

    print(f"\n💾 详细对比报告已保存: {output_file}")


if __name__ == "__main__":
    main()
