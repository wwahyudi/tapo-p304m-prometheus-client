"""# tapo_p304m.py"""
import logging
from typing import Dict, Any, List
from tapo_device import TapoDevice

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def nan_usage():
    """Helper for default device usage with NaN values for Prometheus-friendly missing data."""
    return {
        'power_usage': {'past30': float('nan'), 'past7': float('nan'), 'today': float('nan')},
        'saved_power': {'past30': float('nan'), 'past7': float('nan'), 'today': float('nan')},
        'time_usage':  {'past30': float('nan'), 'past7': float('nan'), 'today': float('nan')}
    }


def empty_device_info():
    """Helper for default device info with 'unknown' values."""
    return {
        'device_id' : 'unknown',
        'fw_ver'    : 'unknown',
        'hw_id'     : 'unknown',
        'ip'        : 'unknown',
        'model'     : 'unknown',
        'type'      : 'unknown'
    }


class TapoP304m:
    """
    Tapo P304m device class for managing Tapo P304m smart plugs
    Code taken from 
    https://www.bentasker.co.uk/posts/blog/house-stuff/how-much-more-energy-efficient-is-eco-mode-on-a-dish-washer.html#tapo
    """

    def __init__(self, ip_address, username, password, **kwargs):
        """initialize Tapo P304m device with IP address, username, and password"""
        self.username   = username
        self.password   = password
        self.ip_address = ip_address
        self.kwargs     = kwargs
        self.tapo_device= TapoDevice(self.ip_address, self.username, self.password, **self.kwargs)


    def tapo_p304m_device_info(self) -> Dict[str, Any]:
        """Get device info; returns all fields as 'unknown' if unavailable"""
        try:
            return self.tapo_device.get_device_info()
        except Exception as ex: # pylint: disable=broad-except
            logger.warning("Failed to get device info from %s: %s", self.ip_address, ex)
            return empty_device_info()


    def tapo_p304m_device_usage(self) -> Dict[str, Any]:
        """Get device usage; returns NaN values for Prometheus if unavailable"""
        try:
            return self.tapo_device.get_device_usage()
        except Exception as ex: # pylint: disable=broad-except
            logger.warning("Failed to get device usage from %s: %s", self.ip_address, ex)
            return nan_usage()


    def tapo_p304m_plugs(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get the list of plugs connected to the Tapo P304m device"""
        try:
            plugs_info = self.tapo_device.get_child_device_list()
            plugs_usage = self.tapo_device.get_realtime_power_usage()

            plugs = plugs_info.get('child_device_list', [])
            usage_data = plugs_usage.get('data', [])
            n = min(len(plugs), len(usage_data))

            for i in range(n):
                # Map usage data in reverse order (as in your logic)
                plugs[i].update(usage_data[-(i+1)])

                # Standardize status fields
                plugs[i]['device_on'] = 'ON' if plugs[i].get('device_on') else 'OFF'
                plugs[i]['charging_status'] = plugs[i].get('charging_status', 'unknown')

            # Return only actual plugs detected and merged
            return {'child_device_list': plugs[:n]}

        except Exception as ex: # pylint: disable=broad-except
            logger.warning("Failed to get plug info from %s: %s", self.ip_address, ex)
            # On error, return *empty* list (no phantom plugs)
            return {'child_device_list': []}
