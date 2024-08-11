import logging
from base64 import b64decode
from .auth_protocol import AuthProtocol

log = logging.getLogger(__name__)

# Code taken from https://github.com/almottier/TapoP100

class Device:
    def __init__(self, address, email, password, preferred_protocol=None, **kwargs):
        self.address = address
        self.email = email
        self.password = password
        self.kwargs = kwargs
        self.protocol = None
        self.preferred_protocol = preferred_protocol

    def _initialize(self):
        protocol_classes = {"new": AuthProtocol}

        for protocol_class in protocol_classes.values():
            if not self.protocol:
                try:
                    protocol = protocol_class(
                        self.address, self.email, self.password, **self.kwargs
                    )
                    protocol.Initialize()
                    self.protocol = protocol
                except:
                    log.exception(
                        f"Failed to initialize protocol {protocol_class.__name__}"
                    )
        if not self.protocol:
            raise Exception("Failed to initialize protocol")

    def request(self, method: str, params: dict = None):
        if not self.protocol:
            self._initialize()
        return self.protocol._request(method, params)

    def handshake(self):
        if not self.protocol:
            self._initialize()
        return

    def login(self):
        return self.handshake()

    def getDeviceInfo(self):
        return self.request("get_device_info")
    
    # Some endpoints taken from:
    # - https://pypi.org/project/tapo-plug/
    # - https://github.com/softScheck/tplink-smartplug/blob/master/tplink-smarthome-commands.txt
    # - https://www.github-zh.com/projects/500625057-tapo

    # new added
    def getChildDeviceList(self):
        return self.request("get_child_device_list")
    
    # new added
    def getChildDeviceComponentList(self):
        return self.request("get_child_device_component_list")

    # new added
    def getLatestFirmware(self):
        return self.request("get_latest_fw")

    # new added
    def getFirmwareDownloadState(self):
        return self.request("get_fw_download_state")

    # new added
    def getDeviceUsage(self):
        return self.request("get_device_usage")
    
    # new added
    def getRealtimePowerUsage(self):
        return self.request("get_realtime")

    def _get_device_info(self):
        return self.request("get_device_info")

    def _set_device_info(self, params: dict):
        return self.request("set_device_info", params)

    def getDeviceName(self):
        data = self.getDeviceInfo()
        encodedName = data["nickname"]
        name = b64decode(encodedName)
        return name.decode("utf-8")

class P100(Device):
    pass
