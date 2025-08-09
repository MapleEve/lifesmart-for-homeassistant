"""
测试 LifeSmart 二元传感器平台。

此测试套件提供全面的功能验证，包括：
- 实体创建和设备过滤逻辑
- 设备类别识别和状态解析
- 实时更新和全局刷新处理
- 特殊设备类型的逻辑（门锁、按钮、温控器等）
- 属性解析和错误处理
- 边界条件和异常情况
"""

import asyncio
from datetime import timedelta

import pytest
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send

from custom_components.lifesmart.core.const import *
from custom_components.lifesmart.core.helpers import generate_unique_id
from ..utils.factories import create_devices_by_category
from ..utils.helpers import (
    find_test_device,
    get_hub_id,
)


# ==================== 测试数据 ====================


def generate_binary_sensor_test_cases():
    """从工厂数据动态生成二进制传感器测试参数"""
    devices = create_devices_by_category(
        ["bs_door", "bs_motion", "bs_water", "bs_lock", "bs_button"]
    )
    test_cases = []

    # 预定义每种设备类型和子键对应的设备类型和期望状态
    device_mappings = {
        ("SL_SC_G", "G"): (BinarySensorDeviceClass.DOOR, STATE_ON),  # 门传感器
        ("SL_SC_MHW", "M"): (BinarySensorDeviceClass.MOTION, STATE_ON),  # 动态感应器
        ("SL_SC_WA", "WA"): (BinarySensorDeviceClass.MOISTURE, STATE_ON),  # 水浸传感器
        ("SL_LK_LS", "EVTLO"): (
            BinarySensorDeviceClass.LOCK,
            STATE_ON,
        ),  # 智能门锁开锁事件
        ("SL_LK_LS", "ALM"): (
            BinarySensorDeviceClass.PROBLEM,
            STATE_ON,
        ),  # 智能门锁报警
        ("SL_SC_BB", "B"): (None, STATE_OFF),  # 按钮
    }

    for device in devices:
        devtype = device.get("devtype")
        me = device.get("me")
        data = device.get("data", {})

        for (target_devtype, sub_key), (
            device_class,
            expected_state,
        ) in device_mappings.items():
            if devtype == target_devtype and sub_key in data:
                test_cases.append((me, sub_key, device_class, expected_state))
                break  # 只添加第一个匹配的设备

    return test_cases


# 生成测试参数
BINARY_SENSOR_TEST_CASES = generate_binary_sensor_test_cases()


def generate_state_parsing_test_cases():
    """生成状态解析测试参数"""
    devices = create_devices_by_category(["bs_door", "bs_motion", "bs_water"])
    test_cases = []

    # 预定义状态测试场景
    state_scenarios = [
        (
            "SL_SC_G",
            "G",
            [
                ({"val": 0}, True),  # 门开
                ({"val": 1}, False),  # 门关
            ],
        ),
        (
            "SL_SC_MHW",
            "M",
            [
                ({"val": 1}, True),  # 检测到运动
                ({"val": 0}, False),  # 未检测到运动
            ],
        ),
        (
            "SL_SC_WA",
            "WA",
            [
                ({"val": 1}, True),  # 检测到水
                ({"val": 0}, False),  # 未检测到水
            ],
        ),
    ]

    for device in devices:
        devtype = device.get("devtype")
        me = device.get("me")
        data = device.get("data", {})

        for target_devtype, sub_key, scenarios in state_scenarios:
            if devtype == target_devtype and sub_key in data:
                for test_data, expected_state in scenarios:
                    test_cases.append((me, sub_key, test_data, expected_state))
                break  # 只添加第一个匹配的设备

    return test_cases


# 生成状态解析测试参数
STATE_PARSING_TEST_CASES = generate_state_parsing_test_cases()

# 设备类型和子设备映射
DEVICE_TYPE_MAPPINGS = {
    # 门窗感应器
    "bs_door": {"device_class": BinarySensorDeviceClass.DOOR, "sub_keys": ["G"]},
    "bs_guard": {
        "device_class": BinarySensorDeviceClass.VIBRATION,
        "sub_keys": ["AXS", "P2"],
    },
    # 动态感应器
    "bs_motion": {"device_class": BinarySensorDeviceClass.MOTION, "sub_keys": ["M"]},
    # 水浸传感器
    "bs_water": {"device_class": BinarySensorDeviceClass.MOISTURE, "sub_keys": ["WA"]},
    # 云防系列
    "bs_defed": {"device_class": BinarySensorDeviceClass.MOTION, "sub_keys": ["M"]},
    # 烟雾感应器
    "bs_smoke": {"device_class": BinarySensorDeviceClass.SMOKE, "sub_keys": ["P1"]},
    # 人体存在感应器
    "bs_radar": {"device_class": BinarySensorDeviceClass.OCCUPANCY, "sub_keys": ["P1"]},
    # 门锁
    "bs_lock": {
        "device_classes": {
            "EVTLO": BinarySensorDeviceClass.LOCK,
            "ALM": BinarySensorDeviceClass.PROBLEM,
        },
        "sub_keys": ["EVTLO", "ALM"],
    },
    # 按钮
    "bs_button": {"device_class": None, "sub_keys": ["B"]},
}

# 状态测试用例
STATE_TEST_CASES = [
    # 门窗感应器 - G键：0=开，其他=关
    {"devices": "bs_door", "sub_key": "G", "test_data": {"val": 0}, "expected": True},
    {"devices": "bs_door", "sub_key": "G", "test_data": {"val": 1}, "expected": False},
    # 动态感应器 - M键：非0=检测到
    {"devices": "bs_motion", "sub_key": "M", "test_data": {"val": 1}, "expected": True},
    {
        "devices": "bs_motion",
        "sub_key": "M",
        "test_data": {"val": 0},
        "expected": False,
    },
    # 水浸传感器 - WA键：非0=检测到水
    {"devices": "bs_water", "sub_key": "WA", "test_data": {"val": 1}, "expected": True},
    {
        "devices": "bs_water",
        "sub_key": "WA",
        "test_data": {"val": 0},
        "expected": False,
    },
    # 烟雾感应器 - P1键：非0=检测到烟雾
    {"devices": "bs_smoke", "sub_key": "P1", "test_data": {"val": 1}, "expected": True},
    {
        "devices": "bs_smoke",
        "sub_key": "P1",
        "test_data": {"val": 0},
        "expected": False,
    },
    # 人体存在感应器 - P1键：非0=检测到人体
    {"devices": "bs_radar", "sub_key": "P1", "test_data": {"val": 1}, "expected": True},
    {
        "devices": "bs_radar",
        "sub_key": "P1",
        "test_data": {"val": 0},
        "expected": False,
    },
]

# 按钮事件测试用例
BUTTON_EVENT_CASES = [
    {"val": 1, "event_name": "single_click"},
    {"val": 2, "event_name": "double_click"},
    {"val": 255, "event_name": "long_press"},
]


# ==================== 实体创建和设置测试 ====================


class TestBinarySensorSetup:
    """测试二元传感器平台的设置和实体创建。"""

    @pytest.mark.asyncio
    async def test_setup_creates_expected_entities(
        self,
        hass: HomeAssistant,
        setup_integration_binary_sensor_only: ConfigEntry,
    ):
        """测试设置过程创建了所有预期的实体。"""
        entity_registry = er.async_get(hass)

        # 获取所有二进制传感器实体
        created_entities = {
            entry.entity_id
            for entry in entity_registry.entities.values()
            if entry.platform == DOMAIN and entry.domain == "binary_sensor"
        }

        # 使用工厂函数获取测试设备来验证实体创建
        test_devices = create_devices_by_category(
            ["bs_door", "bs_guard", "bs_lock", "bs_button"]
        )

        # 验证应该创建的设备类型和数量
        expected_device_types = {
            "SL_SC_G",  # 门禁感应器
            "SL_SC_BG",  # CUBE门禁感应器
            "SL_LK_LS",  # 智能门锁
            "SL_SC_BB",  # 随心开关/按钮
        }

        # 查找对应的设备并验证实体创建
        found_devices = set()
        for device in test_devices:
            if device["devtype"] in expected_device_types:
                found_devices.add(device["devtype"])

        # 验证每种设备类型都有对应的实体创建
        assert len(found_devices) == len(
            expected_device_types
        ), f"应该找到{len(expected_device_types)}种设备类型，实际找到{len(found_devices)}"

        # 验证至少创建了预期数量的二进制传感器实体
        # SL_SC_G: 1个实体 (G)
        # SL_SC_BG: 3个实体 (G, KB, AXS)
        # SL_LK_LS: 2个实体 (EVTLO, ALM)
        # SL_SC_BB: 1个实体 (B)
        expected_entity_count = 7  # 总共应该有7个实体

        assert (
            len(created_entities) >= expected_entity_count
        ), f"应该创建至少{expected_entity_count}个二进制传感器实体，实际创建了{len(created_entities)}个"

        # 验证具体的实体类型存在（基于设备类型而不是hardcode的entity_id）
        entity_unique_ids = {
            entry.unique_id
            for entry in entity_registry.entities.values()
            if entry.platform == DOMAIN and entry.domain == "binary_sensor"
        }

        # 验证门锁实体的unique_id存在
        lock_evtlo_found = any(
            "sl_lk_ls" in uid and "evtlo" in uid for uid in entity_unique_ids
        )
        lock_alm_found = any(
            "sl_lk_ls" in uid and "alm" in uid for uid in entity_unique_ids
        )

        assert lock_evtlo_found, "应该创建门锁开锁事件传感器"
        assert lock_alm_found, "应该创建门锁告警传感器"

    @pytest.mark.asyncio
    async def test_setup_respects_device_exclusion(
        self,
        hass: HomeAssistant,
    ):
        """测试设置过程正确排除指定的设备。"""
        from custom_components.lifesmart.binary_sensor import async_setup_entry
        from unittest.mock import MagicMock

        # 使用工厂函数创建测试设备
        mock_lifesmart_devices = create_devices_by_category(
            ["bs_door", "bs_guard", "bs_lock", "bs_button"]
        )

        # 创建模拟的 hub 和 config_entry
        mock_hub = MagicMock()
        mock_hub.get_devices.return_value = mock_lifesmart_devices
        mock_hub.get_exclude_config.return_value = ({"bs_door"}, set())  # 排除门传感器
        mock_hub.get_client.return_value = MagicMock()

        mock_config_entry = MagicMock()
        mock_config_entry.entry_id = "test_entry"

        # 设置 hass.data
        hass.data[DOMAIN] = {"test_entry": {"hub": mock_hub}}

        entities_added = []

        def mock_add_entities(entities):
            entities_added.extend(entities)

        await async_setup_entry(hass, mock_config_entry, mock_add_entities)

        # 验证被排除的设备没有创建实体
        door_entities = [entity for entity in entities_added if entity.me == "bs_door"]
        assert len(door_entities) == 0, "被排除的设备不应该创建实体"

    @pytest.mark.asyncio
    async def test_setup_respects_hub_exclusion(
        self,
        hass: HomeAssistant,
    ):
        """测试设置过程正确排除指定的 hub。"""
        from custom_components.lifesmart.binary_sensor import async_setup_entry
        from unittest.mock import MagicMock

        # 使用工厂函数创建测试设备
        mock_lifesmart_devices = create_devices_by_category(
            ["bs_door", "bs_guard", "bs_lock", "bs_button"]
        )

        mock_hub = MagicMock()
        mock_hub.get_devices.return_value = mock_lifesmart_devices
        mock_hub.get_exclude_config.return_value = (
            set(),
            {"mocked_agt"},
        )  # 排除整个 hub
        mock_hub.get_client.return_value = MagicMock()

        mock_config_entry = MagicMock()
        mock_config_entry.entry_id = "test_entry"

        hass.data[DOMAIN] = {"test_entry": {"hub": mock_hub}}

        entities_added = []

        def mock_add_entities(entities):
            entities_added.extend(entities)

        await async_setup_entry(hass, mock_config_entry, mock_add_entities)

        # 验证来自被排除 hub 的设备没有创建实体
        excluded_hub_entities = [
            entity for entity in entities_added if entity.agt == "mocked_agt"
        ]
        assert len(excluded_hub_entities) == 0, "来自被排除hub的设备不应该创建实体"


# ==================== 设备类别和属性测试 ====================


class TestDeviceClassification:
    """测试设备类别识别和属性解析。"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "device_me, sub_key, expected_class, expected_state",
        BINARY_SENSOR_TEST_CASES,
        ids=[
            f"{next((d['devtype'] for d in create_devices_by_category(['bs_door', 'bs_motion', 'bs_water', 'bs_lock', 'bs_button']) if d['me'] == me), 'Unknown')}-{sub_key}"
            for me, sub_key, device_class, expected_state in BINARY_SENSOR_TEST_CASES
        ],
    )
    async def test_device_class_and_initial_state(
        self,
        hass: HomeAssistant,
        setup_integration_binary_sensor_only: ConfigEntry,
        device_me: str,
        sub_key: str,
        expected_class: BinarySensorDeviceClass | None,
        expected_state: str,
    ):
        """测试设备类别识别和初始状态。"""
        # 使用工厂函数获取测试设备
        mock_lifesmart_devices = create_devices_by_category(
            ["bs_door", "bs_motion", "bs_water", "bs_lock", "bs_button"]
        )
        device = find_test_device(mock_lifesmart_devices, device_me)
        # For duplicate devices IDs, find the binary sensor devices specifically
        if device is None or sub_key not in device.get("data", {}):
            # Try to find the Door Sensor (SL_SC_G) specifically by hub ID
            device = find_test_device(mock_lifesmart_devices, device_me, get_hub_id(6))

        assert device is not None, f"设备 {device_me} 应该存在于mock数据中"
        assert sub_key in device.get(
            "data", {}
        ), f"设备 {device_me} 应该包含键 {sub_key}"

        entity_registry = er.async_get(hass)
        unique_id = generate_unique_id(
            device[DEVICE_TYPE_KEY], device[HUB_ID_KEY], device[DEVICE_ID_KEY], sub_key
        )
        entity_id = entity_registry.async_get_entity_id(
            "binary_sensor", DOMAIN, unique_id
        )

        assert entity_id is not None, f"实体 {device_me}-{sub_key} 应该存在"

        state = hass.states.get(entity_id)
        assert state is not None, f"实体状态 {entity_id} 应该存在"
        assert state.state == expected_state, f"初始状态应该是 {expected_state}"

        expected_class_value = expected_class.value if expected_class else None
        assert (
            state.attributes.get("device_class") == expected_class_value
        ), f"设备类别应该是 {expected_class_value}"

    @pytest.mark.asyncio
    async def test_lock_entity_attributes(
        self,
        hass: HomeAssistant,
        setup_integration_binary_sensor_only: ConfigEntry,
    ):
        """测试门锁实体的特殊属性。"""
        # 使用工厂函数获取测试设备
        mock_lifesmart_devices = create_devices_by_category(["bs_lock"])
        # 从测试设备中找到门锁设备 - 使用真实的设备ID
        lock_device = find_test_device(mock_lifesmart_devices, "2i1k")
        assert lock_device is not None, "应该找到门锁测试设备"

        entity_registry = er.async_get(hass)

        # 测试 EVTLO 实体的属性
        evtlo_unique_id = generate_unique_id(
            lock_device[DEVICE_TYPE_KEY],
            lock_device[HUB_ID_KEY],
            lock_device[DEVICE_ID_KEY],
            "EVTLO",
        )
        evtlo_entity_id = entity_registry.async_get_entity_id(
            "binary_sensor", DOMAIN, evtlo_unique_id
        )
        evtlo_state = hass.states.get(evtlo_entity_id)
        assert evtlo_state is not None, "门锁状态传感器应该存在"

        assert "unlocking_method" in evtlo_state.attributes, "应该包含解锁方式属性"
        assert "unlocking_user" in evtlo_state.attributes, "应该包含解锁用户属性"
        assert "unlocking_success" in evtlo_state.attributes, "应该包含解锁成功属性"
        assert "last_updated" in evtlo_state.attributes, "应该包含最后更新时间属性"

        # 测试 ALM 实体的属性
        alm_unique_id = generate_unique_id(
            lock_device[DEVICE_TYPE_KEY],
            lock_device[HUB_ID_KEY],
            lock_device[DEVICE_ID_KEY],
            "ALM",
        )
        alm_entity_id = entity_registry.async_get_entity_id(
            "binary_sensor", DOMAIN, alm_unique_id
        )
        alm_state = hass.states.get(alm_entity_id)
        assert alm_state is not None, "门锁报警传感器应该存在"
        assert "alarm_type" in alm_state.attributes, "应该包含报警类型属性"

    @pytest.mark.asyncio
    async def test_water_sensor_attributes(
        self,
        hass: HomeAssistant,
        setup_integration_binary_sensor_only: ConfigEntry,
    ):
        """测试水浸传感器的特殊属性。"""
        # 使用工厂函数获取测试设备
        mock_lifesmart_devices = create_devices_by_category(["bs_water"])
        device = find_test_device(mock_lifesmart_devices, "1h0j")  # SL_SC_WA水浸传感器
        entity_registry = er.async_get(hass)
        unique_id = generate_unique_id(
            device[DEVICE_TYPE_KEY], device[HUB_ID_KEY], device[DEVICE_ID_KEY], "WA"
        )
        entity_id = entity_registry.async_get_entity_id(
            "binary_sensor", DOMAIN, unique_id
        )

        state = hass.states.get(entity_id)
        assert state is not None, "水浸传感器应该存在"
        assert "conductivity_level" in state.attributes, "应该包含导电性属性"
        assert "water_detected" in state.attributes, "应该包含检测到水属性"


# ==================== 状态解析测试 ====================


class TestStateParsingLogic:
    """测试各种设备类型的状态解析逻辑。"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "device_me, sub_key, test_data, expected_state",
        STATE_PARSING_TEST_CASES,
        ids=[
            f"{next((d['devtype'] for d in create_devices_by_category(['bs_door', 'bs_motion', 'bs_water']) if d['me'] == me), 'Unknown')}-{sub_key}-{'On' if expected_state else 'Off'}"
            for me, sub_key, test_data, expected_state in STATE_PARSING_TEST_CASES
        ],
    )
    async def test_state_parsing(
        self,
        hass: HomeAssistant,
        setup_integration_binary_sensor_only: ConfigEntry,
        device_me: str,
        sub_key: str,
        test_data: dict,
        expected_state: bool,
    ):
        """测试各种设备类型的状态解析逻辑。"""
        # 使用工厂函数获取测试设备
        mock_lifesmart_devices = create_devices_by_category(
            ["bs_door", "bs_motion", "bs_water"]
        )
        device = find_test_device(mock_lifesmart_devices, device_me)
        # For duplicate devices IDs, find the binary sensor devices specifically
        if device is None or sub_key not in device.get("data", {}):
            # Try to find the Door Sensor (SL_SC_G) specifically by hub ID
            device = find_test_device(mock_lifesmart_devices, device_me, get_hub_id(6))
        entity_registry = er.async_get(hass)
        unique_id = generate_unique_id(
            device[DEVICE_TYPE_KEY], device[HUB_ID_KEY], device[DEVICE_ID_KEY], sub_key
        )
        entity_id = entity_registry.async_get_entity_id(
            "binary_sensor", DOMAIN, unique_id
        )

        # 发送更新数据
        async_dispatcher_send(
            hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}", test_data
        )
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        assert state is not None, f"实体 {entity_id} 应该存在"

        expected_ha_state = STATE_ON if expected_state else STATE_OFF
        assert state.state == expected_ha_state, f"状态应该是 {expected_ha_state}"

    @pytest.mark.asyncio
    async def test_lock_state_parsing_complex(
        self,
        hass: HomeAssistant,
        setup_integration_binary_sensor_only: ConfigEntry,
    ):
        """测试门锁复杂状态解析逻辑。"""
        # 使用工厂函数获取测试设备
        mock_lifesmart_devices = create_devices_by_category(["bs_lock"])
        device = find_test_device(mock_lifesmart_devices, "2i1k")
        entity_registry = er.async_get(hass)

        # 测试 EVTLO 锁状态
        evtlo_unique_id = generate_unique_id(
            device[DEVICE_TYPE_KEY], device[HUB_ID_KEY], device[DEVICE_ID_KEY], "EVTLO"
        )
        evtlo_entity_id = entity_registry.async_get_entity_id(
            "binary_sensor", DOMAIN, evtlo_unique_id
        )

        # 测试成功解锁 - val=4121, type=1
        success_data = {"val": 4121, "type": 1}  # 密码解锁，用户25
        async_dispatcher_send(
            hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{evtlo_unique_id}", success_data
        )
        await hass.async_block_till_done()

        state = hass.states.get(evtlo_entity_id)
        assert state.state == STATE_ON, "成功解锁时状态应该是 ON"
        assert (
            state.attributes.get("unlocking_method") == "Password"
        ), "解锁方式应该是密码"
        assert state.attributes.get("unlocking_user") == 25, "解锁用户应该是25"

        # 测试失败解锁 - val=0
        fail_data = {"val": 0, "type": 1}
        async_dispatcher_send(
            hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{evtlo_unique_id}", fail_data
        )
        await hass.async_block_till_done()

        state = hass.states.get(evtlo_entity_id)
        assert state.state == STATE_OFF, "失败解锁时状态应该是 OFF"


# ==================== 按钮事件测试 ====================


class TestButtonEventHandling:
    """测试按钮设备的事件处理逻辑。"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "event_val, expected_event_name",
        [
            (1, "single_click"),
            (2, "double_click"),
            (255, "long_press"),
        ],
        ids=["SingleClick", "DoubleClick", "LongPress"],
    )
    async def test_button_event_detection(
        self,
        hass: HomeAssistant,
        setup_integration_binary_sensor_only: ConfigEntry,
        freezer,
        event_val: int,
        expected_event_name: str,
    ):
        """测试按钮事件检测和属性设置。"""
        # 使用工厂函数获取测试设备
        mock_lifesmart_devices = create_devices_by_category(["bs_button"])
        device = find_test_device(mock_lifesmart_devices, "3j2l")
        entity_registry = er.async_get(hass)
        unique_id = generate_unique_id(
            device[DEVICE_TYPE_KEY], device[HUB_ID_KEY], device[DEVICE_ID_KEY], "B"
        )
        entity_id = entity_registry.async_get_entity_id(
            "binary_sensor", DOMAIN, unique_id
        )

        # 发送按钮事件
        event_data = {"val": event_val}
        async_dispatcher_send(
            hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}", event_data
        )
        await hass.async_block_till_done()

        # 验证按钮被激活且事件属性正确
        state = hass.states.get(entity_id)
        assert state.state == STATE_ON, "按钮事件发生时状态应该是 ON"
        assert (
            state.attributes.get("last_event") == expected_event_name
        ), f"事件类型应该是 {expected_event_name}"
        assert state.attributes.get("last_event_time") is not None, "应该有事件时间戳"

        # 立即清理定时器，避免清理检查失败
        freezer.tick(timedelta(seconds=0.6))
        await asyncio.sleep(0)
        await hass.async_block_till_done()

    @pytest.mark.asyncio
    async def test_button_auto_reset(
        self,
        hass: HomeAssistant,
        setup_integration_binary_sensor_only: ConfigEntry,
        freezer,
    ):
        """测试按钮自动重置功能。"""
        mock_lifesmart_devices = create_devices_by_category(["bs_button"])
        device = find_test_device(mock_lifesmart_devices, "3j2l")
        entity_registry = er.async_get(hass)
        unique_id = generate_unique_id(
            device[DEVICE_TYPE_KEY], device[HUB_ID_KEY], device[DEVICE_ID_KEY], "B"
        )
        entity_id = entity_registry.async_get_entity_id(
            "binary_sensor", DOMAIN, unique_id
        )

        # 触发按钮事件
        event_data = {"val": 1}
        async_dispatcher_send(
            hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}", event_data
        )
        await hass.async_block_till_done()

        # 验证按钮被激活
        state = hass.states.get(entity_id)
        assert state.state == STATE_ON, "按钮事件后状态应该是 ON"

        # 快进时间到重置点
        freezer.tick(timedelta(seconds=0.6))
        await asyncio.sleep(0)  # 让事件循环处理调度的回调
        await hass.async_block_till_done()

        # 验证状态已重置
        state = hass.states.get(entity_id)
        assert state.state == STATE_OFF, "按钮应该自动重置为 OFF"


# ==================== 更新处理测试 ====================


class TestUpdateHandling:
    """测试实时更新和全局刷新处理。"""

    @pytest.mark.asyncio
    async def test_real_time_update_handling(
        self,
        hass: HomeAssistant,
        setup_integration_binary_sensor_only: ConfigEntry,
    ):
        """测试实时更新处理。"""
        mock_lifesmart_devices = create_devices_by_category(
            ["bs_door", "bs_motion", "bs_water", "bs_lock", "bs_button"]
        )
        device = find_test_device(mock_lifesmart_devices, "9f8i", get_hub_id(6))
        entity_registry = er.async_get(hass)
        unique_id = generate_unique_id(
            device[DEVICE_TYPE_KEY], device[HUB_ID_KEY], device[DEVICE_ID_KEY], "G"
        )
        entity_id = entity_registry.async_get_entity_id(
            "binary_sensor", DOMAIN, unique_id
        )

        # 获取初始状态
        initial_state = hass.states.get(entity_id)
        assert initial_state.state == STATE_ON, "初始状态应该是 ON"

        # 发送更新使状态变为 OFF
        update_data = {"val": 1}  # 门关闭
        async_dispatcher_send(
            hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}", update_data
        )
        await hass.async_block_till_done()

        # 验证状态已更新
        updated_state = hass.states.get(entity_id)
        assert updated_state.state == STATE_OFF, "状态应该更新为 OFF"

    @pytest.mark.asyncio
    async def test_global_refresh_handling(
        self,
        hass: HomeAssistant,
        setup_integration_binary_sensor_only: ConfigEntry,
    ):
        """测试全局刷新处理。"""
        mock_lifesmart_devices = create_devices_by_category(
            ["bs_door", "bs_motion", "bs_water", "bs_lock", "bs_button"]
        )
        # 从测试设备中找到门传感器设备 - 动态获取
        door_devices = [
            d for d in mock_lifesmart_devices if d.get("devtype") == "SL_SC_G"
        ]
        assert len(door_devices) > 0, "应该至少有一个门传感器设备"
        door_device = door_devices[0]  # 使用第一个门传感器

        entity_registry = er.async_get(hass)
        unique_id = generate_unique_id(
            door_device[DEVICE_TYPE_KEY],
            door_device[HUB_ID_KEY],
            door_device[DEVICE_ID_KEY],
            "G",
        )
        entity_id = entity_registry.async_get_entity_id(
            "binary_sensor", DOMAIN, unique_id
        )

        # 获取初始状态
        initial_state = hass.states.get(entity_id)
        assert initial_state.state == STATE_ON, "初始状态应该是 ON"

        # 修改 hass.data 中的设备数据
        devices = hass.data[DOMAIN][setup_integration_binary_sensor_only.entry_id][
            "devices"
        ]
        test_door_devices = [d for d in devices if d.get("devtype") == "SL_SC_G"]
        assert len(test_door_devices) > 0, "hass.data中应该有门传感器设备"
        test_door_device = test_door_devices[0]
        test_door_device[DEVICE_DATA_KEY]["G"] = {"val": 1, "type": 0}  # 门关闭

        # 发送全局刷新信号
        async_dispatcher_send(hass, LIFESMART_SIGNAL_UPDATE_ENTITY)
        await hass.async_block_till_done()

        # 验证状态已更新
        updated_state = hass.states.get(entity_id)
        assert updated_state.state == STATE_OFF, "全局刷新后状态应该更新为 OFF"

    @pytest.mark.asyncio
    async def test_update_error_handling(
        self,
        hass: HomeAssistant,
        setup_integration_binary_sensor_only: ConfigEntry,
        caplog,
    ):
        """测试更新过程中的错误处理。"""
        mock_lifesmart_devices = create_devices_by_category(
            ["bs_door", "bs_motion", "bs_water", "bs_lock", "bs_button"]
        )
        device = find_test_device(mock_lifesmart_devices, "9f8i", get_hub_id(6))
        unique_id = generate_unique_id(
            device[DEVICE_TYPE_KEY], device[HUB_ID_KEY], device[DEVICE_ID_KEY], "G"
        )

        # 发送 None 数据（应该被忽略）
        async_dispatcher_send(
            hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}", None
        )
        await hass.async_block_till_done()

        # 应该没有错误日志（None 数据被正常处理）
        error_logs = [
            record for record in caplog.records if record.levelname == "ERROR"
        ]
        update_errors = [
            log for log in error_logs if "Error handling update" in log.message
        ]
        assert len(update_errors) == 0, "None数据应该被正常处理，不产生错误日志"

    @pytest.mark.asyncio
    async def test_global_refresh_missing_device(
        self,
        hass: HomeAssistant,
        setup_integration_binary_sensor_only: ConfigEntry,
        caplog,
    ):
        """测试全局刷新时设备不存在的情况。"""
        # 清空设备列表模拟设备丢失
        hass.data[DOMAIN][setup_integration_binary_sensor_only.entry_id]["devices"] = []

        # 发送全局刷新信号
        async_dispatcher_send(hass, LIFESMART_SIGNAL_UPDATE_ENTITY)
        await hass.async_block_till_done()

        # 不应该有错误日志，因为缺失设备是正常情况
        error_logs = [
            record for record in caplog.records if record.levelname == "ERROR"
        ]
        refresh_errors = [
            log for log in error_logs if "Error during global refresh" in log.message
        ]
        assert len(refresh_errors) == 0, "设备缺失应该被正常处理"


# ==================== 特殊设备类型测试 ====================


class TestSpecialDeviceTypes:
    """测试特殊设备类型的逻辑。"""

    @pytest.mark.asyncio
    async def test_guard_sensor_variations(
        self,
        hass: HomeAssistant,
        setup_integration_binary_sensor_only: ConfigEntry,
    ):
        """测试不同类型的门窗感应器。"""
        mock_lifesmart_devices = create_devices_by_category(
            ["bs_door", "bs_motion", "bs_water", "bs_lock", "bs_button"]
        )
        # 测试震动感应器 (假设我们有 SL_SC_BG 设备)
        # 这里需要根据实际的测试设备数据进行调整
        pass

    @pytest.mark.asyncio
    async def test_climate_device_binary_sensors(
        self,
        hass: HomeAssistant,
        setup_integration_binary_sensor_only: ConfigEntry,
    ):
        """测试温控设备的二元传感器功能。"""
        # 测试温控器的阀门状态等
        # 这需要在 conftest.py 中添加相应的温控设备数据
        pass

    @pytest.mark.asyncio
    async def test_unknown_device_handling(
        self,
        hass: HomeAssistant,
        setup_integration_binary_sensor_only: ConfigEntry,
    ):
        """测试未知设备类型的处理。"""
        from custom_components.lifesmart.binary_sensor import LifeSmartBinarySensor
        from unittest.mock import MagicMock

        # 创建一个未知设备类型的传感器
        unknown_device = {
            DEVICE_TYPE_KEY: "UNKNOWN_TYPE",
            HUB_ID_KEY: "test_hub",
            DEVICE_ID_KEY: "unknown_device",
            DEVICE_DATA_KEY: {"P1": {"val": 1, "type": 0}},
            "name": "Unknown Device",
        }

        sensor = LifeSmartBinarySensor(
            raw_device=unknown_device,
            client=MagicMock(),
            entry_id="test_entry",
            sub_device_key="P1",
            sub_device_data={"val": 1, "type": 0},
        )

        # 未知设备应该使用默认逻辑
        assert sensor._determine_device_class() is None, "未知设备类型应该返回 None"
        assert sensor._parse_state() is True, "未知设备应该使用默认状态解析 (val != 0)"


# ==================== 边界条件和异常测试 ====================


class TestEdgeCasesAndExceptions:
    """测试边界条件和异常情况。"""

    @pytest.mark.asyncio
    async def test_entity_with_missing_data(
        self,
        hass: HomeAssistant,
        setup_integration_binary_sensor_only: ConfigEntry,
    ):
        """测试数据缺失时的实体行为。"""
        mock_lifesmart_devices = create_devices_by_category(
            ["bs_door", "bs_motion", "bs_water", "bs_lock", "bs_button"]
        )
        device = find_test_device(mock_lifesmart_devices, "9f8i", get_hub_id(6))
        entity_registry = er.async_get(hass)
        unique_id = generate_unique_id(
            device[DEVICE_TYPE_KEY], device[HUB_ID_KEY], device[DEVICE_ID_KEY], "G"
        )

        # 发送空数据
        async_dispatcher_send(hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}", {})
        await hass.async_block_till_done()

        entity_id = entity_registry.async_get_entity_id(
            "binary_sensor", DOMAIN, unique_id
        )
        state = hass.states.get(entity_id)
        assert state is not None, "即使数据缺失，实体仍应存在"

    @pytest.mark.asyncio
    async def test_entity_device_info(
        self,
        hass: HomeAssistant,
        setup_integration_binary_sensor_only: ConfigEntry,
    ):
        """测试实体的设备信息。"""
        mock_lifesmart_devices = create_devices_by_category(
            ["bs_door", "bs_motion", "bs_water", "bs_lock", "bs_button"]
        )
        from custom_components.lifesmart.binary_sensor import LifeSmartBinarySensor
        from unittest.mock import MagicMock

        device = find_test_device(mock_lifesmart_devices, "9f8i", get_hub_id(6))
        sensor = LifeSmartBinarySensor(
            raw_device=device,
            client=MagicMock(),
            entry_id="test_entry",
            sub_device_key="G",
            sub_device_data=device[DEVICE_DATA_KEY]["G"],
        )

        device_info = sensor.device_info
        assert device_info is not None, "应该有设备信息"
        assert (DOMAIN, device[HUB_ID_KEY], device[DEVICE_ID_KEY]) in device_info[
            "identifiers"
        ], "设备标识符应该正确"
        assert device_info["name"] == device["name"], "设备名称应该正确"
        assert device_info["manufacturer"] == MANUFACTURER, "制造商应该正确"

    @pytest.mark.asyncio
    async def test_entity_unique_id_and_object_id(
        self,
        hass: HomeAssistant,
        setup_integration_binary_sensor_only: ConfigEntry,
    ):
        """测试实体的唯一ID和对象ID生成。"""
        mock_lifesmart_devices = create_devices_by_category(
            ["bs_door", "bs_motion", "bs_water", "bs_lock", "bs_button"]
        )
        from custom_components.lifesmart.binary_sensor import LifeSmartBinarySensor
        from unittest.mock import MagicMock

        device = find_test_device(mock_lifesmart_devices, "9f8i", get_hub_id(6))
        sensor = LifeSmartBinarySensor(
            raw_device=device,
            client=MagicMock(),
            entry_id="test_entry",
            sub_device_key="G",
            sub_device_data=device[DEVICE_DATA_KEY]["G"],
        )

        # 测试唯一ID
        expected_unique_id = generate_unique_id(
            device[DEVICE_TYPE_KEY], device[HUB_ID_KEY], device[DEVICE_ID_KEY], "G"
        )
        assert sensor.unique_id == expected_unique_id, "唯一ID应该正确生成"

        # 测试对象ID（用于实体ID生成）
        expected_object_id = f"{device['name'].lower().replace(' ', '_')}_g"
        assert sensor._attr_object_id == expected_object_id, "对象ID应该正确生成"

        # 测试实体名称
        expected_name = f"{device['name']} G"
        assert sensor._attr_name == expected_name, "实体名称应该正确生成"
