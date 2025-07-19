"""Abstract base class for LifeSmart clients.

This module defines the AbstractLifeSmartClient ABC that enforces interface
consistency between cloud and local LifeSmart clients. It ensures that both
client implementations provide the same control methods with identical signatures.
"""

from abc import ABC, abstractmethod
from typing import Any, List, Dict

from homeassistant.components.climate import HVACMode


class AbstractLifeSmartClient(ABC):
    """Abstract Base Class for LifeSmart clients.
    
    This class defines the common interface that all LifeSmart clients must implement,
    ensuring consistency between cloud (LifeSmartClient) and local (LifeSmartLocalClient)
    implementations.
    """

    @abstractmethod
    async def get_all_device_async(self) -> List[Dict[str, Any]]:
        """Get all devices.
        
        Returns:
            A list of device dictionaries containing device information.
        """
        pass

    @abstractmethod
    async def turn_on_light_switch_async(self, idx: str, agt: str, me: str) -> int:
        """Turn on a light or switch.
        
        Args:
            idx: Subdevice index/key.
            agt: Hub/Agent ID.
            me: Device ID.
            
        Returns:
            Status code (0 for success, non-zero for error).
        """
        pass

    @abstractmethod
    async def turn_off_light_switch_async(self, idx: str, agt: str, me: str) -> int:
        """Turn off a light or switch.
        
        Args:
            idx: Subdevice index/key.
            agt: Hub/Agent ID.
            me: Device ID.
            
        Returns:
            Status code (0 for success, non-zero for error).
        """
        pass

    @abstractmethod
    async def send_epset_async(
        self, agt: str, me: str, idx: str, command_type: str, val: Any
    ) -> int:
        """Send a generic EpSet command to a device endpoint.
        
        Args:
            agt: Hub/Agent ID.
            me: Device ID.
            idx: Subdevice index/key.
            command_type: Command type constant.
            val: Command value.
            
        Returns:
            Status code (0 for success, non-zero for error).
        """
        pass

    @abstractmethod
    async def async_set_multi_ep_async(
        self, agt: str, me: str, io_list: List[Dict]
    ) -> int:
        """Send multiple IO commands to a device simultaneously.
        
        Args:
            agt: Hub/Agent ID.
            me: Device ID.
            io_list: List of IO command dictionaries.
            
        Returns:
            Status code (0 for success, non-zero for error).
        """
        pass

    @abstractmethod
    async def open_cover_async(self, agt: str, me: str, device_type: str) -> int:
        """Open a cover (curtain, garage door, etc.).
        
        Args:
            agt: Hub/Agent ID.
            me: Device ID.
            device_type: Device type identifier.
            
        Returns:
            Status code (0 for success, non-zero for error).
        """
        pass

    @abstractmethod
    async def close_cover_async(self, agt: str, me: str, device_type: str) -> int:
        """Close a cover (curtain, garage door, etc.).
        
        Args:
            agt: Hub/Agent ID.
            me: Device ID.
            device_type: Device type identifier.
            
        Returns:
            Status code (0 for success, non-zero for error).
        """
        pass

    @abstractmethod
    async def stop_cover_async(self, agt: str, me: str, device_type: str) -> int:
        """Stop a cover (curtain, garage door, etc.).
        
        Args:
            agt: Hub/Agent ID.
            me: Device ID.
            device_type: Device type identifier.
            
        Returns:
            Status code (0 for success, non-zero for error).
        """
        pass

    @abstractmethod
    async def set_cover_position_async(
        self, agt: str, me: str, position: int, device_type: str
    ) -> int:
        """Set cover position.
        
        Args:
            agt: Hub/Agent ID.
            me: Device ID.
            position: Target position (0-100).
            device_type: Device type identifier.
            
        Returns:
            Status code (0 for success, non-zero for error).
        """
        pass

    @abstractmethod
    async def async_set_climate_hvac_mode(
        self,
        agt: str,
        me: str,
        device_type: str,
        hvac_mode: HVACMode,
        current_val: int = 0,
    ) -> int:
        """Set HVAC mode for climate devices.
        
        Args:
            agt: Hub/Agent ID.
            me: Device ID.
            device_type: Device type identifier.
            hvac_mode: Target HVAC mode.
            current_val: Current device value for bitwise operations.
            
        Returns:
            Status code (0 for success, non-zero for error).
        """
        pass

    @abstractmethod
    async def async_set_climate_temperature(
        self, agt: str, me: str, device_type: str, temp: float
    ) -> int:
        """Set target temperature for climate devices.
        
        Args:
            agt: Hub/Agent ID.
            me: Device ID.
            device_type: Device type identifier.
            temp: Target temperature in Celsius.
            
        Returns:
            Status code (0 for success, non-zero for error).
        """
        pass

    @abstractmethod
    async def async_set_climate_fan_mode(
        self, agt: str, me: str, device_type: str, fan_mode: str, current_val: int = 0
    ) -> int:
        """Set fan mode for climate devices.
        
        Args:
            agt: Hub/Agent ID.
            me: Device ID.
            device_type: Device type identifier.
            fan_mode: Target fan mode.
            current_val: Current device value for bitwise operations.
            
        Returns:
            Status code (0 for success, non-zero for error).
        """
        pass

    @abstractmethod
    async def press_switch_async(
        self, idx: str, agt: str, me: str, duration_ms: int
    ) -> int:
        """Perform a momentary switch press operation.
        
        Args:
            idx: Subdevice index/key.
            agt: Hub/Agent ID.
            me: Device ID.
            duration_ms: Press duration in milliseconds.
            
        Returns:
            Status code (0 for success, non-zero for error).
        """
        pass

    @abstractmethod
    async def set_scene_async(self, agt: str, scene_id: str) -> int:
        """Activate a scene.
        
        Args:
            agt: Hub/Agent ID.
            scene_id: Scene identifier.
            
        Returns:
            Status code (0 for success, non-zero for error).
        """
        pass

    @abstractmethod
    async def send_ir_key_async(
        self, agt: str, ai: str, me: str, category: str, brand: str, keys: str
    ) -> int:
        """Send infrared key command.
        
        Args:
            agt: Hub/Agent ID.
            ai: AI identifier.
            me: Device ID.
            category: IR device category.
            brand: IR device brand.
            keys: Key codes to send.
            
        Returns:
            Status code (0 for success, non-zero for error).
        """
        pass