#!/bin/bash
cd "/Volumes/LocalRAW/lifesmart-HACS-for-hass/.testing/mapping_tool"
echo "🚀 开始运行映射工具..."
echo "当前目录: $(pwd)"
echo "Python版本: $(python3 --version)"
echo "开始时间: $(date)"
echo "="*50

# 运行工具并捕获输出
python3 RUN_THIS_TOOL.py 2>&1 | tee tmp/tool_execution_log.txt

echo "="*50
echo "完成时间: $(date)"
echo "✅ 工具执行完成"