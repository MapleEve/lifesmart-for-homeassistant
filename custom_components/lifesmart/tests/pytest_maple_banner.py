"""
pytest启动横幅
为LifeSmart Integration测试提供美观的版本信息显示
"""

import os
import platform
import subprocess
import sys


def get_git_info() -> tuple[str, str]:
    """获取Git提交信息"""
    try:
        # 获取当前commit hash (短版本)
        commit_hash = (
            subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )

        # 获取当前分支名
        branch = (
            subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )

        return commit_hash, branch
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown", "unknown"


def get_environment_info() -> dict:
    """收集所有环境信息"""
    info = {}

    # Python版本
    info["python"] = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )

    # pytest版本
    try:
        import pytest

        info["pytest"] = pytest.__version__
    except ImportError:
        info["pytest"] = "unknown"

    # Git信息
    info["git_commit"], info["git_branch"] = get_git_info()

    # Home Assistant版本
    try:
        import homeassistant.const as ha_const

        info["homeassistant"] = ha_const.__version__
    except ImportError:
        info["homeassistant"] = "unknown"

    # pytest-homeassistant-custom-component版本
    try:
        import pytest_homeassistant_custom_component

        info["pytest_ha"] = pytest_homeassistant_custom_component.__version__
    except (ImportError, AttributeError):
        # 如果没有__version__属性，尝试从包信息获取
        try:
            import pkg_resources

            info["pytest_ha"] = pkg_resources.get_distribution(
                "pytest-homeassistant-custom-component"
            ).version
        except:
            info["pytest_ha"] = "unknown"

    # 当前conda环境
    info["conda_env"] = os.environ.get("CONDA_DEFAULT_ENV", "none")

    # aiohttp版本
    try:
        import aiohttp

        info["aiohttp"] = aiohttp.__version__
    except ImportError:
        info["aiohttp"] = "unknown"

    # asyncio版本
    try:
        import asyncio

        # asyncio没有__version__，使用Python版本作为代替
        info["asyncio_version"] = f"Python {info['python']}"
    except ImportError:
        info["asyncio_version"] = "unknown"

    # 平台信息
    info["platform"] = platform.system().lower()

    # 确保所有值都不为None
    for key, value in info.items():
        if value is None:
            info[key] = "unknown"

    return info


def create_maple_home_ascii():
    """创建大型MAPLE HOME ASCII艺术，像DOS启动logo风格"""

    # ANSI颜色代码
    class Colors:
        RESET = "\033[0m"
        BOLD = "\033[1m"

        # 前景色
        RED = "\033[31m"
        GREEN = "\033[32m"
        YELLOW = "\033[33m"
        BLUE = "\033[34m"
        MAGENTA = "\033[35m"
        CYAN = "\033[36m"
        WHITE = "\033[37m"

        # 亮色
        BRIGHT_RED = "\033[91m"
        BRIGHT_GREEN = "\033[92m"
        BRIGHT_YELLOW = "\033[93m"
        BRIGHT_BLUE = "\033[94m"
        BRIGHT_MAGENTA = "\033[95m"
        BRIGHT_CYAN = "\033[96m"
        BRIGHT_WHITE = "\033[97m"

    ascii_art = f"""
{Colors.BRIGHT_RED}  ███╗   ███╗ █████╗ ██████╗ ██╗     ███████╗    ██╗  ██╗ ██████╗ ███╗   ███╗███████╗{Colors.RESET}
{Colors.BRIGHT_YELLOW}  ████╗ ████║██╔══██╗██╔══██╗██║     ██╔════╝    ██║  ██║██╔═══██╗████╗ ████║██╔════╝{Colors.RESET}
{Colors.BRIGHT_GREEN}  ██╔████╔██║███████║██████╔╝██║     █████╗      ███████║██║   ██║██╔████╔██║█████╗{Colors.RESET}  
{Colors.BRIGHT_CYAN}  ██║╚██╔╝██║██╔══██║██╔═══╝ ██║     ██╔══╝      ██╔══██║██║   ██║██║╚██╔╝██║██╔══╝{Colors.RESET}  
{Colors.BRIGHT_BLUE}  ██║ ╚═╝ ██║██║  ██║██║     ███████╗███████╗    ██║  ██║╚██████╔╝██║ ╚═╝ ██║███████╗{Colors.RESET}
{Colors.BRIGHT_MAGENTA}  ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝     ╚══════╝╚══════╝    ╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝{Colors.RESET}
{Colors.BRIGHT_WHITE}                           🏠 LifeSmart IoT Integration Test Suite 🏠{Colors.RESET}
"""
    return ascii_art


def create_version_table(info: dict) -> str:
    """创建版本信息表格"""

    # ANSI颜色代码
    class Colors:
        RESET = "\033[0m"
        BOLD = "\033[1m"
        GREEN = "\033[32m"
        YELLOW = "\033[33m"
        BLUE = "\033[34m"
        MAGENTA = "\033[35m"
        CYAN = "\033[36m"
        BRIGHT_GREEN = "\033[92m"
        BRIGHT_YELLOW = "\033[93m"
        BRIGHT_BLUE = "\033[94m"
        BRIGHT_MAGENTA = "\033[95m"
        BRIGHT_CYAN = "\033[96m"
        BRIGHT_WHITE = "\033[97m"
        BRIGHT_RED = "\033[91m"

    # 安全的字符串格式化函数
    def safe_format(value, width=51):
        """安全的字符串格式化，处理None值"""
        if value is None:
            value = "unknown"
        return f"{str(value):<{width}}"

    # 计算Git信息长度以正确对齐
    git_info = f"{info['git_commit']} ({info['git_branch']})"
    git_padding = 51 - len(git_info)
    git_padding = max(0, git_padding)  # 确保不为负数

    version_info = f"""
{Colors.BRIGHT_CYAN}  📊 Test Environment Information:{Colors.RESET}
{Colors.CYAN}  ┌─────────────────────────┬─────────────────────────────────────────────────────┐{Colors.RESET}
{Colors.CYAN}  │{Colors.RESET} {Colors.BRIGHT_YELLOW}🐍 Python{Colors.RESET}              {Colors.CYAN}│{Colors.RESET} {Colors.GREEN}{safe_format(info['python'])}{Colors.RESET} {Colors.CYAN}│{Colors.RESET}
{Colors.CYAN}  │{Colors.RESET} {Colors.BRIGHT_BLUE}🧪 pytest{Colors.RESET}              {Colors.CYAN}│{Colors.RESET} {Colors.GREEN}{safe_format(info['pytest'])}{Colors.RESET} {Colors.CYAN}│{Colors.RESET}
{Colors.CYAN}  │{Colors.RESET} {Colors.BRIGHT_MAGENTA}📝 Git Commit{Colors.RESET}          {Colors.CYAN}│{Colors.RESET} {Colors.YELLOW}{git_info}{' ' * git_padding}{Colors.RESET} {Colors.CYAN}│{Colors.RESET}
{Colors.CYAN}  │{Colors.RESET} {Colors.BRIGHT_GREEN}🏠 Home Assistant{Colors.RESET}      {Colors.CYAN}│{Colors.RESET} {Colors.BRIGHT_GREEN}{safe_format(info['homeassistant'])}{Colors.RESET} {Colors.CYAN}│{Colors.RESET}
{Colors.CYAN}  │{Colors.RESET} {Colors.BRIGHT_RED}🔌 pytest-HA Plugin{Colors.RESET}    {Colors.CYAN}│{Colors.RESET} {Colors.GREEN}{safe_format(info['pytest_ha'])}{Colors.RESET} {Colors.CYAN}│{Colors.RESET}
{Colors.CYAN}  │{Colors.RESET} {Colors.BRIGHT_CYAN}🐍 Conda Environment{Colors.RESET}   {Colors.CYAN}│{Colors.RESET} {Colors.MAGENTA}{safe_format(info['conda_env'])}{Colors.RESET} {Colors.CYAN}│{Colors.RESET}
{Colors.CYAN}  │{Colors.RESET} {Colors.BRIGHT_WHITE}🌐 aiohttp{Colors.RESET}             {Colors.CYAN}│{Colors.RESET} {Colors.GREEN}{safe_format(info['aiohttp'])}{Colors.RESET} {Colors.CYAN}│{Colors.RESET}
{Colors.CYAN}  │{Colors.RESET} {Colors.BRIGHT_YELLOW}⚡ AsyncIO{Colors.RESET}             {Colors.CYAN}│{Colors.RESET} {Colors.CYAN}{safe_format(info['asyncio_version'])}{Colors.RESET} {Colors.CYAN}│{Colors.RESET}
{Colors.CYAN}  └─────────────────────────┴─────────────────────────────────────────────────────┘{Colors.RESET}
"""
    return version_info


def create_maple_banner(info: dict) -> str:
    """创建完整的MAPLE HOME横幅"""

    # ANSI颜色代码
    class Colors:
        RESET = "\033[0m"
        DIM = "\033[2m"
        CYAN = "\033[36m"
        BRIGHT_GREEN = "\033[92m"

    # 组合所有部分
    ascii_art = create_maple_home_ascii()
    version_table = create_version_table(info)

    # 底部装饰
    footer = f"""
{Colors.DIM}{Colors.CYAN}  ═══════════════════════════════════════════════════════════════════════════════{Colors.RESET}
{Colors.BRIGHT_GREEN}  🚀 Ready to test LifeSmart IoT devices! Good luck! 🍀{Colors.RESET}
{Colors.DIM}{Colors.CYAN}  ═══════════════════════════════════════════════════════════════════════════════{Colors.RESET}
"""

    return ascii_art + version_table + footer


def pytest_sessionstart(session):
    """
    在pytest测试会话开始时显示MAPLE HOME风格的版本信息横幅
    """
    # 收集环境信息
    info = get_environment_info()

    # 创建并显示横幅
    banner = create_maple_banner(info)

    # 分行输出以确保格式正确
    for line in banner.split("\n"):
        if line:  # 跳过空行
            print(line)

    # 添加一个空行分隔测试输出
    print()
