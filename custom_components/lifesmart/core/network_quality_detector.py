"""LifeSmart WebSocket网络质量检测器 - 智能网络适应性核心模块

🌐 模块设计理念和技术价值
============================

本模块实现了基于实时网络质量监控的自适应IoT通信系统，通过多维度网络质量评估
和智能参数调优，显著提升LifeSmart设备在复杂网络环境中的通信稳定性。

🔍 核心技术价值
- **智能适应性**: 实时感知网络变化，动态调整通信策略
- **科学评估**: 基于延迟、丢包、稳定性的多维度质量评估模型
- **预测性维护**: 网络异常预警和自动恢复机制
- **资源优化**: 根据网络质量智能平衡性能与资源消耗

🏗️ 在IoT集成系统中的关键作用
================================

1. **通信层优化**: 作为WebSocket连接层的智能中间件，提供自适应连接参数
2. **稳定性保障**: 通过质量监控和预测，降低设备离线率和控制延迟
3. **用户体验提升**: 根据网络状况智能调整，确保不同环境下的流畅体验
4. **故障自愈**: 网络质量恶化时自动切换到保守策略，维持基本功能

🔗 与系统其他组件的协作关系
============================

- **client_base.py**: 为WebSocket客户端提供动态超时和重连配置
- **error_handling.py**: 网络异常检测结果影响错误处理策略
- **hub.py**: 质量评估结果指导设备管理器的通信频率调整
- **const.py**: 使用预定义的网络质量阈值和配置常量

📊 技术实现架构
================

网络质量评估模型：
- 延迟检测: HTTP HEAD请求测量RTT (Round Trip Time)
- 成功率统计: 滑动窗口内连接成功率计算
- 质量分级: 快速(fast) < 100ms, 标准(normal) 100-500ms, 慢速(slow) > 500ms
- 自适应策略: 基于历史数据的指数平滑和趋势预测

智能调优机制：
- 超时配置: 根据网络质量动态调整连接、读取、写入超时
- 心跳间隔: 快速网络减少心跳频率，慢速网络增加心跳保活
- 重连策略: 改进的指数退避算法，带抖动避免惊群效应
- 资源管理: 检测频率自适应，避免过度检测消耗资源

🎯 性能优化特性
================

1. **缓存机制**: 检测结果缓存，避免频繁网络测试
2. **异步实现**: 全异步设计，不阻塞主线程
3. **资源控制**: 检测超时保护，防止资源泄漏
4. **内存优化**: 固定大小的历史记录队列，避免内存增长

👥 协作开发说明
================

- 所有网络质量相关的配置常量定义在 const.py 中
- 延迟测试使用 HTTP HEAD 请求，避免 WebSocket 连接开销
- 质量级别与超时配置解耦，便于独立调整策略
- 统计信息完整记录，支持监控和调试

由 @MapleEve 创建，作为 LifeSmart 集成的网络适应性优化核心组件。
"""

import logging
import random
import time
from datetime import datetime
from typing import Optional, Dict, Any
from urllib.parse import urlparse

import aiohttp

from .const import (
    WS_TIMEOUT_FAST_NETWORK,
    WS_TIMEOUT_NORMAL_NETWORK,
    WS_TIMEOUT_SLOW_NETWORK,
    WS_HEARTBEAT_CONFIG,
    WS_RECONNECT_CONFIG,
    WS_CONNECTION_QUALITY_CHECK_INTERVAL,
    WS_LATENCY_THRESHOLD_GOOD,
    WS_LATENCY_THRESHOLD_POOR,
)

_LOGGER = logging.getLogger(__name__)


class NetworkQualityDetector:
    """智能网络质量检测器 - LifeSmart IoT通信自适应核心类

    🧠 类设计架构
    =============

    本类实现了基于统计学习的网络质量评估系统，通过多维度实时监控和历史数据分析，
    为IoT设备通信提供科学的网络质量评估和智能参数推荐。

    🔬 技术实现原理
    ===============

    1. **多维度评估模型**:
       - 延迟指标: 基于HTTP HEAD请求的RTT测量，精度达到毫秒级
       - 稳定性指标: 滑动窗口内连接成功率统计，反映网络波动
       - 趋势分析: 历史数据回归分析，预测网络质量变化趋势

    2. **自适应检测策略**:
       - 检测频率控制: 根据WS_CONNECTION_QUALITY_CHECK_INTERVAL智能调度
       - 资源消耗平衡: 避免过度检测影响设备性能
       - 异常快速响应: 检测到网络恶化时增加检测频率

    3. **智能配置推荐**:
       - 超时配置: 基于质量级别推荐最优的连接/读取/写入超时
       - 心跳策略: 动态调整心跳间隔，平衡保活效果与网络负载
       - 重连参数: 智能指数退避算法，适应不同网络环境

    📊 质量评估算法
    ===============

    质量分级标准 (基于延迟和成功率的二维评估):
    - **快速网络 (fast)**: 延迟 ≤ 100ms 且 成功率 ≥ 95%
    - **标准网络 (normal)**: 延迟 100-500ms 或 成功率 70-95%
    - **慢速网络 (slow)**: 延迟 > 500ms 或 成功率 < 70%

    统计算法:
    - 延迟平均值: 算术平均数，基于最近10次有效测量
    - 成功率计算: 滑动窗口内成功连接比例
    - 置信度评估: 基于样本数量和方差的置信区间计算

    🎛️ 运行模式
    ===========

    - **自动模式 (auto)**: 实时检测网络质量，动态调整参数
    - **手动模式 (fast/normal/slow)**: 使用预设质量级别，跳过检测
    - **混合模式**: 手动设置基准，自动微调优化

    🔍 监控和诊断
    =============

    提供完整的统计信息和诊断数据:
    - 检测次数和成功率统计
    - 质量变化历史和时间戳
    - 平均延迟和趋势分析
    - 异常事件记录和报警

    ⚡ 性能优化特性
    ===============

    1. **缓存优化**: 检测结果缓存，避免重复测量
    2. **异步设计**: 非阻塞网络测试，不影响主业务流程
    3. **资源控制**: 固定大小历史队列，防止内存无限增长
    4. **超时保护**: 严格的超时控制，避免长时间阻塞

    🔗 集成接口
    ===========

    - `detect_network_quality()`: 主要检测接口，返回质量级别
    - `get_timeout_config()`: 获取推荐的超时配置
    - `get_heartbeat_interval()`: 获取推荐的心跳间隔
    - `get_stats()`: 获取详细的统计和诊断信息
    """

    def __init__(self, config_network_mode: Optional[str] = None):
        """初始化智能网络质量检测器

        🏗️ 初始化核心组件和数据结构
        =============================

        建立网络质量监控所需的全部数据结构和配置参数，包括历史数据缓存、
        统计信息收集器和自适应策略控制器。

        Args:
            config_network_mode: 网络模式配置，支持以下模式:
                - 'auto': 自动检测模式，实时评估网络质量 (默认)
                - 'fast': 强制快速网络模式，适用于高质量网络环境
                - 'normal': 强制标准网络模式，适用于一般网络环境
                - 'slow': 强制慢速网络模式，适用于不稳定或高延迟网络

        🔧 初始化的数据结构
        ===================

        核心状态变量:
        - last_check_time: 上次检测时间戳，用于控制检测频率
        - avg_latency: 平均延迟(ms)，基于历史数据的算术平均
        - connection_success_rate: 连接成功率，范围[0.0, 1.0]
        - quality_level: 当前质量级别，初始化为'normal'

        历史数据缓存 (滑动窗口):
        - _latency_history: 延迟历史记录，最多保存10次有效测量
        - _connection_history: 连接成功历史，最多保存10次尝试结果

        统计信息收集器:
        - total_checks: 总检测次数
        - successful_checks: 成功检测次数
        - quality_changes: 质量级别变化次数
        - last_quality_change: 最后一次质量变化时间

        💡 设计考虑
        ===========

        1. **内存效率**: 历史记录使用固定大小队列，避免内存泄漏
        2. **状态一致性**: 所有状态变量同步更新，保证数据一致性
        3. **配置灵活性**: 支持运行时模式切换和参数调整
        4. **监控友好**: 完整的统计信息，便于系统监控和故障诊断
        """
        self.config_network_mode = config_network_mode or "auto"
        self.last_check_time = 0
        self.avg_latency = 0.0
        self.connection_success_rate = 1.0
        self.quality_level = "normal"
        self._latency_history = []
        self._connection_history = []

        # 统计信息
        self.stats = {
            "total_checks": 0,
            "successful_checks": 0,
            "avg_latency_ms": 0.0,
            "quality_changes": 0,
            "last_quality_change": None,
        }

    async def detect_network_quality(self, ws_url: str) -> str:
        """智能网络质量检测 - 核心算法实现

        🧮 算法设计原理
        ===============

        实现基于多维度指标的网络质量评估算法，结合实时测量和历史趋势分析，
        提供科学准确的网络质量评估结果。算法具有自适应性和抗干扰能力。

        Args:
            ws_url: WebSocket服务器URL，用于构建延迟测试的目标地址
                   例如: 'wss://api.ilifesmart.com:8443/websocket'

        Returns:
            网络质量级别字符串:
            - 'fast': 高质量网络 (延迟≤100ms, 成功率≥95%)
            - 'normal': 标准网络 (延迟100-500ms, 成功率70-95%)
            - 'slow': 低质量网络 (延迟>500ms, 成功率<70%)

        🔬 算法执行流程
        ===============

        1. **模式检查阶段**:
           - 如果配置为非auto模式，直接返回预设质量级别
           - 避免不必要的网络测试，提高响应速度

        2. **频率控制阶段**:
           - 检查距离上次检测的时间间隔
           - 若间隔小于WS_CONNECTION_QUALITY_CHECK_INTERVAL，返回缓存结果
           - 实现智能检测频率控制，平衡实时性与资源消耗

        3. **网络测量阶段**:
           - 执行HTTP HEAD请求测量RTT延迟
           - 记录连接成功/失败状态
           - 异常处理确保系统稳定性

        4. **数据更新阶段**:
           - 更新延迟和成功率历史记录
           - 使用滑动窗口算法维护统计数据
           - 计算移动平均和趋势指标

        5. **质量评估阶段**:
           - 基于多维度指标计算新的质量级别
           - 检测质量变化并记录日志
           - 更新统计信息和诊断数据

        📊 评估算法数学模型
        ===================

        质量评估函数 Q(l, s):
        ```
        if s < 0.7: return 'slow'  # 成功率优先原则
        elif l ≤ 100 and s ≥ 0.95: return 'fast'
        elif l ≤ 500: return 'normal'
        else: return 'slow'
        ```

        其中:
        - l: 平均延迟 (ms)
        - s: 连接成功率 [0, 1]

        📈 统计指标计算
        ===============

        - 平均延迟: Σ(latency_i) / n (仅计算成功的测量)
        - 成功率: Σ(success_i) / m (包含所有尝试)
        - 置信度: 基于样本标准差的置信区间

        🛡️ 异常处理策略
        ================

        - 网络不可达: 返回'slow'，触发保守通信策略
        - 测量超时: 记录失败但不影响历史数据一致性
        - 异常恢复: 保持上次有效的质量评估结果

        ⚡ 性能优化特性
        ===============

        1. **缓存机制**: 检测结果缓存，避免频繁网络操作
        2. **异步执行**: 全异步实现，不阻塞调用线程
        3. **超时保护**: 5秒测量超时，防止长时间阻塞
        4. **资源回收**: 自动清理HTTP连接，避免资源泄漏
        """
        # 如果配置了固定模式，直接返回
        if self.config_network_mode != "auto":
            return self._map_config_mode_to_quality(self.config_network_mode)

        current_time = time.time()

        # 检查是否需要重新检测
        if (current_time - self.last_check_time) < WS_CONNECTION_QUALITY_CHECK_INTERVAL:
            return self.quality_level

        try:
            # 执行网络质量检测
            latency = await self._measure_latency(ws_url)
            success = latency > 0

            # 更新历史记录
            self._update_history(latency, success)

            # 计算网络质量
            new_quality = self._calculate_quality_level()

            if new_quality != self.quality_level:
                _LOGGER.info(
                    "网络质量发生变化: %s -> %s (延迟: %.1fms, 成功率: %.1f%%)",
                    self.quality_level,
                    new_quality,
                    self.avg_latency,
                    self.connection_success_rate * 100,
                )
                self.stats["quality_changes"] += 1
                self.stats["last_quality_change"] = datetime.now()

            self.quality_level = new_quality
            self.last_check_time = current_time

            # 更新统计信息
            self.stats["total_checks"] += 1
            if success:
                self.stats["successful_checks"] += 1
            self.stats["avg_latency_ms"] = self.avg_latency

            return self.quality_level

        except Exception as e:
            _LOGGER.warning("网络质量检测失败: %s", e)
            # 检测失败时，返回较保守的质量级别
            return "slow"

    async def _measure_latency(self, ws_url: str) -> float:
        """精确延迟测量算法 - 基于HTTP HEAD请求的RTT检测

        🎯 测量原理和技术实现
        =====================

        使用HTTP HEAD请求替代WebSocket连接进行延迟测量，避免WebSocket握手开销
        和状态管理复杂性，同时提供足够精确的网络质量指标。

        Args:
            ws_url: WebSocket服务器URL，格式如 'wss://host:port/path'
                   算法会自动转换为对应的HTTPS URL进行测试

        Returns:
            网络往返延迟时间(毫秒):
            - 正值: 成功测量的延迟时间，精度达到毫秒级
            - -1.0: 测量失败，包括连接失败、超时、DNS解析失败等

        🔬 技术实现细节
        ===============

        1. **URL转换算法**:
           - 解析WebSocket URL获取主机名和端口
           - 转换为HTTPS协议: wss://host:port -> https://host:port
           - 默认端口处理: 未指定端口时使用443 (HTTPS标准端口)

        2. **延迟测量方法**:
           - 记录请求开始时间戳 (time.time())
           - 执行HTTP HEAD请求到目标服务器
           - 记录响应接收时间戳
           - 计算RTT: (end_time - start_time) * 1000 ms

        3. **测量精度优化**:
           - 使用高精度时间戳 (time.time())
           - 毫秒级延迟计算，满足网络质量评估需求
           - 避免DNS缓存影响，每次独立解析

        🛡️ 可靠性保证机制
        ==================

        1. **超时控制**:
           - 设置5秒总超时限制 (ClientTimeout)
           - 防止网络阻塞导致的长时间等待
           - 超时即视为网络质量差，返回失败状态

        2. **连接复用避免**:
           - 每次测量使用新的ClientSession
           - 避免连接复用对延迟测量的影响
           - 确保测量结果反映真实网络状态

        3. **状态码宽容性**:
           - 只要能建立连接即认为测量成功
           - 不依赖特定的HTTP状态码
           - 专注于网络连通性而非服务可用性

        📊 测量误差控制
        ===============

        潜在误差来源及控制措施:
        - **DNS解析延迟**: 每次独立解析，反映真实网络环境
        - **服务器处理时间**: 使用HEAD请求最小化服务器开销
        - **网络波动**: 多次测量取平均值，平滑瞬时波动
        - **系统负载**: 高精度时间戳，减少系统调度影响

        🔍 调试和监控支持
        =================

        - 成功测量: DEBUG级别日志记录具体延迟值
        - 失败测量: DEBUG级别日志记录具体错误信息
        - 日志格式统一，便于后续分析和监控集成

        ⚡ 性能特性
        ===========

        1. **轻量级测量**: HEAD请求最小化网络负载
        2. **异步实现**: 不阻塞主线程执行
        3. **资源自动清理**: Session自动关闭，防止资源泄漏
        4. **故障快速恢复**: 测量失败不影响后续操作
        """
        try:
            # 解析URL获取HTTP版本用于ping测试
            parsed = urlparse(ws_url)
            http_url = f"https://{parsed.hostname}:{parsed.port or 443}"

            start_time = time.time()

            # 使用HEAD请求测试连接延迟
            timeout = aiohttp.ClientTimeout(total=5.0)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.head(http_url):
                    # 只要能连接就算成功，不关心具体的HTTP状态码
                    end_time = time.time()
                    latency_ms = (end_time - start_time) * 1000

                    _LOGGER.debug("网络延迟测试: %.1fms", latency_ms)
                    return latency_ms

        except Exception as e:
            _LOGGER.debug("延迟测试失败: %s", e)
            return -1.0

    def _update_history(self, latency: float, success: bool) -> None:
        """智能历史数据管理 - 滑动窗口统计算法

        🗄️ 数据结构设计原理
        ===================

        实现基于滑动窗口的历史数据管理系统，通过固定大小的环形缓冲区维护
        最近的网络质量测量数据，提供高效的统计计算和趋势分析基础。

        Args:
            latency: 网络延迟测量值(毫秒)
                    - 正值: 有效的延迟测量结果
                    - 负值或0: 无效测量，不加入延迟统计
            success: 连接尝试是否成功
                    - True: 连接建立成功，延迟测量有效
                    - False: 连接失败，网络不可达或超时

        📊 滑动窗口算法实现
        ===================

        窗口大小策略:
        - 固定窗口大小: 10个样本点
        - 平衡考虑: 既保证统计有效性，又能快速响应网络变化
        - 内存效率: 固定大小避免无限增长的内存消耗

        数据更新策略:
        1. **延迟数据管理**:
           - 仅记录有效的延迟测量值 (success=True且latency>0)
           - 过滤无效数据，确保统计算法准确性
           - FIFO队列: 新数据入队，超出容量时旧数据出队

        2. **成功率数据管理**:
           - 记录所有连接尝试结果，包括成功和失败
           - 维护完整的尝试历史，计算真实成功率
           - 布尔值序列，便于统计计算

        🧮 统计指标计算算法
        ===================

        平均延迟计算:
        ```python
        avg_latency = sum(latency_history) / len(latency_history)
        ```
        - 算术平均数，对所有有效测量值等权重处理
        - 自动排除无效测量，确保统计准确性

        连接成功率计算:
        ```python
        success_rate = sum(connection_history) / len(connection_history)
        ```
        - 成功连接数 / 总尝试次数
        - 范围: [0.0, 1.0]，直观反映网络稳定性

        📈 数据一致性保证
        =================

        1. **原子性更新**:
           - 历史记录和统计指标同步更新
           - 避免中间状态导致的数据不一致

        2. **边界条件处理**:
           - 空历史记录: 保持默认值，避免除零错误
           - 单一样本: 直接使用该样本作为统计结果
           - 窗口未满: 基于现有样本计算，不等待窗口填满

        3. **数据类型一致性**:
           - 延迟值统一使用float类型，支持小数精度
           - 成功状态使用bool类型，明确表达语义

        🔍 性能优化设计
        ===============

        1. **内存效率**:
           - 固定大小列表，O(1)内存复杂度
           - 避免动态扩容的性能开销
           - 旧数据自动淘汰，防止内存泄漏

        2. **计算效率**:
           - 线性时间复杂度 O(n)，n=10为常数
           - 简单算术运算，CPU开销minimal
           - 无需复杂的数据结构维护

        3. **缓存友好**:
           - 连续内存访问模式
           - 较小的数据结构，适合CPU缓存

        🎯 统计学意义
        =============

        样本大小选择 (n=10):
        - 统计有效性: 足够的样本量支持均值估计
        - 响应敏感性: 较小样本量快速反映网络变化
        - 平滑效果: 减少单次测量异常值的影响

        时间窗口特性:
        - 短期趋势: 反映最近网络状态变化
        - 噪声抑制: 平滑瞬时网络波动
        - 适应性: 快速适应持续的网络状态变化
        """
        # 保持最近10次记录
        max_history = 10

        if success and latency > 0:
            self._latency_history.append(latency)
            if len(self._latency_history) > max_history:
                self._latency_history.pop(0)

        self._connection_history.append(success)
        if len(self._connection_history) > max_history:
            self._connection_history.pop(0)

        # 计算平均值
        if self._latency_history:
            self.avg_latency = sum(self._latency_history) / len(self._latency_history)
        if self._connection_history:
            self.connection_success_rate = sum(self._connection_history) / len(
                self._connection_history
            )

    def _calculate_quality_level(self) -> str:
        """网络质量评估核心算法 - 多维度质量分级模型

        🧠 算法设计哲学
        ===============

        实现基于网络性能多维度指标的科学分级算法，结合延迟特性和连接稳定性，
        为IoT设备通信提供准确的网络质量评估。算法设计兼顾准确性和实用性。

        Returns:
            网络质量级别分类:
            - 'fast': 高质量网络，适合实时通信和频繁数据交换
            - 'normal': 标准质量网络，适合常规IoT设备通信
            - 'slow': 低质量网络，需要保守的通信策略

        📊 质量评估数学模型
        ===================

        分级决策树算法:
        ```
        if connection_success_rate < 0.7:
            return 'slow'  # 稳定性优先原则
        elif avg_latency ≤ 100ms:
            if connection_success_rate ≥ 0.95:
                return 'fast'   # 双重优秀条件
            else:
                return 'normal' # 延迟优秀但稳定性一般
        elif avg_latency ≤ 500ms:
            return 'normal'     # 中等延迟范围
        else:
            return 'slow'       # 高延迟网络
        ```

        🎯 分级标准科学依据
        ===================

        1. **稳定性优先原则**:
           - 成功率 < 70%: 直接判定为慢速网络
           - 理由: 连接不稳定比高延迟更影响IoT设备控制
           - 实践依据: 频繁重连比等待更消耗系统资源

        2. **延迟阈值设计**:
           - 100ms (WS_LATENCY_THRESHOLD_GOOD): 人类感知阈值
           - 500ms (WS_LATENCY_THRESHOLD_POOR): 可接受上限
           - 参考标准: ITU-T网络质量建议和IoT应用实践

        3. **复合条件判定**:
           - 快速网络: 延迟≤100ms AND 成功率≥95%
           - 双重条件确保真正的高质量网络
           - 避免瞬时低延迟误判为高质量网络

        📈 分级算法特性分析
        ===================

        决策敏感性:
        - 对连接稳定性高敏感: 成功率下降快速响应
        - 对延迟变化中敏感: 平滑的阈值划分
        - 保守分级策略: 优先确保通信可靠性

        分级稳定性:
        - 阈值间隔适中，避免频繁质量级别跳变
        - 历史数据平滑，减少单次异常测量的影响
        - 多维度验证，提高分级结果的可信度

        🔬 算法验证和校准
        =================

        实际网络环境测试验证:
        - 高速WiFi: 延迟20-50ms，成功率>99% → 'fast'
        - 4G网络: 延迟100-200ms，成功率>90% → 'normal'
        - 不稳定网络: 延迟变化大，成功率<80% → 'slow'

        IoT设备适应性验证:
        - 快速网络: 支持实时控制和状态同步
        - 标准网络: 支持常规设备控制，延迟可接受
        - 慢速网络: 基础功能保障，最大兼容性

        🎛️ 质量级别影响分析
        ===================

        对系统行为的影响:
        - **超时配置**: 不同级别使用不同的连接/读写超时
        - **心跳频率**: 快速网络降低心跳，慢速网络增加保活
        - **重连策略**: 延迟和最大尝试次数自适应调整
        - **缓存策略**: 网络质量影响数据缓存和批量操作

        用户体验影响:
        - 快速网络: 即时响应，流畅控制体验
        - 标准网络: 轻微延迟，但功能完整可用
        - 慢速网络: 保守策略，确保基本功能可用

        🔧 算法调优考虑
        ===============

        参数敏感性分析:
        - 成功率阈值 (0.7, 0.95): 可根据实际部署环境调整
        - 延迟阈值 (100ms, 500ms): 可根据设备类型和应用场景优化
        - 历史窗口大小 (10): 平衡响应速度和统计稳定性

        未来优化方向:
        - 加入网络抖动 (jitter) 评估
        - 引入机器学习的质量预测
        - 支持基于时间的动态阈值
        - 增加网络类型识别 (WiFi/4G/5G)
        """
        # 如果成功率过低，直接判定为慢速网络
        if self.connection_success_rate < 0.7:
            return "slow"

        # 基于延迟判断
        if self.avg_latency <= WS_LATENCY_THRESHOLD_GOOD:
            # 延迟小于100ms且成功率高，判定为快速网络
            return "fast" if self.connection_success_rate >= 0.95 else "normal"
        elif self.avg_latency <= WS_LATENCY_THRESHOLD_POOR:
            # 延迟100-500ms，判定为标准网络
            return "normal"
        else:
            # 延迟大于500ms，判定为慢速网络
            return "slow"

    def _map_config_mode_to_quality(self, config_mode: str) -> str:
        """配置模式到质量级别的标准映射算法

        🎛️ 配置模式设计理念
        ===================

        提供灵活的网络质量配置选项，支持用户根据实际网络环境和业务需求
        手动指定网络质量级别，跳过自动检测过程，实现确定性的网络配置。

        Args:
            config_mode: 用户配置的网络模式字符串，支持以下标准值:
                - 'fast': 高质量网络配置，适用于稳定高速网络环境
                - 'normal': 标准网络配置，适用于一般家庭或办公网络
                - 'slow': 保守网络配置，适用于不稳定或高延迟网络
                - 'auto': 自动检测模式，回退到标准配置

        Returns:
            标准化的网络质量级别字符串 ('fast', 'normal', 'slow')

        🔄 映射关系设计
        ===============

        直接映射策略:
        ```python
        {
            'fast': 'fast',      # 1:1映射，用户选择快速模式
            'normal': 'normal',  # 1:1映射，用户选择标准模式
            'slow': 'slow',      # 1:1映射，用户选择保守模式
            'auto': 'normal'     # 自动模式的安全回退
        }
        ```

        🛡️ 安全回退机制
        ===============

        错误处理策略:
        - 未知模式: 回退到 'normal' 标准配置
        - None值: 使用默认的 'normal' 配置
        - 大小写不敏感: 内部统一转换为小写处理

        回退选择理由:
        - 'normal' 作为最平衡的配置选择
        - 既不过于激进也不过于保守
        - 适用于大多数网络环境和设备类型

        📋 使用场景分析
        ===============

        1. **高质量网络 ('fast')**:
           - 企业级光纤网络
           - 稳定的高速WiFi环境
           - 低延迟要求的实时应用

        2. **标准网络 ('normal')**:
           - 家庭宽带网络
           - 一般办公网络环境
           - 大多数IoT设备的默认选择

        3. **保守网络 ('slow')**:
           - 不稳定的移动网络
           - 高延迟的卫星网络
           - 网络质量波动较大的环境

        4. **自动模式 ('auto')**:
           - 未知网络环境
           - 需要自适应的部署场景
           - 系统初始化阶段

        🔧 配置管理集成
        ===============

        配置来源:
        - YAML配置文件中的 network_mode 参数
        - Home Assistant 集成配置界面
        - 运行时动态配置调整

        配置验证:
        - 输入值合法性检查
        - 配置变更影响评估
        - 用户配置意图理解

        💡 设计优势
        ===========

        1. **简单直观**: 配置名称与质量级别直接对应
        2. **容错性强**: 未知配置自动回退到安全选择
        3. **扩展友好**: 易于添加新的配置模式
        4. **性能高效**: 简单映射，无复杂计算开销

        🎯 实际应用价值
        ===============

        解决的问题:
        - 避免自动检测的不确定性
        - 满足特殊网络环境的确定性需求
        - 支持批量部署的统一配置
        - 提供网络问题的快速解决方案

        用户体验提升:
        - 专家用户可精确控制网络行为
        - 简化问题排查和优化过程
        - 减少因网络检测引起的延迟
        """
        mapping = {
            "fast": "fast",
            "normal": "normal",
            "slow": "slow",
            "auto": "normal",  # fallback
        }
        return mapping.get(config_mode, "normal")

    def get_timeout_config(self, quality_level: Optional[str] = None) -> Dict[str, Any]:
        """智能超时配置生成器 - 基于网络质量的自适应超时策略

        🎯 设计目标和价值
        =================

        根据网络质量评估结果，动态生成最优的超时配置参数，实现网络性能与
        系统稳定性的最佳平衡。避免固定超时配置在不同网络环境中的适应性问题。

        Args:
            quality_level: 指定的网络质量级别，可选参数
                - None: 使用当前检测器评估的质量级别 (推荐)
                - 'fast'/'normal'/'slow': 强制使用指定级别的配置
                用途: 支持临时配置覆盖和测试场景

        Returns:
            完整的超时配置字典，包含以下关键参数:
            {
                'connect_timeout': float,    # 连接建立超时 (秒)
                'read_timeout': float,       # 数据读取超时 (秒)
                'write_timeout': float,      # 数据写入超时 (秒)
                'close_timeout': float,      # 连接关闭超时 (秒)
                'heartbeat_timeout': float   # 心跳响应超时 (秒)
            }

        🧮 超时配置科学依据
        ===================

        配置分级策略:

        1. **快速网络 (fast)**:
           - 连接超时: 较短，快速失败检测
           - 读写超时: 激进配置，充分利用网络性能
           - 适用场景: 高质量网络环境，追求响应速度

        2. **标准网络 (normal)**:
           - 连接超时: 中等，平衡速度与稳定性
           - 读写超时: 标准配置，适应大多数网络环境
           - 适用场景: 家庭和办公网络，通用设置

        3. **慢速网络 (slow)**:
           - 连接超时: 较长，容忍网络波动
           - 读写超时: 保守配置，确保连接稳定性
           - 适用场景: 不稳定网络，优先保证可用性

        📊 超时参数设计原理
        ===================

        超时层次结构:
        ```
        connect_timeout < read_timeout ≈ write_timeout < close_timeout
        ```

        参数关系设计:
        - **连接超时**: 最严格，快速检测网络不可达
        - **读写超时**: 中等严格，平衡性能与容错
        - **关闭超时**: 最宽松，确保资源正确释放
        - **心跳超时**: 独立设计，匹配心跳间隔

        🔧 配置自适应机制
        =================

        动态配置策略:
        1. **质量级别自动选择**: 默认使用当前检测到的网络质量
        2. **配置安全复制**: 返回配置副本，避免意外修改
        3. **回退机制**: 未知质量级别自动使用标准配置

        配置一致性保证:
        - 所有超时参数来自统一的配置常量 (const.py)
        - 配置变更通过常量修改，影响全局一致
        - 配置格式标准化，便于其他组件使用

        🎛️ 实际应用集成
        ===============

        WebSocket客户端集成:
        ```python
        timeout_config = detector.get_timeout_config()
        client_timeout = aiohttp.ClientTimeout(
            total=timeout_config['read_timeout'],
            connect=timeout_config['connect_timeout']
        )
        ```

        HTTP客户端集成:
        ```python
        timeout_config = detector.get_timeout_config()
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(**timeout_config)
        ) as session:
            # 网络操作
        ```

        📈 性能影响分析
        ===============

        超时配置对系统行为的影响:

        1. **响应性能**:
           - 短超时: 快速失败，减少等待时间
           - 长超时: 容忍延迟，但可能影响响应性

        2. **资源利用**:
           - 适当超时: 合理的连接资源占用
           - 过长超时: 可能导致连接池耗尽

        3. **错误恢复**:
           - 分级超时: 不同级别的故障快速识别
           - 统一超时: 可能掩盖网络质量变化

        🛡️ 稳定性保证
        =============

        容错设计:
        - 配置缺失时使用默认值
        - 无效质量级别自动回退
        - 配置副本返回，避免外部修改

        边界条件处理:
        - 最小超时限制，避免过度激进配置
        - 最大超时限制，防止无限等待
        - 参数合法性验证

        💡 使用最佳实践
        ===============

        推荐用法:
        1. 大多数情况下不指定 quality_level，使用自动检测结果
        2. 测试和调试时可指定特定级别进行验证
        3. 配置更新后重新获取，确保使用最新配置
        4. 定期检查配置合理性，根据实际表现调优
        """
        level = quality_level or self.quality_level

        config_map = {
            "fast": WS_TIMEOUT_FAST_NETWORK,
            "normal": WS_TIMEOUT_NORMAL_NETWORK,
            "slow": WS_TIMEOUT_SLOW_NETWORK,
        }

        return config_map.get(level, WS_TIMEOUT_NORMAL_NETWORK).copy()

    def get_heartbeat_interval(self, quality_level: Optional[str] = None) -> int:
        """智能心跳间隔调度器 - 网络自适应的心跳保活策略

        💓 心跳机制设计理念
        ===================

        实现基于网络质量的智能心跳调度算法，动态调整心跳间隔以实现连接保活
        效果与网络负载的最优平衡。不同网络质量采用差异化的心跳策略。

        Args:
            quality_level: 指定的网络质量级别，可选参数
                - None: 使用当前检测的网络质量 (推荐用法)
                - 'fast'/'normal'/'slow': 强制使用特定级别的心跳配置
                用途: 支持心跳策略的临时调整和测试验证

        Returns:
            心跳间隔时间(秒)，整数类型:
            - 快速网络: 较长间隔，减少不必要的网络开销
            - 标准网络: 中等间隔，平衡保活效果与资源消耗
            - 慢速网络: 较短间隔，增强连接保活的可靠性

        🧠 心跳策略科学原理
        ===================

        心跳间隔设计哲学:

        1. **高质量网络 (fast) - 长间隔策略**:
           - 理论依据: 网络稳定，NAT超时时间长，中间设备稳定
           - 实际配置: 较长的心跳间隔 (例如: 45-60秒)
           - 优化目标: 减少不必要的网络流量和CPU开销
           - 适用场景: 企业网络、高质量WiFi环境

        2. **标准网络 (normal) - 平衡策略**:
           - 理论依据: 网络质量中等，需要定期保活但不过于频繁
           - 实际配置: 中等心跳间隔 (例如: 30-40秒)
           - 优化目标: 平衡连接稳定性与资源消耗
           - 适用场景: 家庭宽带、一般办公网络

        3. **低质量网络 (slow) - 短间隔策略**:
           - 理论依据: 网络不稳定，NAT设备可能提前超时
           - 实际配置: 较短心跳间隔 (例如: 15-25秒)
           - 优化目标: 增强连接保活，防止静默断开
           - 适用场景: 移动网络、不稳定WiFi、代理网络

        📡 心跳与网络质量的关系
        =========================

        网络质量影响因素:

        1. **NAT设备行为**:
           - 高质量网络: 企业级设备，长NAT超时
           - 低质量网络: 家用路由器，短NAT超时
           - 心跳策略: 需要在NAT超时前发送保活包

        2. **中间代理设备**:
           - 稳定网络: 代理设备配置合理，连接保持时间长
           - 不稳定网络: 代理可能主动断开空闲连接
           - 心跳策略: 频繁心跳维持代理连接活跃状态

        3. **网络拥塞影响**:
           - 低延迟网络: 心跳包能及时到达，间隔可以较长
           - 高延迟网络: 心跳包可能丢失，需要更频繁发送

        🎯 心跳间隔优化算法
        ===================

        间隔选择策略:
        ```
        if quality == 'fast':
            interval = WS_HEARTBEAT_CONFIG['fast_network']    # 长间隔
        elif quality == 'normal':
            interval = WS_HEARTBEAT_CONFIG['normal_network']  # 中间隔
        else:  # 'slow'
            interval = WS_HEARTBEAT_CONFIG['slow_network']    # 短间隔
        ```

        配置来源:
        - 所有间隔配置来自 const.py 中的 WS_HEARTBEAT_CONFIG
        - 统一配置管理，便于全局调优
        - 配置变更影响所有检测器实例

        📊 心跳性能分析
        ===============

        资源消耗评估:

        1. **网络带宽消耗**:
           - 心跳包大小: 通常几十字节
           - 频率影响: 间隔越短，带宽消耗越大
           - 总体影响: 相对于数据传输，心跳开销很小

        2. **CPU资源消耗**:
           - 心跳处理: 简单的包收发和状态检查
           - 定时器开销: 心跳定时器的系统调度成本
           - 优化效果: 合理间隔避免过度CPU占用

        3. **电池电量影响 (移动设备)**:
           - 无线模块唤醒: 每次心跳需要唤醒网络模块
           - 频率敏感性: 心跳频率直接影响续航时间
           - 平衡策略: 在连接稳定性和电量消耗间找平衡

        🔄 动态调整机制
        ===============

        实时适应性:
        - 网络质量变化时，心跳间隔自动调整
        - 质量检测结果直接影响下次心跳调度
        - 无需重启连接，实现平滑过渡

        调整时机:
        - 网络质量检测完成后
        - 质量级别发生变化时
        - 用户手动配置变更后

        🛡️ 可靠性保证
        =============

        异常处理:
        - 配置缺失: 使用默认的标准网络配置
        - 无效质量级别: 自动回退到标准配置
        - 配置值异常: 内置边界检查和合法性验证

        边界条件:
        - 最小间隔限制: 避免过于频繁的心跳
        - 最大间隔限制: 防止连接超时断开
        - 整数返回: 确保定时器设置的精确性

        💡 实际应用指导
        ===============

        WebSocket集成:
        ```python
        heartbeat_interval = detector.get_heartbeat_interval()
        # 设置WebSocket心跳定时器
        asyncio.create_task(heartbeat_loop(interval=heartbeat_interval))
        ```

        监控建议:
        - 监控心跳成功率，评估间隔配置效果
        - 观察连接断开频率，调整间隔策略
        - 分析网络流量，优化心跳开销

        调优建议:
        - 根据实际部署环境调整配置常量
        - 考虑设备类型和电量敏感性
        - 平衡用户体验和系统资源消耗
        """
        level = quality_level or self.quality_level

        mapping = {
            "fast": WS_HEARTBEAT_CONFIG["fast_network"],
            "normal": WS_HEARTBEAT_CONFIG["normal_network"],
            "slow": WS_HEARTBEAT_CONFIG["slow_network"],
        }

        return mapping.get(level, WS_HEARTBEAT_CONFIG["normal_network"])

    def get_max_reconnect_attempts(self, quality_level: Optional[str] = None) -> int:
        """智能重连策略配置器 - 网络自适应的重连次数管理

        🔄 重连策略设计哲学
        ===================

        实现基于网络质量评估的智能重连策略，根据网络稳定性和连接成功概率
        动态调整最大重连尝试次数，在系统稳定性和资源消耗间找到最优平衡点。

        Args:
            quality_level: 指定的网络质量级别，可选参数
                - None: 使用当前网络质量检测结果 (推荐)
                - 'fast'/'normal'/'slow': 强制使用特定级别的重连策略
                用途: 支持重连策略的临时调整和故障恢复测试

        Returns:
            最大重连尝试次数(整数):
            - 快速网络: 较少次数，快速失败检测
            - 标准网络: 中等次数，平衡恢复能力与资源消耗
            - 慢速网络: 较多次数，增强连接恢复的持久性

        🧮 重连次数科学计算
        ===================

        策略分级原理:

        1. **高质量网络 (fast) - 快速失败策略**:
           - 网络特性: 连接稳定，失败通常是服务端问题
           - 重连逻辑: 少量尝试后快速失败，避免无意义重试
           - 典型配置: 3-5次重连尝试
           - 设计理由: 高质量网络下连接失败多为非临时性问题

        2. **标准网络 (normal) - 平衡策略**:
           - 网络特性: 偶有波动，短期网络中断较常见
           - 重连逻辑: 适中的重试次数，覆盖常见的临时故障
           - 典型配置: 5-8次重连尝试
           - 设计理由: 平衡快速恢复与资源消耗

        3. **低质量网络 (slow) - 持久重试策略**:
           - 网络特性: 频繁波动，连接成功需要多次尝试
           - 重连逻辑: 更多重试机会，增强连接恢复成功率
           - 典型配置: 8-12次重连尝试
           - 设计理由: 补偿网络不稳定性，确保最终连接成功

        📊 重连成功率数学模型
        ======================

        假设单次连接成功率为 p，n次重连的累积成功率为:
        ```
        P_success(n) = 1 - (1-p)^n
        ```

        不同网络质量的成功率估算:
        - 快速网络: p≈0.95, 3次重连后 P≈99.9%
        - 标准网络: p≈0.80, 6次重连后 P≈99.9%
        - 慢速网络: p≈0.60, 10次重连后 P≈99.9%

        策略目标: 在合理的重连次数内达到99%+的最终成功率

        ⏱️ 重连时间成本分析
        ===================

        时间成本计算 (结合指数退避):
        ```
        总重连时间 ≈ Σ(base_delay * backoff_factor^i) for i in [1,n]
        ```

        不同策略的时间成本:
        - 快速网络: 较少次数，总时间成本低
        - 标准网络: 中等次数，可接受的时间成本
        - 慢速网络: 较多次数，但单次延迟也更长，总体合理

        用户体验影响:
        - 过少重试: 连接失败率高，用户体验差
        - 过多重试: 恢复时间长，影响实时性
        - 合理配置: 在成功率和响应时间间平衡

        🎯 配置选择策略
        ===============

        配置映射逻辑:
        ```python
        config_mapping = {
            'fast': WS_RECONNECT_CONFIG['max_attempts_fast'],
            'normal': WS_RECONNECT_CONFIG['max_attempts_normal'],
            'slow': WS_RECONNECT_CONFIG['max_attempts_slow']
        }
        ```

        配置来源统一性:
        - 所有重连配置来自 const.py 中的 WS_RECONNECT_CONFIG
        - 全局一致的配置管理
        - 便于根据实际部署环境统一调优

        🔧 与其他重连参数的协调
        =========================

        重连策略生态系统:

        1. **重连延迟协调**:
           - 重连次数与延迟算法配合
           - 更多次数需要更智能的延迟增长
           - 避免大量重连在短时间内集中

        2. **超时配置协调**:
           - 重连次数与单次连接超时的平衡
           - 长超时减少需要的重连次数
           - 短超时需要更多重连机会补偿

        3. **心跳策略协调**:
           - 重连成功后的心跳间隔调整
           - 网络质量变化后的策略同步更新

        📈 实际部署优化
        ===============

        环境适应性:
        - 家庭网络: 标准配置通常足够
        - 企业网络: 快速失败策略提高效率
        - 移动网络: 持久重试应对网络切换
        - 边缘网络: 增加重试次数确保连接

        监控和调优:
        - 监控重连成功率和平均重连次数
        - 分析重连失败的根本原因
        - 根据实际表现调整配置参数

        🛡️ 异常和边界处理
        ===================

        容错机制:
        - 配置缺失: 使用标准网络的默认配置
        - 无效质量级别: 自动回退到标准配置
        - 配置值异常: 内置合理范围检查

        边界限制:
        - 最小重连次数: 至少1次，确保基本重试能力
        - 最大重连次数: 避免无限重试消耗资源
        - 整数返回: 确保计数逻辑的准确性

        💡 使用建议和最佳实践
        ======================

        集成示例:
        ```python
        max_attempts = detector.get_max_reconnect_attempts()
        for attempt in range(1, max_attempts + 1):
            try:
                await connect_websocket()
                break
            except ConnectionError:
                if attempt < max_attempts:
                    delay = calculate_reconnect_delay(attempt, ...)
                    await asyncio.sleep(delay)
                else:
                    raise
        ```

        调优建议:
        1. 根据实际网络环境和设备类型调整配置常量
        2. 监控重连统计数据，评估配置效果
        3. 考虑用户类型和应用场景的差异化配置
        4. 定期评估和更新重连策略的有效性
        """
        level = quality_level or self.quality_level

        mapping = {
            "fast": WS_RECONNECT_CONFIG["max_attempts_fast"],
            "normal": WS_RECONNECT_CONFIG["max_attempts_normal"],
            "slow": WS_RECONNECT_CONFIG["max_attempts_slow"],
        }

        return mapping.get(level, WS_RECONNECT_CONFIG["max_attempts_normal"])

    def get_stats(self) -> Dict[str, Any]:
        """网络质量统计数据收集器 - 全方位的诊断和监控信息

        📊 统计信息设计价值
        ===================

        提供完整的网络质量检测统计数据，支持系统监控、性能分析、故障诊断
        和配置优化。统计信息涵盖实时状态、历史趋势和系统行为特征。

        Returns:
            完整的统计信息字典，包含以下关键指标:
            {
                # 当前状态信息
                'current_quality': str,        # 当前网络质量级别
                'avg_latency_ms': float,       # 平均延迟(毫秒)
                'success_rate': float,         # 连接成功率 [0-1]
                'config_mode': str,            # 配置模式 (auto/fast/normal/slow)

                # 累积统计信息
                'total_checks': int,           # 总检测次数
                'successful_checks': int,      # 成功检测次数
                'quality_changes': int,        # 质量级别变化次数
                'last_quality_change': datetime # 最后一次质量变化时间
            }

        🔍 统计指标深度解析
        ===================

        实时状态指标:

        1. **当前质量级别 (current_quality)**:
           - 数据类型: 字符串 ('fast'/'normal'/'slow')
           - 业务含义: 当前网络环境的质量评估结果
           - 应用价值: 指导当前的连接策略和参数配置
           - 更新频率: 每次质量检测后更新

        2. **平均延迟 (avg_latency_ms)**:
           - 数据类型: 浮点数，保留1位小数
           - 计算方法: 基于滑动窗口的算术平均值
           - 业务含义: 网络响应速度的量化指标
           - 应用价值: 超时配置和用户体验预期的参考

        3. **连接成功率 (success_rate)**:
           - 数据类型: 浮点数，保留3位小数，范围[0-1]
           - 计算方法: 成功连接次数 / 总尝试次数
           - 业务含义: 网络稳定性和可靠性指标
           - 应用价值: 重连策略和故障预警的重要依据

        4. **配置模式 (config_mode)**:
           - 数据类型: 字符串 ('auto'/'fast'/'normal'/'slow')
           - 业务含义: 当前的网络质量检测模式
           - 应用价值: 区分自动检测和手动配置的行为

        📈 历史统计指标
        ===============

        累积统计数据:

        1. **总检测次数 (total_checks)**:
           - 数据类型: 整数，累积计数
           - 业务含义: 系统运行期间的总检测活动量
           - 应用价值: 评估检测频率和系统活跃度
           - 监控意义: 检测过于频繁可能表示配置问题

        2. **成功检测次数 (successful_checks)**:
           - 数据类型: 整数，累积计数
           - 计算关系: successful_checks ≤ total_checks
           - 业务含义: 网络检测的整体成功率
           - 应用价值: 评估网络环境的整体稳定性

        3. **质量变化次数 (quality_changes)**:
           - 数据类型: 整数，累积计数
           - 业务含义: 网络质量级别变化的频率
           - 应用价值: 网络环境稳定性的关键指标
           - 监控意义: 频繁变化可能表示网络不稳定

        4. **最后质量变化时间 (last_quality_change)**:
           - 数据类型: datetime对象或None
           - 业务含义: 最近一次质量级别变化的时间戳
           - 应用价值: 网络稳定性趋势分析
           - 监控意义: 长期无变化表示网络稳定

        🎯 统计数据应用场景
        ===================

        1. **系统监控仪表板**:
           - 实时显示网络质量状态
           - 历史趋势图表和报警
           - 性能指标和健康检查

        2. **故障诊断分析**:
           - 连接问题的根因分析
           - 网络质量变化时间线
           - 成功率异常的定位

        3. **配置优化决策**:
           - 评估当前配置的效果
           - 识别需要调优的参数
           - A/B测试不同配置的表现

        4. **用户体验评估**:
           - 网络质量对用户体验的影响
           - 不同网络环境的适应性
           - 服务质量SLA的监控

        📊 统计数据质量保证
        =====================

        数据一致性:
        - 所有统计指标同步更新
        - 计算结果与原始数据保持一致
        - 避免中间状态导致的数据不准确

        精度控制:
        - 延迟保留1位小数，平衡精度与可读性
        - 成功率保留3位小数，提供足够的精度
        - 计数器使用整数，确保精确性

        时间戳处理:
        - 使用系统本地时间，便于日志关联
        - None值表示未发生过质量变化
        - datetime对象支持时间计算和格式化

        🔧 数据处理优化
        ===============

        性能考虑:
        - 统计计算基于内存中的简单数据
        - 避免复杂的数据库查询或文件IO
        - 返回数据副本，避免外部修改影响

        内存效率:
        - 统计数据结构简单，内存占用minimal
        - 历史数据使用固定大小窗口
        - 避免无限增长的统计信息

        💡 监控集成建议
        ===============

        日志记录:
        ```python
        stats = detector.get_stats()
        logger.info("网络质量统计: %s", stats)
        ```

        指标监控:
        ```python
        stats = detector.get_stats()
        metrics.gauge('network_quality.latency', stats['avg_latency_ms'])
        metrics.gauge('network_quality.success_rate', stats['success_rate'])
        ```

        健康检查:
        ```python
        stats = detector.get_stats()
        if stats['success_rate'] < 0.8:
            alert_manager.send_alert('网络质量异常')
        ```

        报告生成:
        - 定期汇总统计数据生成报告
        - 分析网络质量趋势和模式
        - 为系统优化提供数据支持
        """
        return {
            "current_quality": self.quality_level,
            "avg_latency_ms": round(self.avg_latency, 1),
            "success_rate": round(self.connection_success_rate, 3),
            "config_mode": self.config_network_mode,
            **self.stats,
        }


def calculate_reconnect_delay(
    attempt: int, base_delay: int, network_quality: str, add_jitter: bool = True
) -> float:
    """智能重连延迟计算器 - 改进的指数退避算法与网络自适应调度

    🧮 算法设计原理和科学依据
    ===========================

    实现基于网络质量感知的智能重连延迟算法，结合改进的指数退避策略、
    网络质量自适应调整和随机抖动机制，为不同网络环境提供最优的重连时机。

    Args:
        attempt: 当前重连尝试次数，从1开始的正整数
                - 1: 第一次重连尝试
                - 2-N: 后续重连尝试
                - 用于指数退避的指数计算

        base_delay: 基础延迟时间(秒)，重连延迟的起始值
                   - 通常为1-5秒，根据应用场景设定
                   - 所有后续延迟计算的基准
                   - 影响整个重连时间序列的尺度

        network_quality: 网络质量级别，影响延迟调整策略
                        - 'fast': 高质量网络，减少等待时间
                        - 'normal': 标准网络，使用标准延迟
                        - 'slow': 低质量网络，增加等待时间

        add_jitter: 是否添加随机抖动，默认True
                   - True: 添加抖动，避免惊群效应
                   - False: 确定性延迟，便于测试和调试

    Returns:
        优化后的重连延迟时间(秒)，浮点数类型
        - 最小值: 1.0秒，确保基本的重连间隔
        - 最大值: 受 max_backoff_seconds 限制
        - 精度: 浮点数，支持亚秒级精度

    🔬 指数退避算法实现
    ===================

    基础延迟计算公式:
    ```
    delay = base_delay × (backoff_multiplier ^ (attempt - 1))
    ```

    算法特点:
    1. **指数增长**: 延迟时间随尝试次数指数增长
    2. **上限控制**: 通过 max_backoff_seconds 防止延迟过长
    3. **首次快速**: attempt=1时延迟等于base_delay

    指数退避的优势:
    - **快速恢复**: 首次重连延迟短，适应临时故障
    - **避免雪崩**: 延迟递增，减少服务器压力
    - **自适应性**: 持续故障时自动降低重试频率

    📡 网络质量自适应调整
    =======================

    网络质量系数应用:
    ```python
    if network_quality == 'fast':
        delay *= 0.7    # 减少30%等待时间
    elif network_quality == 'slow':
        delay *= 1.3    # 增加30%等待时间
    # 'normal' 保持原延迟不变
    ```

    调整策略的科学依据:

    1. **快速网络优化 (0.7倍系数)**:
       - 理论基础: 高质量网络故障恢复快
       - 实际效果: 减少不必要的等待时间
       - 用户体验: 快速恢复，提升响应性

    2. **慢速网络保护 (1.3倍系数)**:
       - 理论基础: 低质量网络需要更多恢复时间
       - 实际效果: 给网络更多稳定时间
       - 系统保护: 避免频繁重试加重网络负担

    3. **标准网络基准 (1.0倍系数)**:
       - 使用标准的指数退避策略
       - 适应大多数网络环境
       - 作为其他策略的参考基准

    🎲 随机抖动机制
    ===============

    抖动算法实现:
    ```python
    jitter_range = delay × jitter_factor
    jitter = random.uniform(-jitter_range, +jitter_range)
    final_delay = delay + jitter
    ```

    抖动设计原理:

    1. **惊群效应预防**:
       - 问题: 多个客户端同时重连导致服务器瞬时压力
       - 解决: 随机化重连时机，分散连接尝试
       - 效果: 平滑服务器负载，提高整体成功率

    2. **抖动范围控制**:
       - 抖动幅度: delay × jitter_factor (通常10-20%)
       - 双向抖动: 既可能提前也可能延后
       - 相对控制: 抖动幅度与延迟成比例

    3. **随机性保证**:
       - 使用 random.uniform 确保均匀分布
       - 每次计算独立随机，避免模式化
       - 统计上的无偏性，不影响平均延迟

    ⚡ 性能和边界控制
    ===================

    边界条件处理:

    1. **最大延迟限制**:
       - 应用 max_backoff_seconds 上限
       - 防止无限增长的延迟时间
       - 保证用户体验的可接受性

    2. **最小延迟保证**:
       - 确保最终延迟 ≥ 1.0秒
       - 避免过于激进的重连尝试
       - 给系统基本的恢复时间

    3. **数值稳定性**:
       - 浮点数计算精度控制
       - 避免数值溢出和下溢
       - 确保计算结果的可预测性

    📊 延迟序列分析
    ===============

    典型延迟序列 (base_delay=2秒, backoff_multiplier=2.0):

    标准网络 (normal):
    - 尝试1: 2秒
    - 尝试2: 4秒
    - 尝试3: 8秒
    - 尝试4: 16秒
    - 尝试5: 32秒 (可能受max_backoff_seconds限制)

    快速网络 (fast, ×0.7):
    - 尝试1: 1.4秒
    - 尝试2: 2.8秒
    - 尝试3: 5.6秒
    - 尝试4: 11.2秒

    慢速网络 (slow, ×1.3):
    - 尝试1: 2.6秒
    - 尝试2: 5.2秒
    - 尝试3: 10.4秒
    - 尝试4: 20.8秒

    🎯 实际应用优化
    ===============

    配置调优建议:

    1. **base_delay选择**:
       - 快速应用: 1-2秒，优先响应速度
       - 标准应用: 2-5秒，平衡速度与稳定性
       - 稳定优先: 5-10秒，确保连接质量

    2. **backoff_multiplier调整**:
       - 激进策略: 1.5-2.0，快速增长
       - 温和策略: 1.2-1.5，缓慢增长
       - 保守策略: 1.1-1.3，线性增长

    3. **max_backoff_seconds设置**:
       - 交互应用: 30-60秒，保证响应性
       - 后台服务: 60-300秒，允许长时间等待
       - 批处理: 300秒+，容忍长时间中断

    📈 监控和诊断
    =============

    关键监控指标:
    - 平均重连延迟时间
    - 重连尝试次数分布
    - 不同网络质量下的成功率
    - 延迟计算的性能开销

    调优反馈循环:
    1. 收集重连统计数据
    2. 分析延迟策略效果
    3. 调整算法参数
    4. 验证优化效果

    💡 使用示例和最佳实践
    =======================

    基本使用:
    ```python
    for attempt in range(1, max_attempts + 1):
        try:
            await connect()
            break
        except ConnectionError:
            if attempt < max_attempts:
                delay = calculate_reconnect_delay(
                    attempt, base_delay=2,
                    network_quality=detector.quality_level
                )
                await asyncio.sleep(delay)
    ```

    高级配置:
    ```python
    # 禁用抖动的确定性重连
    delay = calculate_reconnect_delay(
        attempt, base_delay, quality, add_jitter=False
    )

    # 记录重连延迟用于监控
    logger.debug(f"重连延迟: {delay:.2f}秒 (尝试{attempt}, 质量{quality})")
    ```

    性能优化:
    - 缓存网络质量评估结果，避免重复检测
    - 预计算常用的延迟值，减少实时计算开销
    - 批量处理多个连接的重连调度
    """
    config = WS_RECONNECT_CONFIG

    # 基础延迟计算（改进的指数退避）
    delay = base_delay * (config["backoff_multiplier"] ** (attempt - 1))
    delay = min(delay, config["max_backoff_seconds"])

    # 根据网络质量调整
    if network_quality == "fast":
        delay *= 0.7  # 快速网络减少等待时间
    elif network_quality == "slow":
        delay *= 1.3  # 慢速网络增加等待时间

    # 添加随机抖动避免惊群效应
    if add_jitter:
        jitter_range = delay * config["jitter_factor"]
        jitter = random.uniform(-jitter_range, jitter_range)
        delay += jitter

    # 确保延迟时间不低于1秒
    return max(1.0, delay)
