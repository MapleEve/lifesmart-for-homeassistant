#!/usr/bin/env python3
"""
代码样式检查器

基于black和isort进行代码格式检查。
"""

import pathlib
import shutil
from typing import Dict, List, Any

from . import BaseChecker
from ..quality_gate import QualityCheckResult


class CodeStyleChecker(BaseChecker):
    """代码样式检查器"""

    def check(self, target_paths: List[str]) -> "CheckResult":
        """执行代码样式检查"""
        if not self._is_enabled():
            return self._create_result(
                "code_style",
                QualityCheckResult.SKIPPED,
                "代码样式检查已禁用",
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
            "tests/",  # 暂时排除测试文件以专注核心代码
        ]
        python_files = self._exclude_files(python_files, exclude_patterns)

        if not python_files:
            return self._create_result(
                "code_style",
                QualityCheckResult.WARNING,
                "未找到要检查的Python文件",
                {"files_found": 0},
            )

        details = {"files_checked": len(python_files), "tools_used": []}
        issues = []

        # 执行black检查
        black_result = self._check_black(python_files)
        if black_result:
            details["tools_used"].append("black")
            details["black_issues"] = black_result["issues"]
            issues.extend(black_result["issues"])

        # 执行isort检查
        isort_result = self._check_isort(python_files)
        if isort_result:
            details["tools_used"].append("isort")
            details["isort_issues"] = isort_result["issues"]
            issues.extend(isort_result["issues"])

        # 确定结果状态
        if not issues:
            status = QualityCheckResult.PASSED
            message = f"代码样式检查通过 ({len(python_files)} 个文件)"
        elif len(issues) <= 5:
            status = QualityCheckResult.WARNING
            message = f"发现 {len(issues)} 个样式问题 (可接受范围内)"
        else:
            status = QualityCheckResult.FAILED
            message = f"发现 {len(issues)} 个样式问题 (需要修复)"

        details["total_issues"] = len(issues)
        details["issue_summary"] = issues[:10]  # 只显示前10个问题

        return self._create_result("code_style", status, message, details)

    def _check_black(self, python_files: List[pathlib.Path]) -> Dict[str, Any]:
        """使用black检查代码格式"""
        if not shutil.which("black"):
            return {"issues": ["Black 工具未安装，跳过格式检查"]}

        try:
            # 使用black的check模式
            cmd = ["black", "--check", "--diff"] + [str(f) for f in python_files]
            result = self._run_command(cmd, timeout=120)

            issues = []
            if result.returncode != 0:
                # 解析black输出
                lines = result.stdout.split("\n")
                for line in lines:
                    if line.startswith("---") or line.startswith("+++"):
                        issues.append(f"Black格式问题: {line}")

                # 如果没有具体的diff，添加通用消息
                if not issues:
                    issues.append("Black检测到格式问题，建议运行 black 进行修复")

            return {"issues": issues}
        except Exception as e:
            return {"issues": [f"Black检查失败: {str(e)}"]}

    def _check_isort(self, python_files: List[pathlib.Path]) -> Dict[str, Any]:
        """使用isort检查导入排序"""
        if not shutil.which("isort"):
            return {"issues": ["isort 工具未安装，跳过导入检查"]}

        try:
            # 使用isort的check模式
            cmd = ["isort", "--check-only", "--diff"] + [str(f) for f in python_files]
            result = self._run_command(cmd, timeout=120)

            issues = []
            if result.returncode != 0:
                # 解析isort输出
                lines = result.stderr.split("\n")
                for line in lines:
                    if (
                        "Imports are incorrectly sorted" in line
                        or "wrong place" in line
                    ):
                        issues.append(f"导入排序问题: {line}")

                # 如果没有具体错误，添加通用消息
                if not issues:
                    issues.append("isort检测到导入排序问题，建议运行 isort 进行修复")

            return {"issues": issues}
        except Exception as e:
            return {"issues": [f"isort检查失败: {str(e)}"]}
