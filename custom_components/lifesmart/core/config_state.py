"""配置流程状态管理器。

提供统一的配置状态管理，解决配置数据更新顺序混乱问题。

技术特性:
- 明确的配置数据合并优先级
- 统一的用户输入安全性检查
- 配置流程各阶段的状态跟踪
- 统一的配置错误处理机制

创建者: @MapleEve
架构: 配置状态管理器模式
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from dataclasses import dataclass, field

import voluptuous as vol

from .const import (
    CONF_LIFESMART_APPKEY,
    CONF_LIFESMART_APPTOKEN,
    CONF_LIFESMART_USERID,
    CONF_LIFESMART_USERTOKEN,
    CONF_LIFESMART_USERPASSWORD,
    CONF_LIFESMART_AUTH_METHOD,
    LIFESMART_REGION_OPTIONS,
)

from homeassistant.const import CONF_REGION

_LOGGER = logging.getLogger(__name__)


@dataclass
class ConfigFlowState:
    """配置流程状态管理器。

    管理配置流程中的状态数据，提供清晰的合并和验证逻辑。
    """

    # 基础配置数据
    config_data: Dict[str, Any] = field(default_factory=dict)

    # 重认证相关
    reauth_entry: Optional[Any] = None

    # 临时数据存储
    temp_data: Dict[str, Any] = field(default_factory=dict)

    def merge_config(
        self, base_config: Dict[str, Any], user_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """按优先级合并配置数据。

        合并优先级: 默认值 < base_config < 现有config_data < 用户输入

        Args:
            base_config: 基础配置（通常来自重认证条目）
            user_input: 用户输入数据

        Returns:
            合并后的配置数据
        """
        # 创建新的配置数据字典，按优先级合并
        merged_config = {}

        # 1. 基础配置（重认证数据）
        if base_config:
            merged_config.update(base_config)

        # 2. 现有配置数据
        if self.config_data:
            merged_config.update(self.config_data)

        # 3. 用户输入（最高优先级）
        if user_input:
            validated_input = self.validate_input(user_input)
            merged_config.update(validated_input)

        return merged_config

    def update_config(
        self,
        base_config: Optional[Dict[str, Any]] = None,
        user_input: Optional[Dict[str, Any]] = None,
    ) -> None:
        """更新配置状态。

        Args:
            base_config: 基础配置数据
            user_input: 用户输入数据
        """
        self.config_data = self.merge_config(base_config or {}, user_input or {})

    def validate_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """统一用户输入验证。

        Args:
            data: 用户输入数据

        Returns:
            验证后的数据

        Raises:
            vol.Invalid: 验证失败时使用多语言错误键
        """
        validated_data = data.copy()

        # 必填字段检查
        required_fields = [
            CONF_LIFESMART_APPKEY,
            CONF_LIFESMART_APPTOKEN,
            CONF_LIFESMART_USERID,
        ]
        for field_name in required_fields:
            if field_name in data and (
                not data.get(field_name) or not isinstance(data[field_name], str)
            ):
                raise vol.Invalid("invalid_auth")  # 使用多语言错误键

        # 验证区域设置 - 使用项目正确的常量
        region = data.get(CONF_REGION)
        if region and region not in LIFESMART_REGION_OPTIONS:
            raise vol.Invalid("invalid_region")  # 需要添加到translations

        # 验证认证方法
        auth_method = data.get(CONF_LIFESMART_AUTH_METHOD)
        if auth_method and auth_method not in ["token", "password"]:
            raise vol.Invalid("invalid_auth_method")  # 需要添加到translations

        return validated_data

    def get_default_values(self, step: str) -> Dict[str, Any]:
        """获取表单默认值。

        Args:
            step: 配置步骤名称

        Returns:
            默认值字典
        """
        defaults = {}

        if step == "cloud":
            defaults.update(
                {
                    CONF_LIFESMART_APPKEY: self.config_data.get(
                        CONF_LIFESMART_APPKEY, ""
                    ),
                    CONF_LIFESMART_APPTOKEN: self.config_data.get(
                        CONF_LIFESMART_APPTOKEN, ""
                    ),
                    CONF_LIFESMART_USERID: self.config_data.get(
                        CONF_LIFESMART_USERID, ""
                    ),
                    CONF_REGION: self.config_data.get(CONF_REGION, "cn2"),
                    CONF_LIFESMART_AUTH_METHOD: self.config_data.get(
                        CONF_LIFESMART_AUTH_METHOD, "token"
                    ),
                }
            )
        elif step == "cloud_token":
            defaults.update(
                {
                    CONF_LIFESMART_USERTOKEN: self.config_data.get(
                        CONF_LIFESMART_USERTOKEN, ""
                    ),
                }
            )

        return defaults

    def reset_state(self) -> None:
        """重置状态管理器。"""
        self.config_data.clear()
        self.temp_data.clear()
        self.reauth_entry = None

    def is_reauth_flow(self) -> bool:
        """检查是否为重认证流程。"""
        return self.reauth_entry is not None

    def set_reauth_entry(self, entry: Any) -> None:
        """设置重认证条目。

        Args:
            entry: 配置条目对象
        """
        self.reauth_entry = entry
        if entry and hasattr(entry, "data"):
            self.config_data = entry.data.copy()


class ConfigFlowStateManager:
    """配置流程状态管理器的静态工厂类。"""

    @staticmethod
    def create_state() -> ConfigFlowState:
        """创建新的配置状态实例。"""
        return ConfigFlowState()

    @staticmethod
    def create_reauth_state(entry: Any) -> ConfigFlowState:
        """创建重认证配置状态实例。

        Args:
            entry: 重认证的配置条目

        Returns:
            配置状态实例
        """
        state = ConfigFlowState()
        state.set_reauth_entry(entry)
        return state
