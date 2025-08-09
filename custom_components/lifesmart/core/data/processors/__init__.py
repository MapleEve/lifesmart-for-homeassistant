"""
Data Processors Module - 数据处理器模块
由 @MapleEve 初始创建和维护

此模块包含所有的数据处理器，负责将原始IO数据转换为HA可用的格式。
"""

from .data_processors import (
    ALMDataProcessor,
    ALMBitResult,
    alm_data_processor,
    is_alm_io_port,
    process_alm_data,
    get_alm_subdevices,
    EVTLODataProcessor,
    EVTLODataResult,
    evtlo_data_processor,
    is_evtlo_io_port,
    process_evtlo_data,
    get_evtlo_subdevices,
)
from .io_processors import process_io_data
from .logic_processors import (
    DirectProcessor,
    TypeBit0Processor,
    get_processor_registry,
)

__all__ = [
    "process_io_data",
    "DirectProcessor",
    "TypeBit0Processor",
    "get_processor_registry",
    "ALMDataProcessor",
    "ALMBitResult",
    "alm_data_processor",
    "is_alm_io_port",
    "process_alm_data",
    "get_alm_subdevices",
    "EVTLODataProcessor",
    "EVTLODataResult",
    "evtlo_data_processor",
    "is_evtlo_io_port",
    "process_evtlo_data",
    "get_evtlo_subdevices",
]
