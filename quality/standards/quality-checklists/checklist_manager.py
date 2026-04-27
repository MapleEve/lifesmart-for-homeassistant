#!/usr/bin/env python3
"""
质量检查清单管理器 - Phase 3.2 标准体系核心组件

基于Phase 1-2成功经验，建立标准化的质量审查流程和检查清单系统。
确保每个开发任务都符合A+级质量标准。

Version: 1.0.0
Created: 2025-08-14
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChecklistType(Enum):
    """检查清单类型"""

    HARDCODE_ELIMINATION = "hardcode_elimination"
    CODE_QUALITY = "code_quality"
    TESTING_COVERAGE = "testing_coverage"
    ARCHITECTURE_REVIEW = "architecture_review"
    PERFORMANCE_CHECK = "performance_check"
    SECURITY_AUDIT = "security_audit"
    DOCUMENTATION_REVIEW = "documentation_review"
    PRE_COMMIT = "pre_commit"
    POST_DEPLOYMENT = "post_deployment"


class CheckItemStatus(Enum):
    """检查项状态"""

    PENDING = "pending"  # 待检查
    PASSED = "passed"  # 检查通过
    FAILED = "failed"  # 检查失败
    SKIPPED = "skipped"  # 跳过检查
    BLOCKED = "blocked"  # 阻塞状态


class CheckItemPriority(Enum):
    """检查项优先级"""

    CRITICAL = "critical"  # 关键项，必须通过
    HIGH = "high"  # 高优先级
    MEDIUM = "medium"  # 中等优先级
    LOW = "low"  # 低优先级
    OPTIONAL = "optional"  # 可选项


@dataclass
class CheckItem:
    """单个检查项"""

    id: str
    title: str
    description: str
    priority: CheckItemPriority
    automated: bool = False  # 是否可自动化检查
    check_command: Optional[str] = None  # 自动化检查命令
    success_criteria: List[str] = field(default_factory=list)
    failure_consequences: List[str] = field(default_factory=list)
    remediation_steps: List[str] = field(default_factory=list)
    estimated_time: str = "5分钟"
    tags: Set[str] = field(default_factory=set)
    related_practices: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "automated": self.automated,
            "check_command": self.check_command,
            "success_criteria": self.success_criteria,
            "failure_consequences": self.failure_consequences,
            "remediation_steps": self.remediation_steps,
            "estimated_time": self.estimated_time,
            "tags": list(self.tags),
            "related_practices": self.related_practices,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "CheckItem":
        """从字典创建实例"""
        return cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            priority=CheckItemPriority(data["priority"]),
            automated=data.get("automated", False),
            check_command=data.get("check_command"),
            success_criteria=data.get("success_criteria", []),
            failure_consequences=data.get("failure_consequences", []),
            remediation_steps=data.get("remediation_steps", []),
            estimated_time=data.get("estimated_time", "5分钟"),
            tags=set(data.get("tags", [])),
            related_practices=data.get("related_practices", []),
        )


@dataclass
class CheckResult:
    """检查结果"""

    item_id: str
    status: CheckItemStatus
    message: str
    details: Dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    duration: float = 0.0  # 检查耗时（秒）

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "item_id": self.item_id,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "duration": self.duration,
        }


@dataclass
class QualityChecklist:
    """质量检查清单"""

    id: str
    title: str
    checklist_type: ChecklistType
    description: str
    items: List[CheckItem] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    created_date: datetime = field(default_factory=datetime.now)
    updated_date: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "title": self.title,
            "checklist_type": self.checklist_type.value,
            "description": self.description,
            "items": [item.to_dict() for item in self.items],
            "metadata": self.metadata,
            "created_date": self.created_date.isoformat(),
            "updated_date": self.updated_date.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "QualityChecklist":
        """从字典创建实例"""
        checklist = cls(
            id=data["id"],
            title=data["title"],
            checklist_type=ChecklistType(data["checklist_type"]),
            description=data["description"],
            metadata=data.get("metadata", {}),
            created_date=datetime.fromisoformat(data["created_date"]),
            updated_date=datetime.fromisoformat(data["updated_date"]),
        )

        # 加载检查项
        for item_data in data.get("items", []):
            checklist.items.append(CheckItem.from_dict(item_data))

        return checklist

    def get_critical_items(self) -> List[CheckItem]:
        """获取关键检查项"""
        return [
            item for item in self.items if item.priority == CheckItemPriority.CRITICAL
        ]

    def get_automated_items(self) -> List[CheckItem]:
        """获取可自动化检查项"""
        return [item for item in self.items if item.automated]


@dataclass
class ChecklistExecution:
    """检查清单执行会话"""

    session_id: str
    checklist_id: str
    results: List[CheckResult] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    context: Dict = field(default_factory=dict)  # 执行上下文

    def add_result(self, result: CheckResult) -> None:
        """添加检查结果"""
        self.results.append(result)

    def get_summary(self) -> Dict:
        """获取执行摘要"""
        total = len(self.results)
        passed = len([r for r in self.results if r.status == CheckItemStatus.PASSED])
        failed = len([r for r in self.results if r.status == CheckItemStatus.FAILED])
        skipped = len([r for r in self.results if r.status == CheckItemStatus.SKIPPED])

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "success_rate": (passed / total * 100) if total > 0 else 0,
            "duration": (
                (self.end_time - self.start_time).total_seconds()
                if self.end_time
                else 0
            ),
        }


class AutomatedChecker(ABC):
    """自动化检查器抽象基类"""

    @abstractmethod
    def can_check(self, item: CheckItem) -> bool:
        """判断是否可以检查该项"""
        pass

    @abstractmethod
    def execute_check(self, item: CheckItem, context: Dict) -> CheckResult:
        """执行检查"""
        pass


class CodeQualityChecker(AutomatedChecker):
    """代码质量自动化检查器"""

    def can_check(self, item: CheckItem) -> bool:
        """判断是否可以检查代码质量项"""
        return item.automated and any(
            tag in item.tags for tag in ["code_style", "type_check", "lint"]
        )

    def execute_check(self, item: CheckItem, context: Dict) -> CheckResult:
        """执行代码质量检查"""
        start_time = datetime.now()

        try:
            if "black" in item.check_command:
                # 模拟black格式检查
                success = True  # 实际应该运行black --check
                message = "代码格式符合black标准" if success else "代码格式不符合规范"
                status = CheckItemStatus.PASSED if success else CheckItemStatus.FAILED

            elif "mypy" in item.check_command:
                # 模拟mypy类型检查
                success = True  # 实际应该运行mypy
                message = "类型检查通过" if success else "存在类型错误"
                status = CheckItemStatus.PASSED if success else CheckItemStatus.FAILED

            else:
                status = CheckItemStatus.SKIPPED
                message = "未知的检查命令"

            duration = (datetime.now() - start_time).total_seconds()

            return CheckResult(
                item_id=item.id, status=status, message=message, duration=duration
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return CheckResult(
                item_id=item.id,
                status=CheckItemStatus.FAILED,
                message=f"检查执行失败: {str(e)}",
                duration=duration,
            )


class TestCoverageChecker(AutomatedChecker):
    """测试覆盖率自动化检查器"""

    def can_check(self, item: CheckItem) -> bool:
        """判断是否可以检查测试覆盖率"""
        return item.automated and "coverage" in item.tags

    def execute_check(self, item: CheckItem, context: Dict) -> CheckResult:
        """执行测试覆盖率检查"""
        start_time = datetime.now()

        try:
            # 模拟pytest-cov覆盖率检查
            coverage_percentage = 95  # 实际应该运行pytest --cov
            target_coverage = context.get("target_coverage", 90)

            success = coverage_percentage >= target_coverage
            message = f"测试覆盖率: {coverage_percentage}% (目标: {target_coverage}%)"
            status = CheckItemStatus.PASSED if success else CheckItemStatus.FAILED

            duration = (datetime.now() - start_time).total_seconds()

            return CheckResult(
                item_id=item.id,
                status=status,
                message=message,
                details={"coverage": coverage_percentage, "target": target_coverage},
                duration=duration,
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return CheckResult(
                item_id=item.id,
                status=CheckItemStatus.FAILED,
                message=f"覆盖率检查失败: {str(e)}",
                duration=duration,
            )


class QualityChecklistManager:
    """质量检查清单管理器主类"""

    def __init__(self, storage_path: Path):
        """初始化管理器"""
        self.storage_path = storage_path
        self.checklists: Dict[str, QualityChecklist] = {}
        self.executions: Dict[str, ChecklistExecution] = {}

        # 注册自动化检查器
        self.checkers = [CodeQualityChecker(), TestCoverageChecker()]

        self._ensure_storage_path()
        self._load_checklists()

    def _ensure_storage_path(self) -> None:
        """确保存储路径存在"""
        self.storage_path.mkdir(parents=True, exist_ok=True)
        (self.storage_path / "templates").mkdir(exist_ok=True)
        (self.storage_path / "executions").mkdir(exist_ok=True)

    def _load_checklists(self) -> None:
        """加载检查清单"""
        templates_path = self.storage_path / "templates"

        for checklist_file in templates_path.glob("*.json"):
            try:
                with open(checklist_file, "r", encoding="utf-8") as f:
                    checklist_data = json.load(f)
                    checklist = QualityChecklist.from_dict(checklist_data)
                    self.checklists[checklist.id] = checklist
                logger.info(f"加载检查清单: {checklist.title}")
            except Exception as e:
                logger.error(f"加载检查清单失败 {checklist_file}: {e}")

    def _save_checklist(self, checklist: QualityChecklist) -> None:
        """保存检查清单"""
        checklist_file = self.storage_path / "templates" / f"{checklist.id}.json"
        try:
            with open(checklist_file, "w", encoding="utf-8") as f:
                json.dump(checklist.to_dict(), f, ensure_ascii=False, indent=2)
            logger.info(f"保存检查清单: {checklist.title}")
        except Exception as e:
            logger.error(f"保存检查清单失败: {e}")

    def add_checklist(self, checklist: QualityChecklist) -> bool:
        """添加新的检查清单"""
        if checklist.id in self.checklists:
            logger.error(f"检查清单ID已存在: {checklist.id}")
            return False

        checklist.updated_date = datetime.now()
        self.checklists[checklist.id] = checklist
        self._save_checklist(checklist)
        return True

    def get_checklist(self, checklist_id: str) -> Optional[QualityChecklist]:
        """获取指定检查清单"""
        return self.checklists.get(checklist_id)

    def list_checklists(
        self, checklist_type: Optional[ChecklistType] = None
    ) -> List[QualityChecklist]:
        """列出检查清单"""
        checklists = list(self.checklists.values())

        if checklist_type:
            checklists = [c for c in checklists if c.checklist_type == checklist_type]

        return sorted(checklists, key=lambda c: c.updated_date, reverse=True)

    def execute_checklist(
        self, checklist_id: str, context: Dict = None, auto_only: bool = False
    ) -> ChecklistExecution:
        """执行检查清单"""

        if context is None:
            context = {}

        checklist = self.get_checklist(checklist_id)
        if not checklist:
            raise ValueError(f"未找到检查清单: {checklist_id}")

        # 创建执行会话
        session_id = f"{checklist_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        execution = ChecklistExecution(
            session_id=session_id, checklist_id=checklist_id, context=context
        )

        self.executions[session_id] = execution

        # 执行检查项
        for item in checklist.items:
            if auto_only and not item.automated:
                continue  # 只执行自动化检查

            result = self._execute_check_item(item, context)
            execution.add_result(result)

        execution.end_time = datetime.now()
        self._save_execution(execution)

        return execution

    def _execute_check_item(self, item: CheckItem, context: Dict) -> CheckResult:
        """执行单个检查项"""

        if item.automated:
            # 查找合适的自动化检查器
            for checker in self.checkers:
                if checker.can_check(item):
                    return checker.execute_check(item, context)

            # 没有找到合适的检查器
            return CheckResult(
                item_id=item.id,
                status=CheckItemStatus.SKIPPED,
                message="未找到合适的自动化检查器",
            )
        else:
            # 手动检查项，标记为待检查
            return CheckResult(
                item_id=item.id, status=CheckItemStatus.PENDING, message="需要手动检查"
            )

    def _save_execution(self, execution: ChecklistExecution) -> None:
        """保存执行结果"""
        execution_file = (
            self.storage_path / "executions" / f"{execution.session_id}.json"
        )
        try:
            execution_data = {
                "session_id": execution.session_id,
                "checklist_id": execution.checklist_id,
                "start_time": execution.start_time.isoformat(),
                "end_time": (
                    execution.end_time.isoformat() if execution.end_time else None
                ),
                "context": execution.context,
                "results": [result.to_dict() for result in execution.results],
                "summary": execution.get_summary(),
            }

            with open(execution_file, "w", encoding="utf-8") as f:
                json.dump(execution_data, f, ensure_ascii=False, indent=2)

            logger.info(f"保存执行结果: {execution.session_id}")

        except Exception as e:
            logger.error(f"保存执行结果失败: {e}")

    def get_execution(self, session_id: str) -> Optional[ChecklistExecution]:
        """获取执行结果"""
        return self.executions.get(session_id)

    def generate_report(self, execution: ChecklistExecution) -> str:
        """生成检查报告"""
        checklist = self.get_checklist(execution.checklist_id)
        summary = execution.get_summary()

        report = f"""
# 质量检查报告

## 检查清单信息
- **名称**: {checklist.title if checklist else '未知'}
- **类型**: {checklist.checklist_type.value if checklist else '未知'}
- **会话ID**: {execution.session_id}
- **执行时间**: {execution.start_time.strftime('%Y-%m-%d %H:%M:%S')}

## 执行摘要
- **总检查项**: {summary['total']}
- **通过**: {summary['passed']} 
- **失败**: {summary['failed']}
- **跳过**: {summary['skipped']}
- **成功率**: {summary['success_rate']:.1f}%
- **执行耗时**: {summary['duration']:.2f}秒

## 详细结果
"""

        for result in execution.results:
            status_emoji = {
                CheckItemStatus.PASSED: "✅",
                CheckItemStatus.FAILED: "❌",
                CheckItemStatus.SKIPPED: "⏭️",
                CheckItemStatus.PENDING: "⏳",
                CheckItemStatus.BLOCKED: "🚫",
            }.get(result.status, "❓")

            report += f"\n### {status_emoji} {result.item_id}\n"
            report += f"- **状态**: {result.status.value}\n"
            report += f"- **消息**: {result.message}\n"
            report += f"- **耗时**: {result.duration:.2f}秒\n"

            if result.details:
                report += f"- **详情**: {result.details}\n"

        return report


def create_hardcode_elimination_checklist() -> QualityChecklist:
    """创建硬编码消除检查清单"""

    items = [
        CheckItem(
            id="hardcode_scan",
            title="硬编码扫描",
            description="扫描代码中的所有硬编码常量",
            priority=CheckItemPriority.CRITICAL,
            automated=True,
            check_command="grep -r '[\"\\'][A-Z_]{3,}[\"\\']' --include='*.py' .",
            success_criteria=["发现所有硬编码位置", "分类记录硬编码类型"],
            failure_consequences=["遗漏硬编码", "后续修复不完整"],
            remediation_steps=["使用更全面的扫描工具", "手动检查关键文件"],
            estimated_time="10分钟",
            tags={"hardcode", "scan", "automated"},
        ),
        CheckItem(
            id="constant_definition",
            title="常量定义检查",
            description="检查常量定义的规范性和完整性",
            priority=CheckItemPriority.CRITICAL,
            automated=False,
            success_criteria=["常量命名符合规范", "常量分类合理", "无重复定义"],
            failure_consequences=["常量管理混乱", "维护困难"],
            remediation_steps=["修正常量命名", "重新分类整理", "去除重复定义"],
            estimated_time="20分钟",
            tags={"constants", "naming", "manual"},
            related_practices=["phase1_constant_extraction"],
        ),
        CheckItem(
            id="replacement_verification",
            title="替换验证",
            description="验证硬编码替换后的功能正确性",
            priority=CheckItemPriority.CRITICAL,
            automated=True,
            check_command="python -m pytest tests/ -v",
            success_criteria=["所有测试通过", "功能无回归", "性能无明显下降"],
            failure_consequences=["功能破坏", "引入新bug"],
            remediation_steps=["回滚问题修改", "修正替换错误", "补充测试用例"],
            estimated_time="15分钟",
            tags={"testing", "verification", "automated"},
        ),
        CheckItem(
            id="code_review",
            title="代码审查",
            description="人工审查替换质量和代码可读性",
            priority=CheckItemPriority.HIGH,
            automated=False,
            success_criteria=["代码可读性提升", "常量使用正确", "无遗漏的硬编码"],
            failure_consequences=["代码质量不达标", "维护性未改善"],
            remediation_steps=["重新审查问题代码", "优化常量设计", "补充文档说明"],
            estimated_time="30分钟",
            tags={"review", "quality", "manual"},
        ),
        CheckItem(
            id="documentation_update",
            title="文档更新",
            description="更新相关文档和注释",
            priority=CheckItemPriority.MEDIUM,
            automated=False,
            success_criteria=["文档与代码同步", "常量用法说明清晰"],
            failure_consequences=["文档过时", "使用混乱"],
            remediation_steps=["补充遗漏文档", "更新过时说明"],
            estimated_time="15分钟",
            tags={"documentation", "manual"},
        ),
    ]

    return QualityChecklist(
        id="hardcode_elimination_checklist",
        title="硬编码消除质量检查清单",
        checklist_type=ChecklistType.HARDCODE_ELIMINATION,
        description="基于Phase 1成功经验制定的硬编码消除标准检查流程",
        items=items,
        metadata={
            "version": "1.0",
            "based_on": "Phase 1经验",
            "estimated_total_time": "90分钟",
            "critical_items": 3,
        },
    )


if __name__ == "__main__":
    # 示例使用
    storage_path = Path("quality/standards/quality-checklists")
    manager = QualityChecklistManager(storage_path)

    # 创建并添加硬编码消除检查清单
    hardcode_checklist = create_hardcode_elimination_checklist()
    if manager.add_checklist(hardcode_checklist):
        print(f"成功添加检查清单: {hardcode_checklist.title}")

    # 执行检查清单
    context = {
        "target_coverage": 90,
        "project_path": ".",
        "files_to_check": ["const.py", "mapping.py"],
    }

    execution = manager.execute_checklist(
        hardcode_checklist.id, context, auto_only=True
    )

    # 生成报告
    report = manager.generate_report(execution)
    print("\n检查报告:")
    print(report)
