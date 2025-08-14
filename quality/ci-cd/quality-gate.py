#!/usr/bin/env python3
"""
LifeSmart HACS 质量门禁系统 - CI/CD质量关卡集成

基于Phase 1-2成功经验，提供企业级自动化质量检查。
"""

import argparse
import json
import pathlib
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any


class QualityCheckResult(Enum):
    """质量检查结果状态"""

    PASSED = "PASSED"
    FAILED = "FAILED"
    WARNING = "WARNING"
    SKIPPED = "SKIPPED"


@dataclass
class CheckResult:
    """单个检查结果"""

    checker: str
    status: QualityCheckResult
    message: str
    details: Dict[str, Any]
    execution_time: float
    timestamp: str


@dataclass
class QualityReport:
    """质量检查总报告"""

    project_path: str
    total_checks: int
    passed_checks: int
    failed_checks: int
    warning_checks: int
    skipped_checks: int
    overall_status: QualityCheckResult
    execution_time: float
    timestamp: str
    results: List[CheckResult]


class QualityGate:
    """
    质量门禁主控制器

    基于Phase 1-2验证的工具链，提供一站式质量检查。
    """

    def __init__(self, project_root: pathlib.Path):
        self.project_root = project_root
        self.quality_config = self._load_quality_config()
        self.checkers = self._initialize_checkers()

    def _load_quality_config(self) -> Dict[str, Any]:
        """加载质量配置"""
        config_file = self.project_root / "quality" / "configs" / "quality-config.json"

        # 默认配置基于项目当前最佳实践
        default_config = {
            "code_style": {
                "enabled": True,
                "tools": ["black", "isort"],
                "black_config": "--line-length=88 --target-version=py311",
            },
            "type_safety": {
                "enabled": True,
                "tools": ["mypy"],
                "mypy_config": "--strict --python-version=3.11",
            },
            "security_scan": {
                "enabled": True,
                "tools": ["bandit"],
                "severity_threshold": "medium",
            },
            "linting": {
                "enabled": True,
                "tools": ["ruff"],
                "ruff_config": "--select=E,W,F,B,C,N",
            },
            "hardcode_detection": {
                "enabled": True,
                "patterns": ["SL_", "OE_", "DE_", "SPOT_"],  # 基于Phase 1修复经验
            },
            "test_coverage": {"enabled": True, "minimum_coverage": 90.0},
        }

        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    user_config = json.load(f)
                    # 合并用户配置
                    default_config.update(user_config)
            except Exception as e:
                print(f"警告: 无法加载配置文件 {config_file}: {e}")

        return default_config

    def _initialize_checkers(self) -> Dict[str, Any]:
        """初始化检查器"""
        from .checkers.code_style import CodeStyleChecker
        from .checkers.type_safety import TypeSafetyChecker
        from .checkers.security_scan import SecurityScanner
        from .checkers.hardcode_detector import HardcodeDetector

        return {
            "code_style": CodeStyleChecker(self.quality_config["code_style"]),
            "type_safety": TypeSafetyChecker(self.quality_config["type_safety"]),
            "security_scan": SecurityScanner(self.quality_config["security_scan"]),
            "hardcode_detection": HardcodeDetector(
                self.quality_config["hardcode_detection"]
            ),
        }

    def run_quality_checks(
        self,
        target_paths: Optional[List[str]] = None,
        skip_checkers: Optional[List[str]] = None,
    ) -> QualityReport:
        """
        运行完整质量检查流程

        Args:
            target_paths: 目标检查路径，默认检查custom_components/lifesmart
            skip_checkers: 跳过的检查器列表
        """
        start_time = datetime.now()

        # 确定检查目标
        if target_paths is None:
            target_paths = [str(self.project_root / "custom_components" / "lifesmart")]

        skip_checkers = skip_checkers or []
        results = []

        print(f"🚦 开始质量门禁检查...")
        print(f"📂 检查路径: {target_paths}")
        print(f"⏰ 开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        # 执行各项检查
        for checker_name, checker in self.checkers.items():
            if checker_name in skip_checkers:
                result = CheckResult(
                    checker=checker_name,
                    status=QualityCheckResult.SKIPPED,
                    message=f"检查器 {checker_name} 已跳过",
                    details={},
                    execution_time=0.0,
                    timestamp=datetime.now().isoformat(),
                )
                results.append(result)
                continue

            print(f"🔍 运行检查器: {checker_name}")
            check_start = datetime.now()

            try:
                result = checker.check(target_paths)
                result.timestamp = datetime.now().isoformat()
                result.execution_time = (datetime.now() - check_start).total_seconds()
                results.append(result)

                # 输出结果摘要
                status_emoji = {
                    QualityCheckResult.PASSED: "✅",
                    QualityCheckResult.FAILED: "❌",
                    QualityCheckResult.WARNING: "⚠️",
                    QualityCheckResult.SKIPPED: "⏭️",
                }
                print(f"   {status_emoji.get(result.status, '❓')} {result.message}")

            except Exception as e:
                result = CheckResult(
                    checker=checker_name,
                    status=QualityCheckResult.FAILED,
                    message=f"检查器执行失败: {str(e)}",
                    details={"error": str(e)},
                    execution_time=(datetime.now() - check_start).total_seconds(),
                    timestamp=datetime.now().isoformat(),
                )
                results.append(result)
                print(f"   ❌ 检查器执行失败: {e}")

        # 生成总报告
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        passed = len([r for r in results if r.status == QualityCheckResult.PASSED])
        failed = len([r for r in results if r.status == QualityCheckResult.FAILED])
        warnings = len([r for r in results if r.status == QualityCheckResult.WARNING])
        skipped = len([r for r in results if r.status == QualityCheckResult.SKIPPED])

        # 确定总体状态
        if failed > 0:
            overall_status = QualityCheckResult.FAILED
        elif warnings > 0:
            overall_status = QualityCheckResult.WARNING
        else:
            overall_status = QualityCheckResult.PASSED

        report = QualityReport(
            project_path=str(self.project_root),
            total_checks=len(results),
            passed_checks=passed,
            failed_checks=failed,
            warning_checks=warnings,
            skipped_checks=skipped,
            overall_status=overall_status,
            execution_time=execution_time,
            timestamp=end_time.isoformat(),
            results=results,
        )

        self._print_summary(report)
        return report

    def _print_summary(self, report: QualityReport) -> None:
        """打印检查结果摘要"""
        print("=" * 60)
        print("📊 质量检查结果摘要")
        print("=" * 60)

        status_emoji = {
            QualityCheckResult.PASSED: "✅ 通过",
            QualityCheckResult.FAILED: "❌ 失败",
            QualityCheckResult.WARNING: "⚠️ 警告",
        }

        print(f"📂 项目路径: {report.project_path}")
        print(f"🔢 检查总数: {report.total_checks}")
        print(f"✅ 通过: {report.passed_checks}")
        print(f"❌ 失败: {report.failed_checks}")
        print(f"⚠️ 警告: {report.warning_checks}")
        print(f"⏭️ 跳过: {report.skipped_checks}")
        print(f"⏱️ 执行时间: {report.execution_time:.2f}秒")
        print(f"🏆 总体状态: {status_emoji.get(report.overall_status, '❓ 未知')}")

        if report.failed_checks > 0:
            print("\n❌ 失败的检查:")
            for result in report.results:
                if result.status == QualityCheckResult.FAILED:
                    print(f"   • {result.checker}: {result.message}")

        print("=" * 60)

    def save_report(
        self, report: QualityReport, output_path: Optional[str] = None
    ) -> str:
        """保存质量检查报告"""
        if output_path is None:
            reports_dir = self.project_root / "quality" / "ci-cd" / "reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(
                reports_dir
                / f"quality-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
            )

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(asdict(report), f, indent=2, ensure_ascii=False, default=str)

        print(f"📄 质量报告已保存至: {output_path}")
        return output_path


def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(description="LifeSmart HACS 质量门禁系统")
    parser.add_argument("--project-root", type=str, default=".", help="项目根目录路径")
    parser.add_argument(
        "--target-paths", nargs="*", default=None, help="指定检查的目标路径"
    )
    parser.add_argument(
        "--skip-checkers", nargs="*", default=None, help="跳过的检查器列表"
    )
    parser.add_argument("--save-report", type=str, default=None, help="保存报告的路径")
    parser.add_argument("--fail-on-warning", action="store_true", help="将警告视为失败")

    args = parser.parse_args()

    # 初始化质量门禁
    project_root = pathlib.Path(args.project_root).resolve()
    quality_gate = QualityGate(project_root)

    # 运行质量检查
    report = quality_gate.run_quality_checks(
        target_paths=args.target_paths, skip_checkers=args.skip_checkers
    )

    # 保存报告
    if args.save_report or report.failed_checks > 0:
        quality_gate.save_report(report, args.save_report)

    # 确定退出码
    exit_code = 0
    if report.failed_checks > 0:
        exit_code = 1
    elif args.fail_on_warning and report.warning_checks > 0:
        exit_code = 1

    print(f"\n🚀 质量门禁检查完成，退出码: {exit_code}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
