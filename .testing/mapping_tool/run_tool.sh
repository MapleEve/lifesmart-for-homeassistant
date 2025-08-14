#!/bin/bash
# 获取脚本所在目录（修复硬编码路径问题）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

echo "🚀 开始运行映射工具..."
echo "当前目录: $(pwd)"
echo "Python版本: $(python3 --version)"
echo "开始时间: $(date)"
echo "="*50

# 创建临时目录
mkdir -p tmp

# 运行工具并捕获输出
python3 RUN_THIS_TOOL.py 2>&1 | tee tmp/tool_execution_log.txt

echo "="*50
echo "完成时间: $(date)"
echo "✅ 工具执行完成"