from PyP100 import PyP100

# Code taken from https://www.bentasker.co.uk/posts/blog/house-stuff/how-much-more-energy-efficient-is-eco-mode-on-a-dish-washer.html#tapo
class TapoP304m:
    def __init__(self, ip_address, username, password, **kwargs):
        self.username = username
        self.password = password
        self.ip_address = ip_address
        self.kwargs = kwargs
        self.p100 = PyP100.P100(self.ip_address, self.username, self.password)
        
    def tapo_p304m_device_info(self):
        try:
            device_info = self.p100.getDeviceInfo()
            return device_info    
        except:
            #return {'return': -1, 'error': f'Failed to communicate with device {self.ip_address}'}
            return {'device_id' : 'unknown', 
                      'fw_ver'  : 'unknown', 
                      'hw_id'   : 'unknown', 
                      'ip'      : 'unknown', 
                      'model'   : 'unknown', 
                      'type'    : 'unknown'}

    def tapo_p304m_device_usage(self):
        try:
            device_usage = self.p100.getDeviceUsage()
            return device_usage    
        except:
            #return {'return': -1, 'error': f'Failed to communicate with device {self.ip_address}'}
            return {'power_usage': {'past30': -1, 'past7': -1, 'today': -1},
                    'saved_power': {'past30': -1, 'past7': -1, 'today': -1},
                    'time_usage' : {'past30': -1, 'past7': -1, 'today': -1}}


    def tapo_p304m_plugs(self):
        try:
            plugs_info = self.p100.getChildDeviceList()

            plugs_usage = self.p100.getRealtimePowerUsage()

            # Merge data based on mapping
            plugs_info['child_device_list'][0].update(plugs_usage['data'][3])
            plugs_info['child_device_list'][1].update(plugs_usage['data'][2])
            plugs_info['child_device_list'][2].update(plugs_usage['data'][1])
            plugs_info['child_device_list'][3].update(plugs_usage['data'][0])

            # Convert value True to On & False to Off for device_on
            for plug_info in plugs_info['child_device_list']:
                if plug_info['device_on'] is True:
                    plug_info['device_on'] = 'ON'
                elif plug_info['device_on'] is False:
                    plug_info['device_on'] = 'OFF'

            return plugs_info    
        except:
            #return {'return': -1, 'error': f'Failed to communicate with device {self.ip_address}'}
            return {'child_device_list': [{'charging_status'   : 'abnormal',
                                            'current_ma'        : -1,
                                            'device_id'         : 'unknown_plug_1',
                                            'device_on'         : 'OFF',
                                            'on_time'           : -1,
                                            'overcurrent_status': 'abnormal',
                                            'overheat_status'   : 'abnormal',
                                            'position'          : -1,
                                            'power_mw'          : -1,
                                            'total_wh'          : -1,
                                            'voltage_mv'        : -1},
                                            {'charging_status'   : 'abnormal',
                                            'current_ma'        : -1,
                                            'device_id'         : 'unknown_plug_2',
                                            'device_on'         : 'OFF',
                                            'on_time'           : -1,
                                            'overcurrent_status': 'abnormal',
                                            'overheat_status'   : 'abnormal',
                                            'position'          : -1,
                                            'power_mw'          : -1,
                                            'total_wh'          : -1,
                                            'voltage_mv'        : -1},
                                            {'charging_status'   : 'abnormal',
                                            'current_ma'        : -1,
                                            'device_id'         : 'unknown_plug_3',
                                            'device_on'         : 'OFF',
                                            'on_time'           : -1,
                                            'overcurrent_status': 'abnormal',
                                            'overheat_status'   : 'abnormal',
                                            'position'          : -1,
                                            'power_mw'          : -1,
                                            'total_wh'          : -1,
                                            'voltage_mv'        : -1},
                                            {'charging_status'   : 'abnormal',
                                            'current_ma'        : -1,
                                            'device_id'         : 'unknown_plug_4',
                                            'device_on'         : 'OFF',
                                            'on_time'           : -1,
                                            'overcurrent_status': 'abnormal',
                                            'overheat_status'   : 'abnormal',
                                            'position'          : -1,
                                            'power_mw'          : -1,
                                            'total_wh'          : -1,
                                            'voltage_mv'        : -1}
                                            ]}
        
