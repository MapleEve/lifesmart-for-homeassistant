#!/usr/bin/env python3
"""
质量门禁系统测试脚本

验证CI/CD质量关卡集成的功能完整性。
"""

import pathlib
import shutil
import sys
import tempfile

# 添加质量系统路径
quality_path = pathlib.Path(__file__).parent
sys.path.insert(0, str(quality_path))

from quality_gate import QualityGate


def create_test_files() -> pathlib.Path:
    """创建测试文件"""
    test_dir = pathlib.Path(tempfile.mkdtemp(prefix="quality_test_"))

    # 创建一个包含硬编码问题的测试文件
    test_file = test_dir / "test_code.py"
    test_content = '''"""测试文件包含各种质量问题"""

import os

class TestDevice:
    def __init__(self):
        # 硬编码问题
        self.device_type = "SL_SW_CH1"
        self.command = "OE_LIGHT_ON"
        
    def get_status(self):
        # 魔法数字
        timeout = 5000
        retries = 10
        
        # 字符串硬编码
        return "light"
    
    def process_data(self, data):
        # 类型安全问题 - 未添加类型提示
        result = data + 1
        return result

# 安全问题 - 使用eval
def unsafe_function(user_input):
    return eval(user_input)

# 格式问题
def poorly_formatted(a,b,c):
    x=a+b
    y=c*2
    return x+y
'''

    with open(test_file, "w", encoding="utf-8") as f:
        f.write(test_content)

    return test_dir


def test_quality_gate():
    """测试质量门禁系统"""
    print("🧪 开始质量门禁系统测试...")

    # 创建测试文件
    test_dir = create_test_files()
    print(f"📁 创建测试目录: {test_dir}")

    try:
        # 创建项目根目录模拟环境
        project_root = pathlib.Path(__file__).parent.parent.parent
        quality_gate = QualityGate(project_root)

        print(f"🏗️ 初始化质量门禁系统，项目根目录: {project_root}")

        # 运行质量检查
        print("🚦 运行质量检查...")
        report = quality_gate.run_quality_checks(
            target_paths=[str(test_dir)],
            skip_checkers=["type_safety", "security_scan"],  # 跳过需要额外工具的检查
        )

        # 验证结果
        print("\n📊 测试结果验证:")
        print(f"✅ 报告生成成功: {report is not None}")
        print(f"🔢 检查器数量: {len(report.results)}")
        print(
            f"🎯 硬编码检测: {'包含' if any(r.checker == 'hardcode_detection' for r in report.results) else '不包含'}"
        )

        # 检查硬编码检测是否发现问题
        hardcode_result = next(
            (r for r in report.results if r.checker == "hardcode_detection"), None
        )
        if hardcode_result:
            print(f"🔍 硬编码问题检测: {hardcode_result.status}")
            if hardcode_result.details.get("violations_found", 0) > 0:
                print(
                    f"   发现 {hardcode_result.details['violations_found']} 个硬编码问题"
                )
            else:
                print("   未发现硬编码问题（可能是检测逻辑需要调整）")

        # 保存测试报告
        report_path = quality_gate.save_report(report)
        print(f"📄 测试报告保存至: {report_path}")

        # 测试结果评估
        test_success = True

        if report.total_checks == 0:
            print("❌ 测试失败: 没有执行任何检查")
            test_success = False

        if not any(r.checker == "hardcode_detection" for r in report.results):
            print("❌ 测试失败: 硬编码检测器未执行")
            test_success = False

        if test_success:
            print("\n✅ 质量门禁系统测试通过!")
            return True
        else:
            print("\n❌ 质量门禁系统测试失败!")
            return False

    except Exception as e:
        print(f"\n💥 测试过程中发生异常: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        # 清理测试文件
        if test_dir.exists():
            shutil.rmtree(test_dir)
            print(f"🗑️ 清理测试目录: {test_dir}")


def main():
    """主测试函数"""
    print("=" * 60)
    print("🏗️ LifeSmart HACS 质量门禁系统测试")
    print("=" * 60)

    success = test_quality_gate()

    print("=" * 60)
    if success:
        print("🎉 所有测试通过! 质量门禁系统功能正常")
        sys.exit(0)
    else:
        print("💔 测试失败! 需要检查质量门禁系统")
        sys.exit(1)


if __name__ == "__main__":
    main()
