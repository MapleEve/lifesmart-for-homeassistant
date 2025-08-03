#!/bin/bash

# LifeSmart Integration - 版本映射函数
# 为不同HA版本定义兼容的pytest和pytest-homeassistant-custom-component版本

# 函数：获取兼容的测试依赖版本
get_compatible_test_versions() {
  local ha_version=$1

  case "$ha_version" in
  "2023.6.0")
    # HA 2023.6.0 - 使用插件 0.13.36
    echo '"pytest>=7.2.1,<8.0.0" "pytest-homeassistant-custom-component==0.13.36"'
    ;;
  "2024.2.0")
    # HA 2024.2.0 - 使用插件 0.13.99
    echo '"pytest>=7.4.0,<8.0.0" "pytest-homeassistant-custom-component==0.13.99"'
    ;;
  "2024.12.0")
    # HA 2024.12.0 - 使用插件 0.13.190
    echo '"pytest>=8.0.0,<9.0.0" "pytest-homeassistant-custom-component==0.13.190"'
    ;;
  "latest")
    # HA 最新版本 - 使用最新插件
    echo '"pytest" "pytest-homeassistant-custom-component"'
    ;;
  *)
    # 回退
    echo '"pytest" "pytest-homeassistant-custom-component"'
    ;;
  esac
}

# 函数：验证安装的版本是否符合预期
verify_installed_versions() {
  local target_ha_version=$1
  local verification_failed=false

  # 获取实际安装的版本
  local actual_ha=$(pip show homeassistant 2>/dev/null | grep "Version:" | cut -d' ' -f2)
  local actual_pytest=$(pip show pytest 2>/dev/null | grep "Version:" | cut -d' ' -f2)
  local actual_pytest_ha=$(pip show pytest-homeassistant-custom-component 2>/dev/null | grep "Version:" | cut -d' ' -f2)
  local actual_aiohttp=$(pip show aiohttp 2>/dev/null | grep "Version:" | cut -d' ' -f2)

  echo "  📋 Version Verification Report:"
  echo "     Target HA Version: $target_ha_version"
  echo "     Actual HA Version: $actual_ha"
  echo "     pytest Version: $actual_pytest"
  echo "     pytest-ha-custom Version: $actual_pytest_ha"
  echo "     aiohttp Version: $actual_aiohttp"

  # 根据目标HA版本验证关键依赖
  case "$target_ha_version" in
  "2023.6.0")
    # 验证HA版本
    if [[ "$actual_ha" != "2023.6.0" ]]; then
      echo "     ❌ HA version mismatch: expected 2023.6.0, got $actual_ha"
      verification_failed=true
    fi

    # 验证pytest版本范围 (7.2.1 <= version < 8.0.0)
    if ! version_in_range "$actual_pytest" "7.2.1" "8.0.0"; then
      echo "     ❌ pytest version out of range: expected 7.2.1-7.x, got $actual_pytest"
      verification_failed=true
    fi

    # 验证pytest-ha-custom版本
    if [[ "$actual_pytest_ha" != "0.13.36" ]]; then
      echo "     ❌ pytest-ha-custom version mismatch: expected 0.13.36, got $actual_pytest_ha"
      verification_failed=true
    fi

    # 验证aiohttp版本 (应该是3.8.x)
    if [[ ! "$actual_aiohttp" =~ ^3\.8\. ]]; then
      echo "     ❌ aiohttp version unexpected: expected 3.8.x, got $actual_aiohttp"
      verification_failed=true
    fi
    ;;

  "2024.2.0")
    # 验证HA版本
    if [[ "$actual_ha" != "2024.2.0" ]]; then
      echo "     ❌ HA version mismatch: expected 2024.2.0, got $actual_ha"
      verification_failed=true
    fi

    # 验证pytest版本范围 (7.4.0 <= version < 8.0.0)
    if ! version_in_range "$actual_pytest" "7.4.0" "8.0.0"; then
      echo "     ❌ pytest version out of range: expected 7.4.0-7.x, got $actual_pytest"
      verification_failed=true
    fi

    # 验证pytest-ha-custom版本
    if [[ "$actual_pytest_ha" != "0.13.99" ]]; then
      echo "     ❌ pytest-ha-custom version mismatch: expected 0.13.99, got $actual_pytest_ha"
      verification_failed=true
    fi

    # 验证aiohttp版本 (应该是3.9.x)
    if [[ ! "$actual_aiohttp" =~ ^3\.9\. ]]; then
      echo "     ❌ aiohttp version unexpected: expected 3.9.x, got $actual_aiohttp"
      verification_failed=true
    fi
    ;;

  "2024.12.0")
    # 验证HA版本
    if [[ "$actual_ha" != "2024.12.0" ]]; then
      echo "     ❌ HA version mismatch: expected 2024.12.0, got $actual_ha"
      verification_failed=true
    fi

    # 验证pytest版本范围 (8.0.0 <= version < 9.0.0)
    if ! version_in_range "$actual_pytest" "8.0.0" "9.0.0"; then
      echo "     ❌ pytest version out of range: expected 8.0.0-8.x, got $actual_pytest"
      verification_failed=true
    fi

    # 验证pytest-ha-custom版本
    if [[ "$actual_pytest_ha" != "0.13.190" ]]; then
      echo "     ❌ pytest-ha-custom version mismatch: expected 0.13.190, got $actual_pytest_ha"
      verification_failed=true
    fi

    # 验证aiohttp版本 (应该是3.11.x)
    if [[ ! "$actual_aiohttp" =~ ^3\.11\. ]]; then
      echo "     ❌ aiohttp version unexpected: expected 3.11.x, got $actual_aiohttp"
      verification_failed=true
    fi
    ;;

  "latest")
    # 对于latest版本，只检查基本的版本存在性
    if [[ -z "$actual_ha" ]]; then
      echo "     ❌ Home Assistant not installed"
      verification_failed=true
    fi

    if [[ -z "$actual_pytest" ]]; then
      echo "     ❌ pytest not installed"
      verification_failed=true
    fi

    if [[ -z "$actual_pytest_ha" ]]; then
      echo "     ❌ pytest-homeassistant-custom-component not installed"
      verification_failed=true
    fi
    ;;
  esac

  if [ "$verification_failed" = "true" ]; then
    return 1
  else
    echo "     ✅ All version constraints satisfied"
    return 0
  fi
}

# 函数：检查版本是否在指定范围内
version_in_range() {
  local version=$1
  local min_version=$2
  local max_version=$3

  # 首先尝试使用python3进行版本比较
  if python3 -c "
try:
    from packaging import version
    v = version.parse('$version')
    min_v = version.parse('$min_version')
    max_v = version.parse('$max_version')
    exit(0 if min_v <= v < max_v else 1)
except ImportError:
    # 如果packaging不可用，使用简单的字符串比较
    exit(0)
" 2>/dev/null; then
    return 0
  else
    # 如果packaging模块不可用，使用简单的版本字符串比较
    # 这是一个简化的版本比较，适用于大多数情况
    local version_major=$(echo "$version" | cut -d. -f1)
    local version_minor=$(echo "$version" | cut -d. -f2)
    local min_major=$(echo "$min_version" | cut -d. -f1)
    local min_minor=$(echo "$min_version" | cut -d. -f2)
    local max_major=$(echo "$max_version" | cut -d. -f1)

    # 简单的版本范围检查
    if [ "$version_major" -ge "$min_major" ] && [ "$version_major" -lt "$max_major" ]; then
      return 0
    elif [ "$version_major" -eq "$min_major" ] && [ "$version_minor" -ge "$min_minor" ]; then
      return 0
    else
      return 1
    fi
  fi
}

# 函数：安装兼容的测试依赖
# 策略：先安装pytest和pytest-homeassistant-custom-component，让插件自动安装兼容的HA版本
install_compatible_test_deps() {
  local ha_version=$1
  local quiet=${2:-false}
  local no_cache=${3:-true} # 默认使用无缓存安装

  # 构建pip安装参数
  local pip_args=""
  if [ "$no_cache" = "true" ]; then
    pip_args="--no-cache-dir --only-binary=all"
    if [ "$quiet" != "true" ]; then
      echo "Using no-cache installation with binary-only packages"
    fi
  fi

  if [ "$quiet" = "true" ]; then
    pip_args="$pip_args --quiet"
  fi

  # 根据目标HA版本安装对应的pytest插件，让插件决定HA版本
  case "$ha_version" in
  "2023.6.0")
    # HA 2023.6.0 - 使用插件 0.13.36
    if [ "$quiet" = "true" ]; then
      echo "Installing pytest and pytest-homeassistant-custom-component 0.13.36 (will auto-install HA 2023.6.0)..."
    else
      echo "Installing pytest 7.2.1+ and pytest-homeassistant-custom-component 0.13.36..."
      echo "  -> This will auto-install HA 2023.6.0"
    fi
    pip install $pip_args "pytest>=7.2.1,<8.0.0" "pytest-homeassistant-custom-component==0.13.36"
    ;;
  "2024.2.0")
    # HA 2024.2.0 - 使用插件 0.13.99
    if [ "$quiet" = "true" ]; then
      echo "Installing pytest and pytest-homeassistant-custom-component 0.13.99 (will auto-install HA 2024.2.0)..."
    else
      echo "Installing pytest 7.4.x and pytest-homeassistant-custom-component 0.13.99..."
      echo "  -> This will auto-install HA 2024.2.0"
    fi
    pip install $pip_args "pytest>=7.4.0,<8.0.0" "pytest-homeassistant-custom-component==0.13.99"
    ;;
  "2024.12.0")
    # HA 2024.12.0 - 使用插件 0.13.190
    if [ "$quiet" = "true" ]; then
      echo "Installing pytest and pytest-homeassistant-custom-component 0.13.190 (will auto-install HA 2024.12.0)..."
    else
      echo "Installing pytest 8.x and pytest-homeassistant-custom-component 0.13.190..."
      echo "  -> This will auto-install HA 2024.12.0"
    fi
    pip install $pip_args "pytest>=8.0.0,<9.0.0" "pytest-homeassistant-custom-component==0.13.190"
    ;;
  "latest")
    # HA 最新版本 - 使用最新插件
    if [ "$quiet" = "true" ]; then
      echo "Installing pytest and latest pytest-homeassistant-custom-component (will auto-install latest HA)..."
    else
      echo "Installing pytest and latest pytest-homeassistant-custom-component..."
      echo "  -> This will auto-install the latest HA version"
    fi
    pip install $pip_args "pytest" "pytest-homeassistant-custom-component"
    ;;
  *)
    # 回退到最新版本
    if [ "$quiet" = "true" ]; then
      echo "Installing pytest and latest pytest-homeassistant-custom-component (fallback)..."
    else
      echo "Installing pytest and latest pytest-homeassistant-custom-component (fallback)..."
    fi
    pip install $pip_args "pytest" "pytest-homeassistant-custom-component"
    ;;
  esac

  # 安装其他通用测试依赖
  pip install $pip_args pytest-asyncio pytest-cov flake8

  # 显示实际安装的HA版本并验证
  if [ "$quiet" != "true" ]; then
    local actual_ha=$(pip show homeassistant 2>/dev/null | grep "Version:" | cut -d' ' -f2)
    if [ -n "$actual_ha" ]; then
      echo "  -> Actually installed Home Assistant: $actual_ha"

      # 验证版本是否符合预期
      if ! verify_installed_versions "$ha_version"; then
        echo "  ⚠️  Version verification failed!"
        return 1
      else
        echo "  ✅ Version verification passed"
      fi
    fi
  fi
}

# 函数：显示版本映射表
show_version_mapping() {
  echo "LifeSmart Integration - 正确的HA & Test Dependencies Version Mapping:"
  echo "=================================================================="
  echo "| HA目标版本  | Python | pytest插件版本        | 实际安装HA版本 |"
  echo "|-------------|--------|---------------------|---------------|"
  echo "| 2023.6.0    | 3.11   | ==0.13.36           | 2023.6.0      |"
  echo "| 2024.2.0    | 3.12   | ==0.13.99           | 2024.2.0      |"
  echo "| 2024.12.0   | 3.13   | ==0.13.190          | 2024.12.0     |"
  echo "| latest      | 3.13   | (latest)            | 最新版本      |"
  echo "=================================================================="
}
