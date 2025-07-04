"""# tapo_device.py"""
import logging
from base64 import b64decode
from typing import Optional, Dict, Any, Type
from auth_protocol import AuthProtocol

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)


class TapoDevice:
    """
    Base class for Tapo devices, providing common functionality
    Original code idea taken from https://github.com/almottier/TapoP100
    """

    # Registry of supported protocols for flexibility/extensibility
    protocol_classes: Dict[str, Type[AuthProtocol]] = {
        "new": AuthProtocol
    }


    def __init__(
            self,
            address: str,
            email: str,
            password: str,
            preferred_protocol: Optional[str] = None,
            **kwargs
        ):
        self.address                            = address
        self.email                              = email
        self.password                           = password
        self.kwargs                             = kwargs
        self.protocol: Optional[AuthProtocol]   = None
        self.preferred_protocol                 = preferred_protocol


    def _initialize(self):
        """Initialize the device protocol based on the preferred protocol or available protocols"""
        preferred = self.preferred_protocol or "new"
        protocol_cls = self.protocol_classes.get(preferred)
        if not protocol_cls:
            raise ValueError(f"Unsupported protocol: {preferred}")

        try:
            self.protocol = protocol_cls(self.address, self.email, self.password, **self.kwargs)
            self.protocol.initialize()
        except Exception as e:
            log.exception("Failed to initialize protocol %s", protocol_cls.__name__)
            raise RuntimeError("Failed to initialize protocol") from e


    def _ensure_protocol(self) -> None:
        """Ensure protocol is initialized"""
        if not self.protocol:
            self._initialize()


    def request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Make a request to the device using the specified method and parameters."""
        self._ensure_protocol()
        if self.protocol is None:
            raise RuntimeError("Protocol is not initialized")
        return self.protocol.request(method, params or {})


    def handshake(self) -> None:
        """Perform handshake to establish communication."""
        self._ensure_protocol()


    def login(self) -> None:
        """Login to the device."""
        self.handshake()


    def get_device_info(self) -> dict:
        """Get device information"""
        return self.request("get_device_info")

    def set_device_info(self, params: Dict[str, Any]) -> dict:
        """Internal method to set device information"""
        return self.request("set_device_info", params)

    # Some endpoints taken from:
    # - https://pypi.org/project/tapo-plug/
    # - https://github.com/softScheck/tplink-smartplug/blob/master/tplink-smarthome-commands.txt
    # - https://www.github-zh.com/projects/500625057-tapo

    # new added
    def get_child_device_list(self) -> dict:
        """Get the list of child devices (plugs) connected to the main device"""
        return self.request("get_child_device_list")

    # new added
    def get_child_device_component_list(self) -> dict:
        """Get the list of components for each child device"""
        return self.request("get_child_device_component_list")

    # new added
    def get_latest_fw(self) -> dict:
        """Get the latest firmware information for the device"""
        return self.request("get_latest_fw")

    # new added
    def get_fw_download_state(self) -> dict:
        """Get the current state of the firmware download"""
        return self.request("get_fw_download_state")

    # new added
    def get_device_usage(self) -> dict:
        """Get the device usage statistics"""
        return self.request("get_device_usage")

    # new added
    def get_realtime_power_usage(self) -> dict:
        """Get the real-time power usage of the device"""
        return self.request("get_realtime")

    def get_device_name(self) -> str:
        """Get the device name (decoded from base64)."""
        data = self.get_device_info()
        try:
            encoded_name = data.get("nickname", "")
            name = b64decode(encoded_name).decode("utf-8")
        except Exception: # pylint: disable=broad-except
            log.exception("Failed to decode device nickname")
            name = ""
        return name
