#!/usr/bin/env python3
"""
类型安全检查器

使用mypy进行类型检查。
"""

import pathlib
import shutil
from typing import List

from . import BaseChecker
from ..quality_gate import QualityCheckResult


class TypeSafetyChecker(BaseChecker):
    """类型安全检查器"""

    def check(self, target_paths: List[str]) -> "CheckResult":
        """执行类型安全检查"""
        if not self._is_enabled():
            return self._create_result(
                "type_safety",
                QualityCheckResult.SKIPPED,
                "类型安全检查已禁用",
            )

        # 获取Python文件
        python_files = self._filter_python_files(target_paths)
        exclude_patterns = [
            "__pycache__",
            ".git",
            "venv",
            ".venv",
            "build",
            "dist",
            ".pytest_cache",
            "tests/",  # 暂时排除测试文件
        ]
        python_files = self._exclude_files(python_files, exclude_patterns)

        if not python_files:
            return self._create_result(
                "type_safety",
                QualityCheckResult.WARNING,
                "未找到要检查的Python文件",
                {"files_found": 0},
            )

        # 执行mypy检查
        return self._check_mypy(target_paths, python_files)

    def _check_mypy(
        self, target_paths: List[str], python_files: List[pathlib.Path]
    ) -> "CheckResult":
        """使用mypy检查类型安全"""
        if not shutil.which("mypy"):
            return self._create_result(
                "type_safety",
                QualityCheckResult.WARNING,
                "mypy 工具未安装，跳过类型检查",
                {"mypy_available": False},
            )

        try:
            # 构建mypy命令
            mypy_config = self.config.get("mypy_config", "--ignore-missing-imports")
            cmd = ["mypy"] + mypy_config.split() + target_paths

            result = self._run_command(cmd, timeout=180)

            issues = []
            error_count = 0
            warning_count = 0

            if result.returncode != 0:
                lines = result.stdout.split("\n")
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith("Success:"):
                        continue

                    if ": error:" in line:
                        issues.append(f"类型错误: {line}")
                        error_count += 1
                    elif ": warning:" in line:
                        issues.append(f"类型警告: {line}")
                        warning_count += 1
                    elif ": note:" in line:
                        issues.append(f"类型提示: {line}")

            details = {
                "files_checked": len(python_files),
                "error_count": error_count,
                "warning_count": warning_count,
                "total_issues": len(issues),
                "issue_summary": issues[:10],  # 只显示前10个问题
                "mypy_available": True,
            }

            # 确定结果状态
            if error_count == 0 and warning_count == 0:
                status = QualityCheckResult.PASSED
                message = f"类型检查通过 ({len(python_files)} 个文件)"
            elif error_count == 0 and warning_count <= 3:
                status = QualityCheckResult.WARNING
                message = f"发现 {warning_count} 个类型警告"
            else:
                status = QualityCheckResult.FAILED
                message = f"发现 {error_count} 个类型错误, {warning_count} 个警告"

            return self._create_result("type_safety", status, message, details)

        except Exception as e:
            return self._create_result(
                "type_safety",
                QualityCheckResult.FAILED,
                f"mypy检查失败: {str(e)}",
                {"error": str(e)},
            )
