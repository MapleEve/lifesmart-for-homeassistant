#!/usr/bin/env bash

# 本地CI兼容性测试脚本
# 模拟GitHub Actions环境，测试不同HA版本组合
# 
# 特别修复: macOS ARM64 Python 3.11 lru-dict编译问题
# 使用双fork解决方案：
# - Fork 1: pytest-homeassistant-custom-component (修复setup.py和版本兼容性)
# - Fork 2: Home Assistant 2023.6.0 (移除lru-dict依赖冲突)
# 解决方案详情: https://github.com/MapleEve/pytest-homeassistant-custom-component-fixed/tree/macos-fix-branch
#              https://github.com/MapleEve/homeassistant-lru-dict-macos-fix/tree/macos-fix-branch

set -e

# 项目根目录自动检测和切换 (支持Windows/Linux/macOS/WSL/WSL2)
auto_detect_and_switch_to_project_root() {
  # 获取脚本所在目录的绝对路径
  local script_dir
  
  # 检测不同平台环境
  if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ -n "${MSYSTEM:-}" ]]; then
    # Windows环境 (Git Bash/MSYS2/Cygwin)
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -W 2>/dev/null || pwd)"
  elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if grep -qE "(Microsoft|microsoft)" /proc/version 2>/dev/null; then
      # WSL/WSL2环境
      script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
      # WSL路径可能需要特殊处理，但通常标准pwd即可
    else
      # 标准Linux环境
      script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    fi
  elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS环境
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  else
    # 其他环境，使用标准方法
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  fi
  
  # 推导项目根目录 (.testing目录的父目录)
  local project_root="$(dirname "$script_dir")"
  
  # 验证项目根目录的有效性 (检查关键文件/目录是否存在)
  local validation_failed=false
  local missing_items=()
  
  if [ ! -d "$project_root/custom_components" ]; then
    validation_failed=true
    missing_items+=("custom_components/")
  fi
  
  if [ ! -d "$project_root/custom_components/lifesmart" ]; then
    validation_failed=true
    missing_items+=("custom_components/lifesmart/")
  fi
  
  if [ ! -f "$project_root/custom_components/lifesmart/manifest.json" ]; then
    validation_failed=true
    missing_items+=("custom_components/lifesmart/manifest.json")
  fi
  
  if [ ! -f "$project_root/hacs.json" ]; then
    validation_failed=true
    missing_items+=("hacs.json")
  fi
  
  # 如果验证失败，显示错误信息
  if [ "$validation_failed" = true ]; then
    echo -e "${RED}❌ 项目根目录验证失败！${NC}"
    echo -e "${YELLOW}推导的项目根目录: $project_root${NC}"
    echo -e "${YELLOW}缺少以下关键文件/目录:${NC}"
    for item in "${missing_items[@]}"; do
      echo -e "${RED}  - $item${NC}"
    done
    echo ""
    echo -e "${BLUE}请确保从LifeSmart HACS项目目录或其子目录运行此脚本${NC}"
    echo -e "${BLUE}预期的项目结构:${NC}"
    echo "  project-root/"
    echo "  ├── custom_components/lifesmart/"
    echo "  ├── .testing/                  ← 脚本位置"
    echo "  ├── hacs.json"
    echo "  └── ..."
    exit 1
  fi
  
  # 获取当前工作目录
  local current_dir
  if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ -n "${MSYSTEM:-}" ]]; then
    # Windows环境使用特殊的pwd
    current_dir="$(pwd -W 2>/dev/null || pwd)"
  else
    # Linux/macOS/WSL使用标准pwd
    current_dir="$(pwd)"
  fi
  
  # 规范化路径比较 (处理Windows/WSL路径差异)
  local normalized_current normalized_project
  
  if [[ "$OSTYPE" == "linux-gnu"* ]] && grep -qE "(Microsoft|microsoft)" /proc/version 2>/dev/null; then
    # WSL环境：可能存在/mnt/c路径和Windows路径的混合
    normalized_current="$(realpath "$current_dir" 2>/dev/null || echo "$current_dir")"
    normalized_project="$(realpath "$project_root" 2>/dev/null || echo "$project_root")"
  else
    # 其他环境使用标准路径
    normalized_current="$current_dir"
    normalized_project="$project_root"
  fi
  
  # 检查是否需要切换目录
  if [ "$normalized_current" != "$normalized_project" ]; then
    echo -e "${YELLOW}📁 自动切换工作目录:${NC}"
    echo -e "${YELLOW}   从: $current_dir${NC}"
    echo -e "${YELLOW}   到: $project_root${NC}"
    
    # 切换到项目根目录
    if cd "$project_root"; then
      echo -e "${GREEN}✓ 已切换到项目根目录${NC}"
    else
      echo -e "${RED}❌ 无法切换到项目根目录: $project_root${NC}"
      exit 1
    fi
  else
    echo -e "${GREEN}✓ 当前已在项目根目录: $project_root${NC}"
  fi
  
  # 设置全局变量供脚本其他部分使用
  PROJECT_ROOT="$project_root"
  SCRIPT_DIR="$script_dir"
}

# 执行项目根目录检测和切换
auto_detect_and_switch_to_project_root

# 检查 bash 版本兼容性，如果是老版本尝试找新版本
if [ "${BASH_VERSINFO[0]}" -lt 4 ]; then
    echo "当前 bash 版本过低: ${BASH_VERSION}"
    echo "正在尝试使用更新的 bash 版本..."
    
    # 尝试找到更新的 bash 版本
    NEW_BASH=""
    for bash_path in /opt/homebrew/bin/bash /usr/local/bin/bash /bin/bash; do
        if [ -x "$bash_path" ]; then
            BASH_VERSION_CHECK=$("$bash_path" -c 'echo $BASH_VERSION' 2>/dev/null || echo "")
            if [[ "$BASH_VERSION_CHECK" =~ ^[4-9]\. ]]; then
                NEW_BASH="$bash_path"
                break
            fi
        fi
    done
    
    if [ -n "$NEW_BASH" ]; then
        echo "找到兼容的 bash 版本: $NEW_BASH"
        echo "重新执行脚本..."
        exec "$NEW_BASH" "$0" "$@"
    else
        echo "错误: 需要 bash 4.0 或更高版本来支持关联数组"
        echo "请安装更新的 bash 版本: brew install bash"
        exit 1
    fi
fi

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检测操作系统和环境
detect_os_and_env() {
  # 检测操作系统
  if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if grep -qE "(Microsoft|microsoft)" /proc/version 2>/dev/null; then
      # 进一步区分WSL1和WSL2
      if grep -q "WSL2" /proc/version 2>/dev/null; then
        OS_TYPE="wsl2"
        echo -e "${BLUE}检测到 Windows WSL2 环境${NC}"
      else
        OS_TYPE="wsl"
        echo -e "${BLUE}检测到 Windows WSL 环境${NC}"
      fi
      
      # 检测WSL发行版
      if [ -f /etc/os-release ]; then
        WSL_DISTRO=$(grep "^NAME=" /etc/os-release | cut -d'"' -f2)
        echo -e "${YELLOW}WSL 发行版: $WSL_DISTRO${NC}"
      fi
      
      # 检测Windows路径挂载
      if mount | grep -q "C:.*on.*type.*drvfs"; then
        echo -e "${YELLOW}检测到 Windows 文件系统挂载${NC}"
      fi
    else
      OS_TYPE="linux"
      echo -e "${BLUE}检测到 Linux 环境${NC}"
    fi
  elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS_TYPE="macos"
    echo -e "${BLUE}检测到 macOS 环境${NC}"
  elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]]; then
    OS_TYPE="windows"
    echo -e "${BLUE}检测到 Windows 环境 (Cygwin/MSYS)${NC}"
  else
    OS_TYPE="unknown"
    echo -e "${YELLOW}未知操作系统: $OSTYPE${NC}"
  fi
  
  # 检测 shell 环境
  if command -v zsh >/dev/null 2>&1; then
    SHELL_TYPE="zsh"
    SHELL_RC="~/.zshrc"
  elif command -v bash >/dev/null 2>&1; then
    SHELL_TYPE="bash"
    SHELL_RC="~/.bashrc"
  else
    SHELL_TYPE="sh"
    SHELL_RC="~/.profile"
  fi
  
  echo -e "${BLUE}使用 shell: $SHELL_TYPE${NC}"
}

# 获取 conda 命令的包装函数
get_conda_cmd() {
  case "$OS_TYPE" in
    "wsl"|"wsl2"|"linux"|"macos")
      if [[ "$SHELL_TYPE" == "zsh" ]]; then
        echo "source ~/.zshrc && conda"
      else
        echo "source ~/.bashrc && conda"
      fi
      ;;
    "windows")
      echo "conda"
      ;;
    *)
      echo "conda"
      ;;
  esac
}

# 执行 conda 命令的包装函数
exec_conda_cmd() {
  local cmd="$1"
  local conda_cmd
  conda_cmd=$(get_conda_cmd)
  
  case "$OS_TYPE" in
    "wsl"|"wsl2"|"linux"|"macos")
      if [[ "$SHELL_TYPE" == "zsh" ]]; then
        zsh -c "$conda_cmd $cmd"
      else
        bash -c "$conda_cmd $cmd"
      fi
      ;;
    "windows")
      cmd.exe /c "conda $cmd"
      ;;
    *)
      conda "$cmd"
      ;;
  esac
}

# 在 conda 环境中执行命令的包装函数
exec_in_conda_env() {
  local conda_env="$1"
  local work_dir="$2"
  local command="$3"
  
  case "$OS_TYPE" in
    "wsl"|"wsl2"|"linux"|"macos")
      if [[ "$SHELL_TYPE" == "zsh" ]]; then
        zsh -c "source ~/.zshrc && conda activate $conda_env && cd '$work_dir' && $command"
      else
        bash -c "source ~/.bashrc && conda activate $conda_env && cd '$work_dir' && $command"
      fi
      ;;
    "windows")
      cmd.exe /c "conda activate $conda_env && cd /d '$work_dir' && $command"
      ;;
    *)
      bash -c "conda activate $conda_env && cd '$work_dir' && $command"
      ;;
  esac
}

# 初始化环境检测
detect_os_and_env

# 导入版本映射函数 (使用自动检测设置的SCRIPT_DIR)
source "$SCRIPT_DIR/version_mapping.sh"

# 测试配置 - 与GitHub Actions完全一致
# 使用更兼容的方式声明关联数组
declare -A test_matrix
test_matrix["2022.10.0"]="3.10"
test_matrix["2023.6.0"]="3.11"
test_matrix["2024.2.0"]="3.12"
test_matrix["2024.12.0"]="3.13"
test_matrix["latest"]="3.13"

LOG_DIR="$SCRIPT_DIR/test_logs"

# 创建日志目录
mkdir -p "$LOG_DIR"

# 命令行参数解析
usage() {
  echo "用法: $0 [选项]"
  echo ""
  echo "选项:"
  echo "  -h, --help              显示帮助信息"
  echo "  -a, --all               运行全部环境测试"
  echo "  -e, --env ENV_NAME      运行指定环境测试"
  echo "  -c, --current           在当前环境测试（如果是有效CI环境）"
  echo "  -i, --interactive       强制交互式选择"
  echo ""
  echo "环境名称:"
  echo "  ci-test-ha2023.6.0-py3.11"
  echo "  ci-test-ha2024.2.0-py3.12"
  echo "  ci-test-ha2024.12.0-py3.13"
  echo "  ci-test-ha-latest-py3.13"
  echo ""
  echo "示例:"
  echo "  $0                                   # 交互式选择"
  echo "  $0 --all                             # 运行全部环境"
  echo "  $0 --env ci-test-ha2023.6.0-py3.11  # 运行指定环境"
  echo "  $0 --current                         # 当前环境测试"
  echo "  echo '5' | $0                        # 通过管道输入选择全部环境"
}

# 解析命令行参数
FORCE_INTERACTIVE=false
RUN_ALL=false
SPECIFIC_ENV=""
USE_CURRENT=false

while [[ $# -gt 0 ]]; do
  case $1 in
  -h | --help)
    usage
    exit 0
    ;;
  -a | --all)
    RUN_ALL=true
    shift
    ;;
  -e | --env)
    SPECIFIC_ENV="$2"
    shift 2
    ;;
  -c | --current)
    USE_CURRENT=true
    shift
    ;;
  -i | --interactive)
    FORCE_INTERACTIVE=true
    shift
    ;;
  *)
    echo "未知选项: $1"
    usage
    exit 1
    ;;
  esac
done

# 函数：检测当前conda环境
detect_current_env() {
  if [ -z "$CONDA_DEFAULT_ENV" ]; then
    echo "none"
  else
    echo "$CONDA_DEFAULT_ENV"
  fi
}

# 函数：验证是否为有效的CI测试环境
is_valid_ci_env() {
  local env_name=$1
  case "$env_name" in
  "ci-test-ha2022.10.0-py3.10" | "ci-test-ha2023.6.0-py3.11" | "ci-test-ha2024.2.0-py3.12" | "ci-test-ha2024.12.0-py3.13" | "ci-test-ha-latest-py3.13")
    return 0
    ;;
  *)
    return 1
    ;;
  esac
}

# 函数：从环境名获取对应的HA版本和Python版本
get_versions_from_env() {
  local env_name=$1
  case "$env_name" in
  "ci-test-ha2022.10.0-py3.10")
    echo "2022.10.0 3.10"
    ;;
  "ci-test-ha2023.6.0-py3.11")
    echo "2023.6.0 3.11"
    ;;
  "ci-test-ha2024.2.0-py3.12")
    echo "2024.2.0 3.12"
    ;;
  "ci-test-ha2024.12.0-py3.13")
    echo "2024.12.0 3.13"
    ;;
  "ci-test-ha-latest-py3.13")
    echo "latest 3.13"
    ;;
  *)
    echo "unknown unknown"
    ;;
  esac
}

# 函数：交互式环境选择
interactive_env_selection() {
  echo -e "${YELLOW}请选择要测试的CI环境:${NC}" >&2
  echo "1) ci-test-ha2022.10.0-py3.10 (HA 2022.10.0 + Python 3.10)" >&2
  echo "2) ci-test-ha2023.6.0-py3.11  (HA 2023.6.0 + Python 3.11)" >&2
  echo "3) ci-test-ha2024.2.0-py3.12  (HA 2024.2.0 + Python 3.12)" >&2
  echo "4) ci-test-ha2024.12.0-py3.13 (HA 2024.12.0 + Python 3.13)" >&2
  echo "5) ci-test-ha-latest-py3.13   (HA latest + Python 3.13)" >&2
  echo "6) 全部环境测试 (完整CI矩阵)" >&2
  echo "" >&2
  read -p "请输入选择 (1-6): " choice

  case $choice in
  1)
    echo "ci-test-ha2022.10.0-py3.10"
    ;;
  2)
    echo "ci-test-ha2023.6.0-py3.11"
    ;;
  3)
    echo "ci-test-ha2024.2.0-py3.12"
    ;;
  4)
    echo "ci-test-ha2024.12.0-py3.13"
    ;;
  5)
    echo "ci-test-ha-latest-py3.13"
    ;;
  6)
    echo "all"
    ;;
  *)
    echo -e "${RED}无效选择，退出${NC}" >&2
    exit 1
    ;;
  esac
}

echo -e "${BLUE}=== LifeSmart Integration CI Compatibility Test ===${NC}"
echo -e "${BLUE}Project: $(basename $SCRIPT_DIR)${NC}"
echo -e "${BLUE}Date: $(date)${NC}"
echo ""

# 检测当前conda环境
current_env=$(detect_current_env)
echo -e "${BLUE}当前conda环境: ${YELLOW}$current_env${NC}"

# 显示版本映射表
show_version_mapping
echo ""

# 主逻辑：根据命令行参数或交互选择确定测试模式
selected_env=""
single_env_mode=true

if [ "$RUN_ALL" = true ]; then
  # 命令行指定运行全部环境
  echo -e "${BLUE}=== 命令行模式: 全部环境测试 ===${NC}"
  single_env_mode=false
elif [ -n "$SPECIFIC_ENV" ]; then
  # 命令行指定特定环境
  if is_valid_ci_env "$SPECIFIC_ENV"; then
    echo -e "${BLUE}=== 命令行模式: 指定环境 $SPECIFIC_ENV ===${NC}"
    selected_env="$SPECIFIC_ENV"
    single_env_mode=true
  else
    echo -e "${RED}错误: 无效的环境名称: $SPECIFIC_ENV${NC}"
    echo -e "${YELLOW}有效的环境名称:${NC}"
    echo "  ci-test-ha2023.6.0-py3.11"
    echo "  ci-test-ha2024.2.0-py3.12"
    echo "  ci-test-ha2024.12.0-py3.13"
    echo "  ci-test-ha-latest-py3.13"
    exit 1
  fi
elif [ "$USE_CURRENT" = true ]; then
  # 命令行指定使用当前环境
  if is_valid_ci_env "$current_env"; then
    echo -e "${BLUE}=== 命令行模式: 当前环境 $current_env ===${NC}"
    selected_env="$current_env"
    single_env_mode=true
  else
    echo -e "${RED}错误: 当前环境 '$current_env' 不是有效的CI测试环境${NC}"
    exit 1
  fi
else
  # 交互模式或管道输入模式
  if is_valid_ci_env "$current_env" && [ "$FORCE_INTERACTIVE" = false ]; then
    # 当前环境是有效的CI环境，询问是否在当前环境测试
    versions=$(get_versions_from_env "$current_env")
    ha_version=$(echo $versions | cut -d' ' -f1)
    py_version=$(echo $versions | cut -d' ' -f2)

    echo -e "${GREEN}✓ 检测到有效的CI测试环境: $current_env${NC}"
    echo -e "${BLUE}对应版本: HA $ha_version + Python $py_version${NC}"
    echo ""

    # 检查是否是非交互式输入
    if [ -t 0 ]; then
      # 标准输入是终端，使用交互模式
      read -p "是否在当前环境中进行单环境测试? (y/n, 默认y): " test_current
      test_current=${test_current:-y}
    else
      # 非交互式输入，直接使用当前环境
      echo "检测到非交互式输入，使用当前环境进行测试..."
      test_current="y"
    fi

    if [[ "$test_current" =~ ^[Yy]$ ]]; then
      # 在当前环境进行单环境测试
      echo -e "${BLUE}在当前环境 $current_env 中进行测试...${NC}"
      selected_env="$current_env"
      single_env_mode=true
    else
      # 用户选择其他选项，进入交互选择
      selected_env=$(interactive_env_selection)
      if [ "$selected_env" = "all" ]; then
        single_env_mode=false
      else
        single_env_mode=true
      fi
    fi
  else
    # 当前环境不是有效的CI环境，或强制交互模式
    if [ "$current_env" = "312-lifesmart" ]; then
      echo -e "${RED}⚠️  检测到用户开发环境: $current_env${NC}"
      echo -e "${RED}   AI助手禁止使用此环境进行测试${NC}"
    elif [ "$current_env" = "none" ]; then
      echo -e "${YELLOW}⚠️  未检测到conda环境${NC}"
    else
      echo -e "${YELLOW}⚠️  当前环境 '$current_env' 不是有效的CI测试环境${NC}"
    fi

    echo -e "${BLUE}需要切换到正确的CI测试环境${NC}"
    echo ""

    # 检查是否是管道输入
    if [ ! -t 0 ]; then
      # 非交互式输入，读取选择
      read -r choice
      case $choice in
      1)
        selected_env="ci-test-ha2023.6.0-py3.11"
        single_env_mode=true
        ;;
      2)
        selected_env="ci-test-ha2024.2.0-py3.12"
        single_env_mode=true
        ;;
      3)
        selected_env="ci-test-ha2024.12.0-py3.13"
        single_env_mode=true
        ;;
      4)
        selected_env="ci-test-ha-latest-py3.13"
        single_env_mode=true
        ;;
      5)
        single_env_mode=false
        ;;
      *)
        echo -e "${RED}无效选择: $choice${NC}"
        exit 1
        ;;
      esac

      if [ "$single_env_mode" = true ]; then
        echo -e "${BLUE}=== 管道输入模式: 单环境测试 $selected_env ===${NC}"
      else
        echo -e "${BLUE}=== 管道输入模式: 全部环境测试 ===${NC}"
      fi
    else
      # 交互式选择
      selected_env=$(interactive_env_selection)
      if [ "$selected_env" = "all" ]; then
        single_env_mode=false
        echo -e "${BLUE}=== 交互式模式: 全部环境测试 ===${NC}"
      else
        single_env_mode=true
        echo -e "${BLUE}=== 交互式模式: 单环境测试 $selected_env ===${NC}"
      fi
    fi
  fi
fi

echo ""

# 函数：创建 conda 测试环境
create_conda_env() {
  local conda_env=$1
  local py_version=$2
  
  echo -e "${YELLOW}Creating conda environment: $conda_env with Python $py_version${NC}"
  
  # 检查环境是否已存在
  if exec_conda_cmd "env list" | grep -q "^$conda_env "; then
    echo -e "${GREEN}Environment $conda_env already exists${NC}"
    return 0
  fi
  
  # 配置conda使用仅conda-forge通道以避免TOS问题
  echo -e "${YELLOW}Configuring conda channels to avoid TOS issues${NC}"
  exec_conda_cmd "config --set channel_priority strict" || true
  exec_conda_cmd "config --add channels conda-forge" || true
  
  # 创建新环境 (使用conda-forge避免TOS问题)
  if exec_conda_cmd "create -n '$conda_env' python='$py_version' -c conda-forge --override-channels -y"; then
    echo -e "${GREEN}✓ Created conda environment: $conda_env${NC}"
    return 0
  else
    echo -e "${RED}✗ Failed to create conda environment: $conda_env${NC}"
    return 1
  fi
}

# 函数：获取对应的conda环境
get_conda_env() {
  local ha_version=$1
  local py_version=$2

  case "${ha_version}_${py_version}" in
  "2022.10.0_3.10")
    echo "ci-test-ha2022.10.0-py3.10"
    ;;
  "2023.6.0_3.11")
    echo "ci-test-ha2023.6.0-py3.11"
    ;;
  "2024.2.0_3.12")
    echo "ci-test-ha2024.2.0-py3.12"
    ;;
  "2024.12.0_3.13")
    echo "ci-test-ha2024.12.0-py3.13"
    ;;
  "latest_3.13")
    echo "ci-test-ha-latest-py3.13"
    ;;
  *)
    echo ""
    return 1
    ;;
  esac
}

# 函数：清理并重新安装依赖（模拟GitHub CI的全新安装）
clean_install_dependencies() {
  local ha_version=$1
  local conda_env=$2

  echo -e "${YELLOW}Clean installing dependencies for HA $ha_version (mirroring GitHub CI fresh install)${NC}"

  # 在conda环境中执行清理和安装，根据操作系统选择执行方式
  local install_cmd_common="
# 1. 清理pytest缓存和__pycache__（保持测试环境干净）
echo 'Clearing test cache...' &&
find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true &&
find . -name '*.pyc' -delete 2>/dev/null || true &&
rm -rf .pytest_cache 2>/dev/null || true &&

# 2. 升级pip（与GitHub CI一致）
python -m pip install --upgrade pip -q &&

# 3. 根据HA版本安装兼容的pytest-homeassistant-custom-component版本
# 完全复制GitHub CI的逻辑，使用--force-reinstall提高本地测试效率
echo 'Installing fresh dependencies...' &&
"

  if [[ "$ha_version" == "2022.10.0" ]]; then
    install_cmd_common+="
if [ \"\$(python -c 'import sys; print(f\"{sys.version_info.major}.{sys.version_info.minor}\")')\" = \"3.10\" ]; then
  if [[ \"\$OSTYPE\" == \"darwin\"* ]]; then
    # macOS Python 3.10: 使用双fork解决方案修复lru-dict编译问题 (基于0.12.5)
    echo 'Using dual-fork solution for macOS ARM64 lru-dict compatibility (2022.10.0)...'
    echo 'Step 1: Installing lru-dict==1.3.0 (compatible version)...'
    pip install -q lru-dict==1.3.0 &&
    echo 'Step 2: Installing forked HA 2022.10.0 (lru-dict dependencies removed)...'
    timeout 600 pip install git+https://github.com/MapleEve/homeassistant-lru-dict-macos-fix.git@py310-fix-branch &&
    echo 'Step 3: Installing forked pytest plugin (compatible with our HA fork)...'
    timeout 600 pip install git+https://github.com/MapleEve/pytest-homeassistant-custom-component-fixed.git@py310-fix-branch
  else
    pip install --force-reinstall -q 'pytest-homeassistant-custom-component==0.12.5'
  fi
else
  pip install --force-reinstall -q 'pytest-homeassistant-custom-component==0.12.5'
fi &&"
  elif [[ "$ha_version" == "2023.6.0" ]]; then
    install_cmd_common+="
if [ \"\$(python -c 'import sys; print(f\"{sys.version_info.major}.{sys.version_info.minor}\")')\" = \"3.11\" ]; then
  if [[ \"\$OSTYPE\" == \"darwin\"* ]]; then
    # macOS Python 3.11: 使用双fork解决方案修复lru-dict编译问题
    echo 'Using dual-fork solution for macOS ARM64 lru-dict compatibility...'
    echo 'Step 1: Installing lru-dict==1.3.0 (compatible version)...'
    pip install -q lru-dict==1.3.0 &&
    echo 'Step 2: Installing forked HA 2023.6.0 (lru-dict dependencies removed)...'
    timeout 600 pip install git+https://github.com/MapleEve/homeassistant-lru-dict-macos-fix.git@macos-fix-branch &&
    echo 'Step 3: Installing forked pytest plugin (compatible with our HA fork)...'
    timeout 600 pip install git+https://github.com/MapleEve/pytest-homeassistant-custom-component-fixed.git@macos-fix-branch
  else
    pip install --force-reinstall -q 'pytest-homeassistant-custom-component==0.13.36'
  fi
else
  pip install --force-reinstall -q 'pytest-homeassistant-custom-component==0.13.36'
fi &&"
  elif [[ "$ha_version" == "2024.2.0" ]]; then
    install_cmd_common+="pip install --force-reinstall -q 'pytest-homeassistant-custom-component==0.13.99' &&"
  elif [[ "$ha_version" == "2024.12.0" ]]; then
    install_cmd_common+="pip install --force-reinstall -q 'pytest-homeassistant-custom-component==0.13.190' &&"
  elif [[ "$ha_version" == "latest" ]]; then
    install_cmd_common+="pip install --force-reinstall -q 'pytest-homeassistant-custom-component' &&"
  else
    install_cmd_common+="pip install --force-reinstall -q pytest-homeassistant-custom-component &&"
  fi

  install_cmd_common+="
# 4. 安装其他测试依赖（pytest-asyncio和pytest-cov由pytest-homeassistant-custom-component管理）
pip install -q flake8 &&

# 5. 验证安装
echo 'Verifying installations...' &&
python --version &&
python -c 'import homeassistant.const; print(\"HA version:\", homeassistant.const.__version__)' &&
python -c 'import pytest; print(\"pytest version:\", pytest.__version__)' &&
pip show pytest-homeassistant-custom-component | grep Version &&
python -c 'import aiohttp; print(\"aiohttp version:\", aiohttp.__version__)'
"

  # 根据操作系统和shell类型执行安装命令
  case "$OS_TYPE" in
    "wsl"|"wsl2"|"linux"|"macos")
      if [[ "$SHELL_TYPE" == "zsh" ]]; then
        local install_cmd="source ~/.zshrc && conda activate $conda_env && $install_cmd_common"
        if zsh -c "$install_cmd"; then
          echo -e "${GREEN}✓ Dependencies clean installed successfully${NC}"
          return 0
        fi
      else
        local install_cmd="source ~/.bashrc && conda activate $conda_env && $install_cmd_common"
        if bash -c "$install_cmd"; then
          echo -e "${GREEN}✓ Dependencies clean installed successfully${NC}"
          return 0
        fi
      fi
      ;;
    "windows")
      local install_cmd="conda activate $conda_env && $install_cmd_common"
      if cmd.exe /c "$install_cmd"; then
        echo -e "${GREEN}✓ Dependencies clean installed successfully${NC}"
        return 0
      fi
      ;;
    *)
      local install_cmd="conda activate $conda_env && $install_cmd_common"
      if bash -c "$install_cmd"; then
        echo -e "${GREEN}✓ Dependencies clean installed successfully${NC}"
        return 0
      fi
      ;;
  esac

  echo -e "${RED}✗ Failed to clean install dependencies${NC}"
  return 1
}

# 函数：运行代码风格检查
run_flake8() {
  local ha_version=$1
  local log_file="$LOG_DIR/flake8_ha_${ha_version}.log"

  echo -e "${YELLOW}Running Flake8 lint check...${NC}"

  if flake8 --count --show-source --statistics custom_components/lifesmart >"$log_file" 2>&1; then
    echo -e "${GREEN}✓ Flake8 passed${NC}"
    return 0
  else
    echo -e "${RED}✗ Flake8 failed${NC}"
    echo "Check log: $log_file"
    return 1
  fi
}

# 函数：运行单元测试
run_pytest() {
  local ha_version=$1
  local log_file="$LOG_DIR/pytest_ha_${ha_version}.log"

  echo -e "${YELLOW}Running pytest for HA $ha_version...${NC}"

  # 设置环境变量
  export PYTHONPATH="."

  local pytest_args="-v --cov --cov-branch --cov-report=xml"

  if eval "pytest $pytest_args > \"$log_file\" 2>&1"; then
    echo -e "${GREEN}✓ Pytest passed${NC}"
    return 0
  else
    echo -e "${RED}✗ Pytest failed${NC}"
    echo "Check log: $log_file"
    return 1
  fi
}

# 函数：测试单个HA版本（使用conda环境+清理安装，完全模拟GitHub CI）
test_ha_version() {
  local ha_version=$1
  local py_version=$2

  echo ""
  echo -e "${BLUE}=== Testing Home Assistant $ha_version with Python $py_version ===${NC}"

  # 获取对应的conda环境
  local conda_env
  conda_env=$(get_conda_env "$ha_version" "$py_version")
  if [ $? -ne 0 ] || [ -z "$conda_env" ]; then
    echo -e "${RED}✗ Unknown version combination: HA $ha_version Python $py_version${NC}"
    return 1
  fi

  echo -e "${YELLOW}Using conda environment: $conda_env${NC}"

  # 检查conda环境是否存在，如果不存在则创建
  if ! exec_conda_cmd "env list" | grep -q "^$conda_env "; then
    echo -e "${YELLOW}Conda environment '$conda_env' not found, creating it...${NC}"
    if ! create_conda_env "$conda_env" "$py_version"; then
      echo -e "${RED}✗ Failed to create conda environment${NC}"
      return 1
    fi
  fi

  # 清理并重新安装依赖（模拟GitHub CI全新安装）
  if ! clean_install_dependencies "$ha_version" "$conda_env"; then
    echo -e "${RED}✗ Failed to clean install dependencies for HA $ha_version${NC}"
    return 1
  fi

  # 运行Flake8（在conda环境中）
  echo -e "${YELLOW}Running Flake8 lint check in conda environment $conda_env...${NC}"
  local log_file="$LOG_DIR/flake8_ha_${ha_version}.log"
  
  # 获取当前工作目录，支持不同操作系统
  local work_dir
  case "$OS_TYPE" in
    "windows")
      work_dir="$(pwd | sed 's|/mnt/||' | sed 's|/|:|' | sed 's|:|://|')"
      ;;
    *)
      work_dir="$(pwd)"
      ;;
  esac

  # 检查是否是交互模式
  local flake8_exit_code
  if [ -t 1 ]; then
    # 交互模式：显示实时输出并保存到日志
    exec_in_conda_env "$conda_env" "$work_dir" "flake8 --count --show-source --statistics custom_components/lifesmart" 2>&1 | tee "$log_file"
    flake8_exit_code=${PIPESTATUS[0]}
  else
    # 管道模式：静默运行，只保存到日志
    exec_in_conda_env "$conda_env" "$work_dir" "flake8 --count --show-source --statistics custom_components/lifesmart" >"$log_file" 2>&1
    flake8_exit_code=$?
  fi

  # 根据flake8退出码判断检查结果
  if [ $flake8_exit_code -eq 0 ]; then
    echo -e "${GREEN}✓ Flake8 passed${NC}"
  else
    echo -e "${RED}✗ Flake8 failed (exit code: $flake8_exit_code)${NC}"
    echo "Check log: $log_file"
    return 1
  fi

  # 运行pytest（在conda环境中）
  echo -e "${YELLOW}Running pytest for HA $ha_version in conda environment $conda_env...${NC}"
  local pytest_log_file="$LOG_DIR/pytest_ha_${ha_version}.log"

  local pytest_args="-v --cov --cov-branch --cov-report=xml"

  # 检查是否是交互模式
  local pytest_exit_code
  if [ -t 1 ]; then
    # 交互模式：显示实时输出并保存到日志
    exec_in_conda_env "$conda_env" "$work_dir" "export PYTHONPATH=. && pytest $pytest_args" 2>&1 | tee "$pytest_log_file"
    pytest_exit_code=${PIPESTATUS[0]}
  else
    # 管道模式：静默运行，只保存到日志
    exec_in_conda_env "$conda_env" "$work_dir" "export PYTHONPATH=. && pytest $pytest_args" >"$pytest_log_file" 2>&1
    pytest_exit_code=$?
  fi

  # 根据pytest退出码判断测试结果
  if [ $pytest_exit_code -eq 0 ]; then
    echo -e "${GREEN}✓ Pytest passed${NC}"
  else
    echo -e "${RED}✗ Pytest failed (exit code: $pytest_exit_code)${NC}"
    echo "Check log: $pytest_log_file"
    return 1
  fi

  echo -e "${GREEN}✓ HA $ha_version test completed successfully${NC}"
  return 0
}

# 主测试循环
failed_tests=()
successful_tests=()

if [ "$single_env_mode" = true ] && [ "$selected_env" != "all" ]; then
  # 单环境测试模式
  versions=$(get_versions_from_env "$selected_env")
  ha_version=$(echo $versions | cut -d' ' -f1)
  py_version=$(echo $versions | cut -d' ' -f2)

  echo -e "${BLUE}=== 单环境测试模式: $selected_env ===${NC}"

  if test_ha_version "$ha_version" "$py_version"; then
    successful_tests+=("$ha_version (Python $py_version)")
  else
    failed_tests+=("$ha_version (Python $py_version)")
  fi
else
  # 全环境测试模式
  echo -e "${BLUE}=== 完整CI矩阵测试模式 ===${NC}"

  for ha_version in "${!test_matrix[@]}"; do
    py_version="${test_matrix[$ha_version]}"

    if test_ha_version "$ha_version" "$py_version"; then
      successful_tests+=("$ha_version (Python $py_version)")
    else
      failed_tests+=("$ha_version (Python $py_version)")
    fi
  done
fi

# 输出测试总结
echo ""
echo -e "${BLUE}=== Test Summary ===${NC}"
echo ""

if [ ${#successful_tests[@]} -gt 0 ]; then
  echo -e "${GREEN}Successful tests:${NC}"
  for test in "${successful_tests[@]}"; do
    echo -e "${GREEN}  ✓ $test${NC}"
  done
fi

if [ ${#failed_tests[@]} -gt 0 ]; then
  echo ""
  echo -e "${RED}Failed tests:${NC}"
  for test in "${failed_tests[@]}"; do
    echo -e "${RED}  ✗ $test${NC}"
  done
fi

echo ""
echo -e "${BLUE}Total: ${#successful_tests[@]} passed, ${#failed_tests[@]} failed${NC}"
echo -e "${BLUE}Logs available in: $LOG_DIR${NC}"

# 退出码
if [ ${#failed_tests[@]} -eq 0 ]; then
  echo -e "${GREEN}All tests passed! 🎉${NC}"
  exit 0
else
  echo -e "${RED}Some tests failed. Check logs for details.${NC}"
  exit 1
fi
