#!/usr/bin/env bash
# -*- coding: utf-8 -*-

# =============================================================================
# Mapping Tool - Full Mode Installation Script
# 完整版 mapping tool 依赖安装脚本
# 
# 此脚本安装所有高级 NLP 和 AI 分析依赖，解锁完整功能。
# 内部工具专用，提供最佳用户体验。
#
# 作者：@MapleEve
# 日期：2025-08-15
# =============================================================================

set -e  # 出错立即停止

# 配置和常量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REQUIREMENTS_FILE="${SCRIPT_DIR}/requirements.txt"
PYTHON_CMD="python3"
PIP_CMD="pip3"

# 颜色输出函数
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${PURPLE}===============================================${NC}"
    echo -e "${PURPLE}    Mapping Tool - Full Mode Installer       ${NC}"
    echo -e "${PURPLE}    完整版 mapping tool 依赖安装器           ${NC}"
    echo -e "${PURPLE}===============================================${NC}"
    echo
}

print_step() {
    echo -e "${CYAN}🔄 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# 检查系统环境
check_system_requirements() {
    print_step "检查系统环境..."
    
    # 检查 Python 版本
    if ! command -v "$PYTHON_CMD" &> /dev/null; then
        print_error "Python3 not found. 请安装 Python 3.7+"
        exit 1
    fi
    
    python_version=$($PYTHON_CMD --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
    python_major=$(echo "$python_version" | cut -d. -f1)
    python_minor=$(echo "$python_version" | cut -d. -f2)
    
    if [[ $python_major -lt 3 ]] || [[ $python_major -eq 3 && $python_minor -lt 7 ]]; then
        print_error "Python version too old: $python_version. 需要 Python 3.7+"
        exit 1
    fi
    
    print_success "Python version: $python_version ✓"
    
    # 检查 pip
    if ! command -v "$PIP_CMD" &> /dev/null; then
        print_error "pip3 not found. 请安装 pip"
        exit 1
    fi
    
    # 检查 requirements.txt
    if [[ ! -f "$REQUIREMENTS_FILE" ]]; then
        print_error "Requirements file not found: $REQUIREMENTS_FILE"
        exit 1
    fi
    
    print_success "系统环境检查通过"
}

# 显示安装预览
show_installation_preview() {
    print_step "分析依赖包..."
    
    echo -e "${BLUE}📦 即将安装的完整版依赖包:${NC}"
    echo
    echo "🧠 NLP & AI Analysis:"
    echo "   • spaCy >= 3.7.0 (高级语言处理)"
    echo "   • jieba >= 0.42.1 (中文分词)"
    echo "   • transformers >= 4.35.0 (transformer 模型)"
    echo "   • sentence-transformers >= 2.2.2 (语义相似度)"
    echo "   • scikit-learn >= 1.3.0 (机器学习)"
    echo
    echo "📊 Data & Performance:"
    echo "   • numpy >= 1.24.0 (数值计算)"
    echo "   • pandas >= 2.0.0 (数据处理)"
    echo "   • psutil >= 5.9.0 (系统监控)"
    echo "   • memory-profiler >= 0.61.0 (内存分析)"
    echo
    echo "⚡ Async & Optimization:"
    echo "   • aiofiles >= 23.2.1 (异步文件 I/O)"
    echo "   • cachetools >= 5.3.0 (智能缓存)"
    echo "   • lru-dict >= 1.2.0 (LRU 缓存优化)"
    echo
    echo "🔧 Development & Testing:"
    echo "   • pytest >= 7.4.0 (测试框架)"
    echo "   • pydantic >= 2.5.0 (数据验证)"
    echo "   • colorlog >= 6.7.0 (彩色日志)"
    echo
    echo -e "${YELLOW}预计下载大小: ~300MB${NC}"
    echo -e "${YELLOW}安装后占用空间: ~800MB${NC}"
    echo
}

# 安装确认
confirm_installation() {
    echo -e "${CYAN}🤔 这将安装完整版依赖以解锁所有高级功能。${NC}"
    echo -e "${CYAN}   包括 spaCy, transformers, jieba 等重量级 NLP 库。${NC}"
    echo
    
    while true; do
        read -p "是否继续安装? (y/N): " yn
        case $yn in
            [Yy]* ) break;;
            [Nn]* | "" ) 
                print_info "安装取消。如需基础版本，请直接使用 pip install psutil"
                exit 0
                ;;
            * ) echo "请输入 y 或 n";;
        esac
    done
}

# 创建虚拟环境 (可选)
setup_virtual_environment() {
    echo
    print_step "检查虚拟环境设置..."
    
    if [[ -z "${VIRTUAL_ENV}" ]]; then
        print_warning "当前未在虚拟环境中运行"
        echo
        
        while true; do
            read -p "是否创建新的虚拟环境? (推荐) (y/N): " yn
            case $yn in
                [Yy]* )
                    venv_name="mapping_tool_env"
                    print_step "创建虚拟环境: $venv_name"
                    
                    $PYTHON_CMD -m venv "$venv_name"
                    source "$venv_name/bin/activate"
                    
                    # 更新 pip 命令路径
                    PIP_CMD="$venv_name/bin/pip"
                    
                    print_success "虚拟环境创建完成: $venv_name"
                    print_info "使用 'source $venv_name/bin/activate' 激活环境"
                    break
                    ;;
                [Nn]* | "" ) 
                    print_warning "在系统 Python 环境中安装 (不推荐)"
                    break
                    ;;
                * ) echo "请输入 y 或 n";;
            esac
        done
    else
        print_success "检测到虚拟环境: $VIRTUAL_ENV"
    fi
}

# 升级 pip 和安装工具
upgrade_pip() {
    print_step "升级 pip 和安装工具..."
    
    $PIP_CMD install --upgrade pip setuptools wheel
    
    print_success "pip 和安装工具已升级"
}

# 安装依赖包
install_dependencies() {
    print_step "安装完整版依赖包..."
    echo
    
    print_info "开始安装... 这可能需要几分钟时间"
    print_info "首次安装会下载和编译一些库，请耐心等待"
    echo
    
    # 使用进度条和详细输出安装
    $PIP_CMD install -r "$REQUIREMENTS_FILE" --progress-bar on --verbose
    
    print_success "所有依赖包安装完成!"
}

# 下载 spaCy 语言模型
install_spacy_models() {
    print_step "安装 spaCy 语言模型..."
    
    # 检查 spaCy 是否成功安装
    if $PYTHON_CMD -c "import spacy" 2>/dev/null; then
        print_info "正在下载英文模型 (en_core_web_sm)..."
        $PYTHON_CMD -m spacy download en_core_web_sm || print_warning "英文模型下载失败，可手动安装"
        
        print_info "正在下载中文模型 (zh_core_web_sm)..."
        $PYTHON_CMD -m spacy download zh_core_web_sm || print_warning "中文模型下载失败，可手动安装"
        
        print_success "spaCy 语言模型安装完成"
    else
        print_warning "spaCy 未正确安装，跳过模型下载"
    fi
}

# 验证安装
verify_installation() {
    print_step "验证安装..."
    
    # 测试核心库导入
    test_imports=(
        "spacy:spaCy NLP库"
        "jieba:中文分词库"
        "sentence_transformers:语义相似度库"
        "sklearn:机器学习库"
        "numpy:数值计算库"
        "pandas:数据处理库"
        "psutil:系统监控库"
        "aiofiles:异步文件库"
        "pytest:测试框架"
        "pydantic:数据验证库"
    )
    
    success_count=0
    total_count=${#test_imports[@]}
    
    for import_test in "${test_imports[@]}"; do
        IFS=':' read -r module_name description <<< "$import_test"
        
        if $PYTHON_CMD -c "import $module_name" 2>/dev/null; then
            print_success "$description ✓"
            ((success_count++))
        else
            print_error "$description ✗"
        fi
    done
    
    echo
    if [[ $success_count -eq $total_count ]]; then
        print_success "🎉 所有依赖验证通过! ($success_count/$total_count)"
        print_success "完整版 mapping tool 已准备就绪!"
        return 0
    else
        print_warning "部分依赖验证失败 ($success_count/$total_count)"
        print_info "某些高级功能可能不可用，但基础功能应正常工作"
        return 1
    fi
}

# 显示使用说明
show_usage_instructions() {
    echo
    print_header
    echo -e "${GREEN}🎉 安装完成! 使用说明:${NC}"
    echo
    echo "1. 运行完整版 mapping tool:"
    echo -e "   ${CYAN}python3 main.py${NC}"
    echo
    echo "2. 或者使用传统模式:"
    echo -e "   ${CYAN}python3 RUN_THIS_TOOL.py${NC}"
    echo
    echo "3. 测试 NLP 服务:"
    echo -e "   ${CYAN}python3 -m implements.enhanced_nlp_service${NC}"
    echo
    echo "4. 运行测试套件:"
    echo -e "   ${CYAN}python3 -m pytest tests/$(NC)"
    echo
    echo -e "${BLUE}📖 完整版功能特性:${NC}"
    echo "   • 🧠 高级 NLP 语义分析 (spaCy + transformers)"
    echo "   • 🔍 中文智能分词 (jieba)"
    echo "   • 📊 语义相似度计算 (sentence-transformers)"
    echo "   • ⚡ 异步高性能处理"
    echo "   • 🎯 智能设备特征提取"
    echo "   • 📈 详细性能监控"
    echo "   • ✅ 完整测试覆盖"
    echo
    print_success "Happy coding! 🚀"
}

# 错误处理
handle_error() {
    print_error "安装过程中出现错误!"
    print_info "你可以尝试:"
    echo "   1. 检查网络连接"
    echo "   2. 升级 pip: pip3 install --upgrade pip"
    echo "   3. 使用代理: pip3 install -r requirements.txt --proxy=http://proxy:port"
    echo "   4. 手动安装失败的包"
    echo
    print_info "如需帮助，请查看错误日志或联系开发者"
    exit 1
}

# 主函数
main() {
    # 错误处理设置
    trap handle_error ERR
    
    print_header
    
    check_system_requirements
    echo
    
    show_installation_preview
    
    confirm_installation
    
    setup_virtual_environment
    
    upgrade_pip
    echo
    
    install_dependencies
    echo
    
    install_spacy_models
    echo
    
    if verify_installation; then
        show_usage_instructions
        exit 0
    else
        print_warning "安装完成但部分验证失败"
        show_usage_instructions
        exit 1
    fi
}

# 运行主函数
main "$@"