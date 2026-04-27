#!/usr/bin/env python3
"""
质量检查器基类

提供所有检查器的通用接口和基础功能。
"""

import abc
import pathlib
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional

from ..quality_gate import CheckResult, QualityCheckResult


class BaseChecker(abc.ABC):
    """质量检查器基类"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get("enabled", True)

    @abc.abstractmethod
    def check(self, target_paths: List[str]) -> CheckResult:
        """
        执行检查

        Args:
            target_paths: 目标检查路径列表

        Returns:
            CheckResult: 检查结果
        """
        pass

    def _is_enabled(self) -> bool:
        """检查是否启用"""
        return self.enabled

    def _create_result(
        self,
        checker_name: str,
        status: QualityCheckResult,
        message: str,
        details: Dict[str, Any] = None,
        execution_time: float = 0.0,
    ) -> CheckResult:
        """创建检查结果"""
        return CheckResult(
            checker=checker_name,
            status=status,
            message=message,
            details=details or {},
            execution_time=execution_time,
            timestamp=datetime.now().isoformat(),
        )

    def _run_command(
        self, cmd: List[str], cwd: Optional[str] = None, timeout: int = 60
    ) -> subprocess.CompletedProcess:
        """运行命令行工具"""
        return subprocess.run(
            cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout
        )

    def _filter_python_files(self, paths: List[str]) -> List[pathlib.Path]:
        """过滤Python文件"""
        python_files = []
        for path_str in paths:
            path = pathlib.Path(path_str)
            if path.is_file() and path.suffix == ".py":
                python_files.append(path)
            elif path.is_dir():
                python_files.extend(path.rglob("*.py"))
        return python_files

    def _exclude_files(
        self, files: List[pathlib.Path], exclude_patterns: List[str]
    ) -> List[pathlib.Path]:
        """排除匹配模式的文件"""
        if not exclude_patterns:
            return files

        filtered = []
        for file_path in files:
            should_exclude = any(
                pattern in str(file_path) for pattern in exclude_patterns
            )
            if not should_exclude:
                filtered.append(file_path)

        return filtered
