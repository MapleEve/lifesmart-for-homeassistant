#!/usr/bin/env python3
"""
硬编码检测器

基于Phase 1修复经验，检测硬编码的设备类型常量。
"""

import pathlib
import re
from typing import List

from . import BaseChecker
from ..quality_gate import QualityCheckResult


class HardcodeDetector(BaseChecker):
    """硬编码检测器"""

    def check(self, target_paths: List[str]) -> "CheckResult":
        """执行硬编码检测"""
        if not self._is_enabled():
            return self._create_result(
                "hardcode_detection",
                QualityCheckResult.SKIPPED,
                "硬编码检测已禁用",
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
            "tests/",  # 排除测试文件
            "const.py",  # 排除常量定义文件
        ]
        python_files = self._exclude_files(python_files, exclude_patterns)

        if not python_files:
            return self._create_result(
                "hardcode_detection",
                QualityCheckResult.WARNING,
                "未找到要检查的Python文件",
                {"files_found": 0},
            )

        # 执行硬编码检测
        return self._detect_hardcoded_values(python_files)

    def _detect_hardcoded_values(
        self, python_files: List[pathlib.Path]
    ) -> "CheckResult":
        """检测硬编码值"""
        patterns = self.config.get("patterns", ["SL_", "OE_", "DE_", "SPOT_"])

        # 基于Phase 1修复经验的检测模式
        hardcode_patterns = [
            # 设备类型硬编码
            (r'"(SL_[A-Z_]+)"', "设备类型字符串"),
            (r'"(OE_[A-Z_]+)"', "设备类型字符串"),
            (r'"(DE_[A-Z_]+)"', "设备类型字符串"),
            (r'"(SPOT_[A-Z_]+)"', "设备类型字符串"),
            # 字典键硬编码
            (r'[\'"](SL_[A-Z_]+)[\'"]\s*:', "字典键硬编码"),
            (r'[\'"](OE_[A-Z_]+)[\'"]\s*:', "字典键硬编码"),
            (r'[\'"](DE_[A-Z_]+)[\'"]\s*:', "字典键硬编码"),
            # 条件判断中的硬编码
            (r'==\s*[\'"](SL_[A-Z_]+)[\'"]', "条件判断硬编码"),
            (r'==\s*[\'"](OE_[A-Z_]+)[\'"]', "条件判断硬编码"),
            (r'in\s*\[.*[\'"](SL_[A-Z_]+)[\'"].*\]', "列表成员硬编码"),
        ]

        issues = []
        file_stats = {}

        for file_path in python_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    lines = content.split("\n")

                file_issues = []

                for i, line in enumerate(lines, 1):
                    # 跳过注释行和导入语句
                    line_stripped = line.strip()
                    if (
                        line_stripped.startswith("#")
                        or line_stripped.startswith("import")
                        or line_stripped.startswith("from")
                    ):
                        continue

                    for pattern, description in hardcode_patterns:
                        matches = re.finditer(pattern, line)
                        for match in matches:
                            hardcoded_value = match.group(1)
                            issue = {
                                "file": str(
                                    file_path.relative_to(file_path.parents[5])
                                ),
                                "line": i,
                                "column": match.start() + 1,
                                "hardcoded_value": hardcoded_value,
                                "description": description,
                                "suggestion": f"使用常量 CMD_TYPE_* 替代硬编码 '{hardcoded_value}'",
                            }
                            file_issues.append(issue)
                            issues.append(issue)

                file_stats[str(file_path.relative_to(file_path.parents[5]))] = len(
                    file_issues
                )

            except Exception as e:
                issues.append(
                    {
                        "file": str(file_path),
                        "line": 0,
                        "error": f"文件读取失败: {str(e)}",
                        "description": "文件处理错误",
                    }
                )

        details = {
            "files_checked": len(python_files),
            "total_issues": len(issues),
            "files_with_issues": len(
                [f for f, count in file_stats.items() if count > 0]
            ),
            "file_statistics": file_stats,
            "issue_summary": issues[:15],  # 显示前15个问题
            "patterns_checked": patterns,
        }

        # 确定结果状态
        if len(issues) == 0:
            status = QualityCheckResult.PASSED
            message = f"未发现硬编码问题 ({len(python_files)} 个文件)"
        elif len(issues) <= 5:
            status = QualityCheckResult.WARNING
            message = f"发现 {len(issues)} 个硬编码问题 (数量可接受)"
        else:
            status = QualityCheckResult.FAILED
            message = f"发现 {len(issues)} 个硬编码问题 (需要修复)"

        return self._create_result("hardcode_detection", status, message, details)
