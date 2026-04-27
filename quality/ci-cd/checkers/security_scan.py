#!/usr/bin/env python3
"""
安全扫描检查器

使用bandit进行安全漏洞检测。
"""

import json
import pathlib
import shutil
from typing import List

from . import BaseChecker
from ..quality_gate import QualityCheckResult


class SecurityScanner(BaseChecker):
    """安全扫描检查器"""

    def check(self, target_paths: List[str]) -> "CheckResult":
        """执行安全扫描"""
        if not self._is_enabled():
            return self._create_result(
                "security_scan",
                QualityCheckResult.SKIPPED,
                "安全扫描已禁用",
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
                "security_scan",
                QualityCheckResult.WARNING,
                "未找到要检查的Python文件",
                {"files_found": 0},
            )

        # 执行bandit扫描
        return self._scan_with_bandit(target_paths, python_files)

    def _scan_with_bandit(
        self, target_paths: List[str], python_files: List[pathlib.Path]
    ) -> "CheckResult":
        """使用bandit进行安全扫描"""
        if not shutil.which("bandit"):
            # 如果bandit未安装，执行基础的安全模式扫描
            return self._basic_security_scan(python_files)

        try:
            # 构建bandit命令
            severity_threshold = self.config.get("severity_threshold", "medium")
            cmd = [
                "bandit",
                "-r",
                "-f",
                "json",
                "--severity-level",
                severity_threshold,
            ] + target_paths

            result = self._run_command(cmd, timeout=180)

            # 解析bandit JSON输出
            try:
                if result.stdout:
                    bandit_data = json.loads(result.stdout)
                else:
                    bandit_data = {"results": [], "metrics": {}}
            except json.JSONDecodeError:
                # 如果JSON解析失败，尝试解析文本输出
                return self._parse_bandit_text_output(result, python_files)

            issues = bandit_data.get("results", [])
            metrics = bandit_data.get("metrics", {})

            # 按严重程度分类问题
            high_severity = [i for i in issues if i.get("issue_severity") == "HIGH"]
            medium_severity = [i for i in issues if i.get("issue_severity") == "MEDIUM"]
            low_severity = [i for i in issues if i.get("issue_severity") == "LOW"]

            details = {
                "files_checked": len(python_files),
                "total_issues": len(issues),
                "high_severity": len(high_severity),
                "medium_severity": len(medium_severity),
                "low_severity": len(low_severity),
                "bandit_available": True,
                "severity_threshold": severity_threshold,
                "metrics": metrics,
                "issue_summary": [
                    {
                        "file": issue.get("filename", "unknown"),
                        "line": issue.get("line_number", 0),
                        "severity": issue.get("issue_severity", "UNKNOWN"),
                        "confidence": issue.get("issue_confidence", "UNKNOWN"),
                        "test": issue.get("test_name", "unknown"),
                        "message": issue.get("issue_text", "unknown"),
                    }
                    for issue in issues[:10]
                ],  # 显示前10个问题
            }

            # 确定结果状态
            if len(high_severity) > 0:
                status = QualityCheckResult.FAILED
                message = f"发现 {len(high_severity)} 个高危安全问题"
            elif len(medium_severity) > 3:
                status = QualityCheckResult.FAILED
                message = f"发现 {len(medium_severity)} 个中危安全问题 (超过阈值)"
            elif len(medium_severity) > 0 or len(low_severity) > 0:
                status = QualityCheckResult.WARNING
                message = f"发现 {len(medium_severity)} 个中危, {len(low_severity)} 个低危安全问题"
            else:
                status = QualityCheckResult.PASSED
                message = f"未发现安全问题 ({len(python_files)} 个文件)"

            return self._create_result("security_scan", status, message, details)

        except Exception as e:
            return self._create_result(
                "security_scan",
                QualityCheckResult.FAILED,
                f"bandit扫描失败: {str(e)}",
                {"error": str(e)},
            )

    def _parse_bandit_text_output(
        self, result: "subprocess.CompletedProcess", python_files: List[pathlib.Path]
    ) -> "CheckResult":
        """解析bandit的文本输出"""
        issues = []

        if result.stdout:
            lines = result.stdout.split("\n")
            for line in lines:
                if ">> Issue:" in line or "Severity:" in line:
                    issues.append(line.strip())

        details = {
            "files_checked": len(python_files),
            "total_issues": len(issues),
            "bandit_available": True,
            "text_output": result.stdout[:1000],  # 限制输出长度
        }

        if result.returncode == 0:
            status = QualityCheckResult.PASSED
            message = f"安全扫描通过 ({len(python_files)} 个文件)"
        else:
            status = QualityCheckResult.WARNING
            message = f"发现 {len(issues)} 个潜在安全问题"

        return self._create_result("security_scan", status, message, details)

    def _basic_security_scan(self, python_files: List[pathlib.Path]) -> "CheckResult":
        """基础安全模式扫描 (bandit未安装时的备用方案)"""
        issues = []

        # 定义一些基本的安全问题模式
        security_patterns = [
            (r"eval\s*\(", "使用eval()可能导致代码注入"),
            (r"exec\s*\(", "使用exec()可能导致代码注入"),
            (
                r"subprocess\.call\([^)]*shell=True",
                "subprocess调用使用shell=True存在注入风险",
            ),
            (r"os\.system\s*\(", "使用os.system()存在命令注入风险"),
            (r"pickle\.loads?\s*\(", "使用pickle反序列化存在代码执行风险"),
            (r"yaml\.load\s*\([^)]*Loader=yaml\.Loader", "yaml.load使用不安全的Loader"),
            (r"random\.random\(\)", "使用random模块生成密码学随机数不安全"),
        ]

        import re

        for file_path in python_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    lines = content.split("\n")

                for i, line in enumerate(lines, 1):
                    for pattern, description in security_patterns:
                        if re.search(pattern, line):
                            issues.append(
                                {
                                    "file": str(
                                        file_path.relative_to(file_path.parents[5])
                                    ),
                                    "line": i,
                                    "pattern": pattern,
                                    "description": description,
                                    "code": line.strip(),
                                }
                            )
            except Exception:
                continue

        details = {
            "files_checked": len(python_files),
            "total_issues": len(issues),
            "bandit_available": False,
            "patterns_checked": len(security_patterns),
            "issue_summary": issues[:10],  # 显示前10个问题
        }

        if len(issues) == 0:
            status = QualityCheckResult.PASSED
            message = f"基础安全扫描通过 ({len(python_files)} 个文件)"
        elif len(issues) <= 3:
            status = QualityCheckResult.WARNING
            message = f"发现 {len(issues)} 个潜在安全问题 (建议安装bandit进行详细扫描)"
        else:
            status = QualityCheckResult.FAILED
            message = f"发现 {len(issues)} 个安全问题 (需要立即处理)"

        return self._create_result("security_scan", status, message, details)
