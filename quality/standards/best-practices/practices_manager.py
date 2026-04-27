#!/usr/bin/env python3
"""
最佳实践管理器 - Phase 3.2 标准体系核心组件

基于Phase 1-2的98个硬编码修复经验，建立可复用的最佳实践管理系统。
严格遵循A+级Python代码质量标准。

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


class PracticeCategory(Enum):
    """最佳实践分类枚举"""

    HARDCODE_ELIMINATION = "hardcode_elimination"
    CODE_QUALITY = "code_quality"
    TESTING_STRATEGY = "testing_strategy"
    ARCHITECTURE_DESIGN = "architecture_design"
    ERROR_HANDLING = "error_handling"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    DOCUMENTATION = "documentation"


class PracticeStatus(Enum):
    """实践状态枚举"""

    DRAFT = "draft"
    VALIDATED = "validated"
    ACTIVE = "active"
    DEPRECATED = "deprecated"


@dataclass
class BestPractice:
    """最佳实践数据模型"""

    id: str
    title: str
    category: PracticeCategory
    description: str
    problem_statement: str
    solution_approach: str
    implementation_steps: List[str]
    code_examples: List[str] = field(default_factory=list)
    related_files: List[str] = field(default_factory=list)
    success_metrics: List[str] = field(default_factory=list)
    common_pitfalls: List[str] = field(default_factory=list)
    status: PracticeStatus = PracticeStatus.DRAFT
    tags: Set[str] = field(default_factory=set)
    created_date: datetime = field(default_factory=datetime.now)
    updated_date: datetime = field(default_factory=datetime.now)
    source_phase: str = ""
    validation_count: int = 0

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category.value,
            "description": self.description,
            "problem_statement": self.problem_statement,
            "solution_approach": self.solution_approach,
            "implementation_steps": self.implementation_steps,
            "code_examples": self.code_examples,
            "related_files": self.related_files,
            "success_metrics": self.success_metrics,
            "common_pitfalls": self.common_pitfalls,
            "status": self.status.value,
            "tags": list(self.tags),
            "created_date": self.created_date.isoformat(),
            "updated_date": self.updated_date.isoformat(),
            "source_phase": self.source_phase,
            "validation_count": self.validation_count,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "BestPractice":
        """从字典创建实例"""
        return cls(
            id=data["id"],
            title=data["title"],
            category=PracticeCategory(data["category"]),
            description=data["description"],
            problem_statement=data["problem_statement"],
            solution_approach=data["solution_approach"],
            implementation_steps=data["implementation_steps"],
            code_examples=data.get("code_examples", []),
            related_files=data.get("related_files", []),
            success_metrics=data.get("success_metrics", []),
            common_pitfalls=data.get("common_pitfalls", []),
            status=PracticeStatus(data.get("status", "draft")),
            tags=set(data.get("tags", [])),
            created_date=datetime.fromisoformat(data["created_date"]),
            updated_date=datetime.fromisoformat(data["updated_date"]),
            source_phase=data.get("source_phase", ""),
            validation_count=data.get("validation_count", 0),
        )


class PracticeValidator(ABC):
    """最佳实践验证器抽象基类"""

    @abstractmethod
    def validate(self, practice: BestPractice) -> tuple[bool, List[str]]:
        """验证实践是否符合标准"""
        pass


class StandardPracticeValidator(PracticeValidator):
    """标准实践验证器"""

    def validate(self, practice: BestPractice) -> tuple[bool, List[str]]:
        """验证实践完整性和质量"""
        errors = []

        # 基本完整性检查
        if not practice.title.strip():
            errors.append("标题不能为空")

        if not practice.description.strip():
            errors.append("描述不能为空")

        if not practice.problem_statement.strip():
            errors.append("问题陈述不能为空")

        if not practice.solution_approach.strip():
            errors.append("解决方案不能为空")

        if not practice.implementation_steps:
            errors.append("实施步骤不能为空")

        # 质量标准检查
        if len(practice.implementation_steps) < 3:
            errors.append("实施步骤应至少包含3个步骤")

        if not practice.success_metrics:
            errors.append("应定义成功指标")

        # 分类一致性检查
        if practice.category == PracticeCategory.HARDCODE_ELIMINATION:
            if "hardcode" not in practice.description.lower():
                errors.append("硬编码消除实践应在描述中提及硬编码")

        return len(errors) == 0, errors


class BestPracticesManager:
    """最佳实践管理器主类"""

    def __init__(self, storage_path: Path):
        """初始化管理器"""
        self.storage_path = storage_path
        self.practices: Dict[str, BestPractice] = {}
        self.validator = StandardPracticeValidator()
        self._ensure_storage_path()
        self._load_practices()

    def _ensure_storage_path(self) -> None:
        """确保存储路径存在"""
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def _load_practices(self) -> None:
        """从存储加载实践"""
        practices_file = self.storage_path / "practices.json"
        if practices_file.exists():
            try:
                with open(practices_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for practice_data in data.get("practices", []):
                        practice = BestPractice.from_dict(practice_data)
                        self.practices[practice.id] = practice
                logger.info(f"加载了 {len(self.practices)} 个最佳实践")
            except Exception as e:
                logger.error(f"加载实践失败: {e}")

    def _save_practices(self) -> None:
        """保存实践到存储"""
        practices_file = self.storage_path / "practices.json"
        try:
            data = {
                "metadata": {
                    "version": "1.0.0",
                    "updated": datetime.now().isoformat(),
                    "count": len(self.practices),
                },
                "practices": [
                    practice.to_dict() for practice in self.practices.values()
                ],
            }
            with open(practices_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"保存了 {len(self.practices)} 个最佳实践")
        except Exception as e:
            logger.error(f"保存实践失败: {e}")

    def add_practice(self, practice: BestPractice) -> bool:
        """添加新的最佳实践"""
        # 验证实践
        is_valid, errors = self.validator.validate(practice)
        if not is_valid:
            logger.error(f"实践验证失败: {', '.join(errors)}")
            return False

        # 检查ID冲突
        if practice.id in self.practices:
            logger.error(f"实践ID已存在: {practice.id}")
            return False

        # 添加实践
        practice.updated_date = datetime.now()
        self.practices[practice.id] = practice
        self._save_practices()
        logger.info(f"成功添加实践: {practice.title}")
        return True

    def update_practice(self, practice_id: str, updates: Dict) -> bool:
        """更新现有实践"""
        if practice_id not in self.practices:
            logger.error(f"未找到实践: {practice_id}")
            return False

        practice = self.practices[practice_id]

        # 应用更新
        for key, value in updates.items():
            if hasattr(practice, key):
                setattr(practice, key, value)

        practice.updated_date = datetime.now()

        # 重新验证
        is_valid, errors = self.validator.validate(practice)
        if not is_valid:
            logger.error(f"更新后验证失败: {', '.join(errors)}")
            return False

        self._save_practices()
        logger.info(f"成功更新实践: {practice.title}")
        return True

    def get_practice(self, practice_id: str) -> Optional[BestPractice]:
        """获取指定实践"""
        return self.practices.get(practice_id)

    def list_practices(
        self,
        category: Optional[PracticeCategory] = None,
        status: Optional[PracticeStatus] = None,
        tags: Optional[Set[str]] = None,
    ) -> List[BestPractice]:
        """列出符合条件的实践"""
        practices = list(self.practices.values())

        if category:
            practices = [p for p in practices if p.category == category]

        if status:
            practices = [p for p in practices if p.status == status]

        if tags:
            practices = [p for p in practices if p.tags.intersection(tags)]

        return sorted(practices, key=lambda p: p.updated_date, reverse=True)

    def search_practices(self, query: str) -> List[BestPractice]:
        """搜索实践"""
        query_lower = query.lower()
        results = []

        for practice in self.practices.values():
            if (
                query_lower in practice.title.lower()
                or query_lower in practice.description.lower()
                or query_lower in practice.problem_statement.lower()
                or any(query_lower in tag.lower() for tag in practice.tags)
            ):
                results.append(practice)

        return sorted(results, key=lambda p: p.validation_count, reverse=True)

    def validate_practice(self, practice_id: str) -> bool:
        """验证并标记实践为已验证"""
        if practice_id not in self.practices:
            return False

        practice = self.practices[practice_id]
        practice.validation_count += 1
        practice.status = PracticeStatus.VALIDATED
        practice.updated_date = datetime.now()

        self._save_practices()
        return True

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        total = len(self.practices)
        by_category = {}
        by_status = {}

        for practice in self.practices.values():
            category = practice.category.value
            status = practice.status.value

            by_category[category] = by_category.get(category, 0) + 1
            by_status[status] = by_status.get(status, 0) + 1

        return {
            "total_practices": total,
            "by_category": by_category,
            "by_status": by_status,
            "most_validated": max(
                self.practices.values(), key=lambda p: p.validation_count, default=None
            ),
            "latest_updated": max(
                self.practices.values(), key=lambda p: p.updated_date, default=None
            ),
        }


def create_phase1_hardcode_practices(manager: BestPracticesManager) -> None:
    """基于Phase 1经验创建硬编码消除实践"""

    # 实践1: 常量提取和集中管理
    practice1 = BestPractice(
        id="phase1_constant_extraction",
        title="常量提取和集中管理",
        category=PracticeCategory.HARDCODE_ELIMINATION,
        description="将散布在代码中的硬编码字符串和数值提取为常量，实现集中管理",
        problem_statement="代码中存在大量硬编码的字符串、数值等常量，难以维护和修改",
        solution_approach="建立统一的常量定义文件，按功能模块分类管理所有常量",
        implementation_steps=[
            "识别代码中的所有硬编码常量",
            "按功能和模块对常量进行分类",
            "在const.py文件中定义相应的常量",
            "替换代码中的硬编码为常量引用",
            "验证功能正确性并运行测试",
        ],
        code_examples=[
            "# 之前: hardcoded\nif device_type == 'SL_SW_TH':\n    return 'switch'\n\n# 之后: 使用常量\nif device_type == DEVICE_TYPES.SL_SW_TH:\n    return PLATFORM_SWITCH"
        ],
        success_metrics=[
            "硬编码数量减少 > 95%",
            "代码可读性显著提升",
            "测试覆盖率保持或提升",
        ],
        common_pitfalls=[
            "常量命名不规范",
            "过度拆分导致常量过多",
            "忘记更新相关测试代码",
        ],
        source_phase="Phase 1",
        tags={"hardcode", "constants", "maintainability"},
    )

    # 实践2: 映射表驱动设计
    practice2 = BestPractice(
        id="phase1_mapping_driven_design",
        title="映射表驱动设计",
        category=PracticeCategory.ARCHITECTURE_DESIGN,
        description="使用映射表替代复杂的if-elif判断链，提高代码可维护性",
        problem_statement="复杂的条件判断逻辑难以维护，新增分支时容易出错",
        solution_approach="建立映射表，将条件和结果的对应关系数据化",
        implementation_steps=[
            "分析现有的条件判断逻辑",
            "识别可以用映射表表示的模式",
            "设计映射表结构和数据格式",
            "实现映射表查找逻辑",
            "重构原有代码使用映射表",
            "添加映射表的测试覆盖",
        ],
        code_examples=[
            "# 映射表设计\nDEVICE_PLATFORM_MAPPING = {\n    DEVICE_TYPES.SL_SW_TH: PLATFORM_SWITCH,\n    DEVICE_TYPES.SL_LI_WW: PLATFORM_LIGHT,\n}\n\n# 使用映射表\ndef get_platform(device_type):\n    return DEVICE_PLATFORM_MAPPING.get(device_type, PLATFORM_UNKNOWN)"
        ],
        success_metrics=[
            "代码行数减少 > 50%",
            "圈复杂度显著降低",
            "新增功能时修改点减少",
        ],
        source_phase="Phase 1",
        tags={"mapping", "architecture", "complexity"},
    )

    manager.add_practice(practice1)
    manager.add_practice(practice2)


if __name__ == "__main__":
    # 示例使用
    storage_path = Path("quality/standards/best-practices")
    manager = BestPracticesManager(storage_path)

    # 创建基于Phase 1经验的实践
    create_phase1_hardcode_practices(manager)

    # 显示统计信息
    stats = manager.get_statistics()
    print(f"最佳实践管理器启动成功，共有 {stats['total_practices']} 个实践")
    for category, count in stats["by_category"].items():
        print(f"  {category}: {count} 个实践")
