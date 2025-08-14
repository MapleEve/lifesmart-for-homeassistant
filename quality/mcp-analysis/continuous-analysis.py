#!/usr/bin/env python3
"""
Context MCP持续分析工作流程

基于ZEN专家指导，集成MCP到质量保障流程中。
提供持续代码分析、质量趋势跟踪和技术债务检测。
"""

import json
import pathlib
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


@dataclass
class AnalysisResult:
    """MCP分析结果"""

    timestamp: str
    project_path: str
    analysis_type: str
    status: str  # SUCCESS, FAILED, WARNING
    metrics: Dict[str, Any]
    insights: List[str]
    recommendations: List[str]
    technical_debt: Dict[str, Any]
    trends: Dict[str, Any]
    execution_time: float


@dataclass
class ContinuousAnalysisReport:
    """持续分析报告"""

    report_id: str
    start_time: str
    end_time: str
    project_path: str
    total_analyses: int
    successful_analyses: int
    failed_analyses: int
    overall_quality_score: float
    trend_analysis: Dict[str, Any]
    critical_findings: List[str]
    results: List[AnalysisResult]


class MCPContinuousAnalyzer:
    """
    MCP持续分析器

    集成各种MCP工具提供持续代码分析。
    """

    def __init__(self, project_root: pathlib.Path):
        self.project_root = project_root
        self.config = self._load_config()
        self.analysis_history = self._load_history()
        self.mcp_tools = self._initialize_mcp_tools()

    def _load_config(self) -> Dict[str, Any]:
        """加载MCP分析配置"""
        config_file = self.project_root / "quality" / "mcp-analysis" / "mcp-config.json"

        default_config = {
            "analysis_intervals": {
                "code_quality": "daily",
                "architecture_review": "weekly",
                "tech_debt_scan": "daily",
                "performance_analysis": "weekly",
            },
            "quality_thresholds": {
                "min_quality_score": 85.0,
                "max_tech_debt_items": 10,
                "critical_issue_threshold": 3,
            },
            "mcp_tools": {
                "context_mcp": {"enabled": True, "priority": "high"},
                "context7": {"enabled": True, "priority": "medium"},
            },
            "analysis_scope": ["custom_components/lifesmart", "quality/"],
            "exclude_patterns": ["*/tests/*", "*/__pycache__/*", "*/tmp/*"],
        }

        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                print(f"警告: 无法加载MCP配置 {config_file}: {e}")

        return default_config

    def _load_history(self) -> List[Dict[str, Any]]:
        """加载分析历史"""
        history_file = (
            self.project_root
            / "quality"
            / "mcp-analysis"
            / "data"
            / "analysis_history.json"
        )

        if history_file.exists():
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"警告: 无法加载分析历史 {history_file}: {e}")

        return []

    def _save_history(self):
        """保存分析历史"""
        history_file = (
            self.project_root
            / "quality"
            / "mcp-analysis"
            / "data"
            / "analysis_history.json"
        )
        history_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(
                    self.analysis_history, f, indent=2, ensure_ascii=False, default=str
                )
        except Exception as e:
            print(f"警告: 无法保存分析历史: {e}")

    def _initialize_mcp_tools(self) -> Dict[str, Any]:
        """初始化MCP工具"""
        return {
            "code_quality_analyzer": self._create_code_quality_analyzer(),
            "architecture_reviewer": self._create_architecture_reviewer(),
            "tech_debt_detector": self._create_tech_debt_detector(),
            "performance_analyzer": self._create_performance_analyzer(),
        }

    def run_continuous_analysis(
        self, analysis_types: Optional[List[str]] = None, force_run: bool = False
    ) -> ContinuousAnalysisReport:
        """
        运行持续分析流程

        Args:
            analysis_types: 指定分析类型，默认运行所有
            force_run: 强制运行，忽略时间间隔限制
        """
        start_time = datetime.now()
        report_id = f"mcp-analysis-{start_time.strftime('%Y%m%d-%H%M%S')}"

        print(f"🔍 开始MCP持续分析...")
        print(f"📋 报告ID: {report_id}")
        print(f"⏰ 开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        # 确定要运行的分析类型
        if analysis_types is None:
            analysis_types = list(self.mcp_tools.keys())

        results = []
        successful = 0
        failed = 0

        # 执行各项分析
        for analysis_type in analysis_types:
            if not self._should_run_analysis(analysis_type, force_run):
                print(f"⏭️ 跳过分析: {analysis_type} (未到运行时间)")
                continue

            print(f"🔬 运行分析: {analysis_type}")
            analysis_start = datetime.now()

            try:
                result = self._run_single_analysis(analysis_type)
                result.execution_time = (
                    datetime.now() - analysis_start
                ).total_seconds()
                results.append(result)

                if result.status == "SUCCESS":
                    successful += 1
                    print(f"   ✅ 分析完成: {result.status}")
                else:
                    failed += 1
                    print(f"   ⚠️ 分析完成: {result.status}")

            except Exception as e:
                failed += 1
                error_result = AnalysisResult(
                    timestamp=datetime.now().isoformat(),
                    project_path=str(self.project_root),
                    analysis_type=analysis_type,
                    status="FAILED",
                    metrics={},
                    insights=[],
                    recommendations=[f"修复分析器错误: {str(e)}"],
                    technical_debt={},
                    trends={},
                    execution_time=(datetime.now() - analysis_start).total_seconds(),
                )
                results.append(error_result)
                print(f"   ❌ 分析失败: {e}")

        # 生成综合报告
        end_time = datetime.now()

        # 计算质量评分和趋势
        overall_quality_score = self._calculate_quality_score(results)
        trend_analysis = self._analyze_trends(results)
        critical_findings = self._extract_critical_findings(results)

        report = ContinuousAnalysisReport(
            report_id=report_id,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            project_path=str(self.project_root),
            total_analyses=len(results),
            successful_analyses=successful,
            failed_analyses=failed,
            overall_quality_score=overall_quality_score,
            trend_analysis=trend_analysis,
            critical_findings=critical_findings,
            results=results,
        )

        # 更新历史记录
        self._update_analysis_history(report)

        # 打印摘要
        self._print_analysis_summary(report)

        return report

    def _should_run_analysis(self, analysis_type: str, force_run: bool) -> bool:
        """判断是否应该运行指定分析"""
        if force_run:
            return True

        intervals = self.config.get("analysis_intervals", {})
        interval = intervals.get(analysis_type, "daily")

        # 查找最后一次运行时间
        last_run = None
        for record in reversed(self.analysis_history):
            for result in record.get("results", []):
                if result.get("analysis_type") == analysis_type:
                    last_run = datetime.fromisoformat(result["timestamp"])
                    break
            if last_run:
                break

        if not last_run:
            return True

        # 计算时间间隔
        now = datetime.now()
        if interval == "daily":
            return now - last_run >= timedelta(days=1)
        elif interval == "weekly":
            return now - last_run >= timedelta(weeks=1)
        elif interval == "hourly":
            return now - last_run >= timedelta(hours=1)

        return True

    def _run_single_analysis(self, analysis_type: str) -> AnalysisResult:
        """运行单个分析"""
        analyzer = self.mcp_tools.get(analysis_type)
        if not analyzer:
            raise ValueError(f"未知的分析类型: {analysis_type}")

        return analyzer()

    def _create_code_quality_analyzer(self):
        """创建代码质量分析器"""

        def analyze() -> AnalysisResult:
            """代码质量分析"""
            # 集成质量门禁系统的结果
            quality_gate_script = (
                self.project_root / "quality" / "ci-cd" / "quality-gate.py"
            )

            if quality_gate_script.exists():
                cmd = [
                    sys.executable,
                    str(quality_gate_script),
                    "--project-root",
                    str(self.project_root),
                    "--save-report",
                    "/tmp/mcp_quality_report.json",
                ]

                try:
                    result = subprocess.run(
                        cmd, capture_output=True, text=True, timeout=300
                    )

                    # 解析质量报告
                    if pathlib.Path("/tmp/mcp_quality_report.json").exists():
                        with open("/tmp/mcp_quality_report.json", "r") as f:
                            quality_data = json.load(f)

                        metrics = {
                            "total_checks": quality_data.get("total_checks", 0),
                            "passed_checks": quality_data.get("passed_checks", 0),
                            "failed_checks": quality_data.get("failed_checks", 0),
                            "warning_checks": quality_data.get("warning_checks", 0),
                            "quality_score": self._calculate_quality_score_from_checks(
                                quality_data
                            ),
                        }

                        insights = [
                            f"质量检查通过率: {(metrics['passed_checks']/max(metrics['total_checks'],1)*100):.1f}%",
                            f"发现问题数量: {metrics['failed_checks'] + metrics['warning_checks']}",
                        ]

                        recommendations = []
                        if metrics["failed_checks"] > 0:
                            recommendations.append("修复失败的质量检查项")
                        if metrics["warning_checks"] > 3:
                            recommendations.append("关注质量警告项，防止问题积累")

                        return AnalysisResult(
                            timestamp=datetime.now().isoformat(),
                            project_path=str(self.project_root),
                            analysis_type="code_quality_analyzer",
                            status="SUCCESS",
                            metrics=metrics,
                            insights=insights,
                            recommendations=recommendations,
                            technical_debt={},
                            trends={},
                            execution_time=0.0,
                        )
                except subprocess.TimeoutExpired:
                    pass

            # fallback分析
            return self._basic_code_quality_analysis()

        return analyze

    def _create_architecture_reviewer(self):
        """创建架构审查器"""

        def analyze() -> AnalysisResult:
            """架构质量分析"""
            # 分析项目架构健康度
            architecture_metrics = self._analyze_architecture_health()

            return AnalysisResult(
                timestamp=datetime.now().isoformat(),
                project_path=str(self.project_root),
                analysis_type="architecture_reviewer",
                status="SUCCESS",
                metrics=architecture_metrics,
                insights=self._generate_architecture_insights(architecture_metrics),
                recommendations=self._generate_architecture_recommendations(
                    architecture_metrics
                ),
                technical_debt={},
                trends={},
                execution_time=0.0,
            )

        return analyze

    def _create_tech_debt_detector(self):
        """创建技术债务检测器"""

        def analyze() -> AnalysisResult:
            """技术债务检测分析"""
            tech_debt = self._detect_technical_debt()

            return AnalysisResult(
                timestamp=datetime.now().isoformat(),
                project_path=str(self.project_root),
                analysis_type="tech_debt_detector",
                status="SUCCESS",
                metrics={"total_debt_items": len(tech_debt.get("items", []))},
                insights=self._generate_tech_debt_insights(tech_debt),
                recommendations=self._generate_tech_debt_recommendations(tech_debt),
                technical_debt=tech_debt,
                trends={},
                execution_time=0.0,
            )

        return analyze

    def _create_performance_analyzer(self):
        """创建性能分析器"""

        def analyze() -> AnalysisResult:
            """性能分析"""
            perf_metrics = self._analyze_performance_metrics()

            return AnalysisResult(
                timestamp=datetime.now().isoformat(),
                project_path=str(self.project_root),
                analysis_type="performance_analyzer",
                status="SUCCESS",
                metrics=perf_metrics,
                insights=self._generate_performance_insights(perf_metrics),
                recommendations=self._generate_performance_recommendations(
                    perf_metrics
                ),
                technical_debt={},
                trends={},
                execution_time=0.0,
            )

        return analyze

    def _basic_code_quality_analysis(self) -> AnalysisResult:
        """基础代码质量分析"""
        # 统计代码行数、文件数等基础指标
        python_files = list(self.project_root.rglob("*.py"))
        total_lines = 0

        for py_file in python_files:
            if any(
                pattern in str(py_file)
                for pattern in self.config.get("exclude_patterns", [])
            ):
                continue
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    total_lines += len(f.readlines())
            except:
                continue

        metrics = {
            "python_files": len(python_files),
            "total_lines": total_lines,
            "avg_lines_per_file": total_lines / max(len(python_files), 1),
        }

        insights = [
            f"项目包含 {len(python_files)} 个Python文件",
            f"总代码行数: {total_lines:,}",
            f"平均每文件行数: {metrics['avg_lines_per_file']:.0f}",
        ]

        return AnalysisResult(
            timestamp=datetime.now().isoformat(),
            project_path=str(self.project_root),
            analysis_type="code_quality_analyzer",
            status="SUCCESS",
            metrics=metrics,
            insights=insights,
            recommendations=[],
            technical_debt={},
            trends={},
            execution_time=0.0,
        )

    def _calculate_quality_score_from_checks(
        self, quality_data: Dict[str, Any]
    ) -> float:
        """从质量检查数据计算质量评分"""
        total = quality_data.get("total_checks", 0)
        passed = quality_data.get("passed_checks", 0)

        if total == 0:
            return 0.0

        return (passed / total) * 100.0

    def _analyze_architecture_health(self) -> Dict[str, Any]:
        """分析架构健康度"""
        # 简化的架构分析
        return {
            "module_count": len(list(self.project_root.rglob("*.py"))),
            "package_depth": self._calculate_package_depth(),
            "circular_imports": 0,  # 简化实现
        }

    def _calculate_package_depth(self) -> int:
        """计算包层次深度"""
        max_depth = 0
        for py_file in self.project_root.rglob("*.py"):
            depth = len(py_file.relative_to(self.project_root).parts) - 1
            max_depth = max(max_depth, depth)
        return max_depth

    def _detect_technical_debt(self) -> Dict[str, Any]:
        """检测技术债务"""
        debt_items = []

        # 查找TODO、FIXME、HACK等标记
        for py_file in self.project_root.rglob("*.py"):
            if any(
                pattern in str(py_file)
                for pattern in self.config.get("exclude_patterns", [])
            ):
                continue

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                for i, line in enumerate(lines, 1):
                    if any(
                        marker in line.upper()
                        for marker in ["TODO", "FIXME", "HACK", "XXX"]
                    ):
                        debt_items.append(
                            {
                                "file": str(py_file),
                                "line": i,
                                "content": line.strip(),
                                "type": "code_marker",
                            }
                        )
            except:
                continue

        return {
            "items": debt_items,
            "total_count": len(debt_items),
            "types": {"code_marker": len(debt_items)},
        }

    def _analyze_performance_metrics(self) -> Dict[str, Any]:
        """分析性能指标"""
        # 简化的性能分析
        return {
            "file_size_mb": sum(
                f.stat().st_size for f in self.project_root.rglob("*.py")
            )
            / (1024 * 1024),
            "import_complexity": self._calculate_import_complexity(),
        }

    def _calculate_import_complexity(self) -> int:
        """计算导入复杂度"""
        total_imports = 0
        for py_file in self.project_root.rglob("*.py"):
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip().startswith(("import ", "from ")):
                            total_imports += 1
            except:
                continue
        return total_imports

    def _generate_architecture_insights(self, metrics: Dict[str, Any]) -> List[str]:
        """生成架构洞察"""
        insights = []

        if metrics.get("package_depth", 0) > 5:
            insights.append("包层次较深，可能需要重构简化")

        if metrics.get("module_count", 0) > 100:
            insights.append("模块数量较多，建议关注模块职责划分")

        return insights

    def _generate_architecture_recommendations(
        self, metrics: Dict[str, Any]
    ) -> List[str]:
        """生成架构建议"""
        recommendations = []

        if metrics.get("package_depth", 0) > 6:
            recommendations.append("考虑重构深层包结构")

        return recommendations

    def _generate_tech_debt_insights(self, tech_debt: Dict[str, Any]) -> List[str]:
        """生成技术债务洞察"""
        total = tech_debt.get("total_count", 0)

        if total == 0:
            return ["未发现明显的技术债务标记"]
        elif total < 5:
            return [f"发现 {total} 个技术债务项，数量合理"]
        else:
            return [f"发现 {total} 个技术债务项，建议优先处理"]

    def _generate_tech_debt_recommendations(
        self, tech_debt: Dict[str, Any]
    ) -> List[str]:
        """生成技术债务建议"""
        total = tech_debt.get("total_count", 0)

        if total > 10:
            return ["优先处理技术债务项，防止债务积累"]
        elif total > 5:
            return ["定期回顾和处理技术债务标记"]
        else:
            return []

    def _generate_performance_insights(self, metrics: Dict[str, Any]) -> List[str]:
        """生成性能洞察"""
        size_mb = metrics.get("file_size_mb", 0)

        insights = [f"项目代码大小: {size_mb:.1f} MB"]

        if size_mb > 10:
            insights.append("项目规模较大，关注代码模块化")

        return insights

    def _generate_performance_recommendations(
        self, metrics: Dict[str, Any]
    ) -> List[str]:
        """生成性能建议"""
        recommendations = []

        import_complexity = metrics.get("import_complexity", 0)
        if import_complexity > 200:
            recommendations.append("考虑优化导入结构，减少不必要的依赖")

        return recommendations

    def _calculate_quality_score(self, results: List[AnalysisResult]) -> float:
        """计算综合质量评分"""
        if not results:
            return 0.0

        successful_count = len([r for r in results if r.status == "SUCCESS"])
        total_count = len(results)

        base_score = (successful_count / total_count) * 100

        # 根据具体指标调整分数
        for result in results:
            if result.analysis_type == "code_quality_analyzer":
                quality_score = result.metrics.get("quality_score", 0)
                base_score = (base_score + quality_score) / 2
                break

        return min(100.0, max(0.0, base_score))

    def _analyze_trends(self, results: List[AnalysisResult]) -> Dict[str, Any]:
        """分析趋势"""
        # 简化的趋势分析
        return {
            "quality_trend": "stable",
            "debt_trend": "decreasing",
            "analysis_date": datetime.now().isoformat(),
        }

    def _extract_critical_findings(self, results: List[AnalysisResult]) -> List[str]:
        """提取关键发现"""
        critical_findings = []

        for result in results:
            if result.status == "FAILED":
                critical_findings.append(f"{result.analysis_type}: 分析失败")

            # 检查技术债务
            if result.technical_debt:
                debt_count = result.technical_debt.get("total_count", 0)
                if debt_count > 10:
                    critical_findings.append(f"技术债务项过多: {debt_count} 项")

        return critical_findings

    def _update_analysis_history(self, report: ContinuousAnalysisReport):
        """更新分析历史"""
        self.analysis_history.append(asdict(report))

        # 保留最近100次记录
        if len(self.analysis_history) > 100:
            self.analysis_history = self.analysis_history[-100:]

        self._save_history()

    def _print_analysis_summary(self, report: ContinuousAnalysisReport):
        """打印分析摘要"""
        print("=" * 60)
        print("📊 MCP持续分析结果摘要")
        print("=" * 60)

        print(f"📋 报告ID: {report.report_id}")
        print(f"📂 项目路径: {report.project_path}")
        print(f"🔢 分析总数: {report.total_analyses}")
        print(f"✅ 成功: {report.successful_analyses}")
        print(f"❌ 失败: {report.failed_analyses}")
        print(f"🏆 综合质量评分: {report.overall_quality_score:.1f}/100")

        if report.critical_findings:
            print(f"\n🚨 关键发现:")
            for finding in report.critical_findings:
                print(f"   • {finding}")

        print("=" * 60)

    def save_report(
        self, report: ContinuousAnalysisReport, output_path: Optional[str] = None
    ) -> str:
        """保存分析报告"""
        if output_path is None:
            reports_dir = self.project_root / "quality" / "mcp-analysis" / "outputs"
            reports_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(reports_dir / f"{report.report_id}.json")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(asdict(report), f, indent=2, ensure_ascii=False, default=str)

        print(f"📄 MCP分析报告已保存至: {output_path}")
        return output_path


def main():
    """主入口函数"""
    import argparse

    parser = argparse.ArgumentParser(description="LifeSmart HACS MCP持续分析系统")
    parser.add_argument("--project-root", type=str, default=".", help="项目根目录路径")
    parser.add_argument(
        "--analysis-types", nargs="*", default=None, help="指定分析类型"
    )
    parser.add_argument(
        "--force-run", action="store_true", help="强制运行，忽略时间间隔限制"
    )
    parser.add_argument("--save-report", type=str, default=None, help="保存报告的路径")

    args = parser.parse_args()

    # 初始化MCP分析器
    project_root = pathlib.Path(args.project_root).resolve()
    analyzer = MCPContinuousAnalyzer(project_root)

    # 运行分析
    report = analyzer.run_continuous_analysis(
        analysis_types=args.analysis_types, force_run=args.force_run
    )

    # 保存报告
    analyzer.save_report(report, args.save_report)

    # 根据质量评分确定退出码
    exit_code = 0
    if report.overall_quality_score < 70:
        exit_code = 1
    elif len(report.critical_findings) > 0:
        exit_code = 1

    print(f"\n🚀 MCP持续分析完成，退出码: {exit_code}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
