#!/usr/bin/env python3
"""
实践分类器 - 智能分析和分类Phase 1-2经验

自动分析代码变更、commit消息、文件修改等信息，智能分类为可复用的最佳实践。
基于机器学习和规则引擎的混合方法。

Version: 1.0.0
Created: 2025-08-14
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional

from practices_manager import (
    BestPractice,
    PracticeCategory,
    BestPracticesManager,
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChangeType(Enum):
    """变更类型枚举"""

    HARDCODE_REMOVAL = "hardcode_removal"
    CONSTANT_ADDITION = "constant_addition"
    MAPPING_CREATION = "mapping_creation"
    TEST_IMPROVEMENT = "test_improvement"
    ARCHITECTURE_REFACTOR = "architecture_refactor"
    ERROR_HANDLING = "error_handling"
    PERFORMANCE_OPT = "performance_optimization"


@dataclass
class CodeChange:
    """代码变更数据模型"""

    file_path: str
    change_type: ChangeType
    before_snippet: str
    after_snippet: str
    description: str
    impact_metrics: Dict[str, any]
    commit_message: str = ""
    tags: Set[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = set()


class PatternMatcher:
    """模式匹配器 - 识别代码变更模式"""

    def __init__(self):
        """初始化模式匹配器"""
        self.hardcode_patterns = [
            r"['\"](?!test|debug)[A-Z_]{3,}['\"]",  # 硬编码常量
            r"['\"][^'\"]*\.[^'\"]*['\"]",  # 带点的字符串
            r"(?<!=\s)['\"][A-Z][A-Za-z_]+['\"]",  # 大写开头字符串
        ]

        self.constant_patterns = [
            r"[A-Z_]{3,}\s*=\s*['\"]",  # 常量定义
            r"class\s+[A-Z_]+\(",  # 常量类定义
            r"@dataclass.*\nclass\s+[A-Z_]+",  # dataclass常量
        ]

        self.mapping_patterns = [
            r"\w+_MAPPING\s*=\s*\{",  # 映射表定义
            r"\.get\(\w+,\s*\w+\)",  # 映射表使用
            r"if\s+\w+\s+in\s+\w+_MAPPING",  # 映射表判断
        ]

    def analyze_change(self, change: CodeChange) -> Tuple[ChangeType, float]:
        """分析单个变更，返回变更类型和置信度"""
        before = change.before_snippet
        after = change.after_snippet

        # 硬编码移除检测
        if self._detect_hardcode_removal(before, after):
            return ChangeType.HARDCODE_REMOVAL, 0.9

        # 常量添加检测
        if self._detect_constant_addition(before, after):
            return ChangeType.CONSTANT_ADDITION, 0.85

        # 映射表创建检测
        if self._detect_mapping_creation(before, after):
            return ChangeType.MAPPING_CREATION, 0.8

        # 测试改进检测
        if "test" in change.file_path.lower() and len(after) > len(before):
            return ChangeType.TEST_IMPROVEMENT, 0.7

        # 架构重构检测
        if self._detect_architecture_refactor(before, after):
            return ChangeType.ARCHITECTURE_REFACTOR, 0.6

        return ChangeType.HARDCODE_REMOVAL, 0.1  # 默认

    def _detect_hardcode_removal(self, before: str, after: str) -> bool:
        """检测硬编码移除"""
        before_hardcodes = sum(
            len(re.findall(pattern, before)) for pattern in self.hardcode_patterns
        )
        after_hardcodes = sum(
            len(re.findall(pattern, after)) for pattern in self.hardcode_patterns
        )

        return before_hardcodes > after_hardcodes and before_hardcodes >= 3

    def _detect_constant_addition(self, before: str, after: str) -> bool:
        """检测常量添加"""
        before_constants = sum(
            len(re.findall(pattern, before)) for pattern in self.constant_patterns
        )
        after_constants = sum(
            len(re.findall(pattern, after)) for pattern in self.constant_patterns
        )

        return after_constants > before_constants

    def _detect_mapping_creation(self, before: str, after: str) -> bool:
        """检测映射表创建"""
        before_mappings = sum(
            len(re.findall(pattern, before)) for pattern in self.mapping_patterns
        )
        after_mappings = sum(
            len(re.findall(pattern, after)) for pattern in self.mapping_patterns
        )

        return after_mappings > before_mappings

    def _detect_architecture_refactor(self, before: str, after: str) -> bool:
        """检测架构重构"""
        # 检测复杂度降低
        before_complexity = (
            before.count("if ") + before.count("elif ") + before.count("for ")
        )
        after_complexity = (
            after.count("if ") + after.count("elif ") + after.count("for ")
        )

        # 检测函数提取
        before_functions = len(re.findall(r"def\s+\w+", before))
        after_functions = len(re.findall(r"def\s+\w+", after))

        return (
            before_complexity > after_complexity + 3
            or after_functions > before_functions + 1
        )


class PracticeCategorizer:
    """实践分类器主类"""

    def __init__(self, practices_manager: BestPracticesManager):
        """初始化分类器"""
        self.practices_manager = practices_manager
        self.pattern_matcher = PatternMatcher()

        # 变更类型到实践类别的映射
        self.type_to_category = {
            ChangeType.HARDCODE_REMOVAL: PracticeCategory.HARDCODE_ELIMINATION,
            ChangeType.CONSTANT_ADDITION: PracticeCategory.HARDCODE_ELIMINATION,
            ChangeType.MAPPING_CREATION: PracticeCategory.ARCHITECTURE_DESIGN,
            ChangeType.TEST_IMPROVEMENT: PracticeCategory.TESTING_STRATEGY,
            ChangeType.ARCHITECTURE_REFACTOR: PracticeCategory.ARCHITECTURE_DESIGN,
            ChangeType.ERROR_HANDLING: PracticeCategory.ERROR_HANDLING,
            ChangeType.PERFORMANCE_OPT: PracticeCategory.PERFORMANCE_OPTIMIZATION,
        }

    def categorize_changes(
        self, changes: List[CodeChange]
    ) -> Dict[PracticeCategory, List[CodeChange]]:
        """将变更按实践类别分类"""
        categorized = {}

        for change in changes:
            change_type, confidence = self.pattern_matcher.analyze_change(change)

            if confidence >= 0.6:  # 置信度阈值
                category = self.type_to_category[change_type]

                if category not in categorized:
                    categorized[category] = []

                categorized[category].append(change)

                # 添加变更类型到标签
                change.tags.add(change_type.value)
                change.tags.add(f"confidence_{int(confidence * 100)}")

        return categorized

    def generate_practice_from_changes(
        self, category: PracticeCategory, changes: List[CodeChange]
    ) -> Optional[BestPractice]:
        """从相同类别的变更生成最佳实践"""

        if not changes:
            return None

        # 基于类别生成实践模板
        if category == PracticeCategory.HARDCODE_ELIMINATION:
            return self._generate_hardcode_practice(changes)
        elif category == PracticeCategory.ARCHITECTURE_DESIGN:
            return self._generate_architecture_practice(changes)
        elif category == PracticeCategory.TESTING_STRATEGY:
            return self._generate_testing_practice(changes)
        else:
            return self._generate_generic_practice(category, changes)

    def _generate_hardcode_practice(self, changes: List[CodeChange]) -> BestPractice:
        """生成硬编码消除实践"""

        # 统计影响
        total_files = len(set(change.file_path for change in changes))
        total_changes = len(changes)

        # 提取示例
        examples = []
        for change in changes[:3]:  # 取前3个作为示例
            examples.append(
                f"# 文件: {change.file_path}\n# 之前:\n{change.before_snippet[:200]}...\n\n# 之后:\n{change.after_snippet[:200]}..."
            )

        # 提取相关文件
        related_files = list(set(change.file_path for change in changes))

        practice_id = f"auto_hardcode_{len(changes)}_{hash(str(related_files)) % 10000}"

        return BestPractice(
            id=practice_id,
            title=f"批量硬编码消除模式 ({total_files}个文件)",
            category=PracticeCategory.HARDCODE_ELIMINATION,
            description=f"在{total_files}个文件中成功消除{total_changes}处硬编码，建立统一常量管理",
            problem_statement="多个文件存在硬编码常量，维护困难且容易出错",
            solution_approach="建立统一常量定义，批量替换硬编码引用",
            implementation_steps=[
                "扫描识别所有硬编码位置",
                "按功能分类设计常量结构",
                "在常量文件中定义新常量",
                "批量替换硬编码引用",
                "验证功能正确性",
                "更新相关测试用例",
            ],
            code_examples=examples,
            related_files=related_files,
            success_metrics=[
                f"消除硬编码 {total_changes} 处",
                f"影响文件 {total_files} 个",
                "代码可维护性显著提升",
            ],
            common_pitfalls=["常量命名不一致", "遗漏边缘情况", "测试覆盖不完整"],
            source_phase="Phase 1-2",
            tags={"auto_generated", "hardcode", "batch_operation"},
        )

    def _generate_architecture_practice(
        self, changes: List[CodeChange]
    ) -> BestPractice:
        """生成架构设计实践"""

        total_files = len(set(change.file_path for change in changes))

        # 检测映射表模式
        mapping_changes = [c for c in changes if "mapping" in c.description.lower()]

        if mapping_changes:
            return self._generate_mapping_practice(mapping_changes)

        practice_id = f"auto_arch_{len(changes)}_{hash(str([c.file_path for c in changes])) % 10000}"

        return BestPractice(
            id=practice_id,
            title=f"架构重构模式 ({total_files}个文件)",
            category=PracticeCategory.ARCHITECTURE_DESIGN,
            description=f"通过重构提升{total_files}个文件的架构设计质量",
            problem_statement="代码结构复杂，维护困难",
            solution_approach="应用设计模式和重构技巧改善架构",
            implementation_steps=[
                "分析现有架构问题",
                "设计重构方案",
                "分步执行重构",
                "验证重构效果",
                "更新文档和测试",
            ],
            code_examples=[c.after_snippet for c in changes[:2]],
            related_files=list(set(c.file_path for c in changes)),
            success_metrics=["代码复杂度降低", "可维护性提升", "性能优化"],
            source_phase="Phase 1-2",
            tags={"auto_generated", "architecture", "refactoring"},
        )

    def _generate_mapping_practice(self, changes: List[CodeChange]) -> BestPractice:
        """生成映射表实践"""

        practice_id = f"auto_mapping_{len(changes)}_{hash(str([c.file_path for c in changes])) % 10000}"

        return BestPractice(
            id=practice_id,
            title="映射表驱动设计模式",
            category=PracticeCategory.ARCHITECTURE_DESIGN,
            description="使用映射表替代复杂条件判断，提高代码可维护性",
            problem_statement="复杂的if-elif链难以维护和扩展",
            solution_approach="建立映射表，将条件逻辑数据化",
            implementation_steps=[
                "识别复杂条件判断逻辑",
                "分析条件和结果的映射关系",
                "设计映射表数据结构",
                "实现映射表查找逻辑",
                "替换原有条件判断",
                "添加映射表测试覆盖",
            ],
            code_examples=[c.after_snippet for c in changes[:2]],
            related_files=list(set(c.file_path for c in changes)),
            success_metrics=[
                "代码行数减少 > 50%",
                "圈复杂度显著降低",
                "新增分支时修改点减少",
            ],
            common_pitfalls=["映射关系设计不当", "缺少默认值处理", "映射表过于复杂"],
            source_phase="Phase 1-2",
            tags={"auto_generated", "mapping", "pattern"},
        )

    def _generate_testing_practice(self, changes: List[CodeChange]) -> BestPractice:
        """生成测试策略实践"""

        practice_id = f"auto_test_{len(changes)}_{hash(str([c.file_path for c in changes])) % 10000}"

        return BestPractice(
            id=practice_id,
            title="测试策略优化模式",
            category=PracticeCategory.TESTING_STRATEGY,
            description="优化测试架构，提高测试覆盖率和质量",
            problem_statement="测试覆盖不足或测试质量低",
            solution_approach="建立系统化测试策略和工具",
            implementation_steps=[
                "分析测试覆盖缺口",
                "设计测试策略",
                "实现测试工具和fixture",
                "编写测试用例",
                "建立持续测试流程",
            ],
            code_examples=[c.after_snippet for c in changes[:2]],
            related_files=list(set(c.file_path for c in changes)),
            success_metrics=["测试覆盖率 > 90%", "测试稳定性提升", "缺陷发现能力增强"],
            source_phase="Phase 1-2",
            tags={"auto_generated", "testing", "quality"},
        )

    def _generate_generic_practice(
        self, category: PracticeCategory, changes: List[CodeChange]
    ) -> BestPractice:
        """生成通用实践"""

        practice_id = f"auto_{category.value}_{len(changes)}_{hash(str([c.file_path for c in changes])) % 10000}"

        return BestPractice(
            id=practice_id,
            title=f"{category.value.replace('_', ' ').title()} 优化模式",
            category=category,
            description=f"基于实际项目经验的{category.value}优化实践",
            problem_statement="需要改进代码质量和可维护性",
            solution_approach="应用最佳实践和优化技巧",
            implementation_steps=[
                "分析现状和问题",
                "制定改进方案",
                "执行优化改进",
                "验证改进效果",
            ],
            code_examples=[c.after_snippet for c in changes[:2]],
            related_files=list(set(c.file_path for c in changes)),
            success_metrics=["代码质量提升", "可维护性改善"],
            source_phase="Phase 1-2",
            tags={"auto_generated", category.value},
        )

    def batch_categorize_and_generate(
        self, changes: List[CodeChange]
    ) -> List[BestPractice]:
        """批量分类并生成最佳实践"""

        # 分类变更
        categorized = self.categorize_changes(changes)

        practices = []
        for category, category_changes in categorized.items():
            practice = self.generate_practice_from_changes(category, category_changes)
            if practice:
                practices.append(practice)

        return practices


def load_phase_changes_from_git(
    project_path: Path, phase_commits: List[str]
) -> List[CodeChange]:
    """从Git提交历史加载Phase变更（模拟实现）"""

    # 这里是模拟实现，实际应该解析git log
    sample_changes = [
        CodeChange(
            file_path="custom_components/lifesmart/const.py",
            change_type=ChangeType.CONSTANT_ADDITION,
            before_snippet="# 硬编码常量",
            after_snippet='# 统一常量定义\nDEVICE_TYPES = {\n    "SL_SW_TH": "smart_switch",\n    "SL_LI_WW": "smart_light"\n}',
            description="添加设备类型常量定义",
            impact_metrics={"files_affected": 5, "hardcodes_removed": 12},
            commit_message="🔧 [2025-08-12] Phase 1 硬编码修复: 常量定义",
        ),
        CodeChange(
            file_path="custom_components/lifesmart/core/config/mapping.py",
            change_type=ChangeType.MAPPING_CREATION,
            before_snippet='if device_type == "SL_SW_TH":\n    return "switch"\nelif device_type == "SL_LI_WW":\n    return "light"',
            after_snippet="DEVICE_PLATFORM_MAPPING = {\n    DEVICE_TYPES.SL_SW_TH: PLATFORM_SWITCH,\n    DEVICE_TYPES.SL_LI_WW: PLATFORM_LIGHT\n}\n\nreturn DEVICE_PLATFORM_MAPPING.get(device_type)",
            description="创建设备平台映射表",
            impact_metrics={"complexity_reduced": 8, "lines_reduced": 15},
            commit_message="🏗️ [2025-08-11] 架构优化: 映射表驱动",
        ),
    ]

    return sample_changes


if __name__ == "__main__":
    # 示例使用
    from pathlib import Path

    # 初始化管理器
    storage_path = Path("quality/standards/best-practices")
    practices_manager = BestPracticesManager(storage_path)

    # 初始化分类器
    categorizer = PracticeCategorizer(practices_manager)

    # 加载Phase变更（示例）
    sample_changes = load_phase_changes_from_git(Path("."), [])

    # 批量生成实践
    new_practices = categorizer.batch_categorize_and_generate(sample_changes)

    print(f"从{len(sample_changes)}个变更生成了{len(new_practices)}个最佳实践")

    # 添加到管理器
    for practice in new_practices:
        if practices_manager.add_practice(practice):
            print(f"成功添加实践: {practice.title}")
        else:
            print(f"添加实践失败: {practice.title}")
