from flask import Flask
from prometheus_client import make_wsgi_app, CollectorRegistry, Gauge, Enum
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from TapoP304m import TapoP304m
import asyncio
import threading
import os

TAPO_USERNAME = os.environ.get('TAPO_USERNAME')
TAPO_PASSWORD = os.environ.get('TAPO_PASSWORD')
TAPO_IP_ADDRESS = os.environ.get('TAPO_IP_ADDRESS')

tapo_p304m = TapoP304m(TAPO_IP_ADDRESS, TAPO_USERNAME, TAPO_PASSWORD)

device_info = tapo_p304m.tapo_p304m_device_info()
default_device_labels = {'device_id'   : device_info['device_id'], 
                        'fw_ver'      : device_info['fw_ver'], 
                        'hw_id'       : device_info['hw_id'], 
                        'ip'          : device_info['ip'], 
                        'model'       : device_info['model'], 
                        'type'        : device_info['type']}

# label for gauge device usage
label_gauge_device_usage = ['device_id','hw_id','fw_ver','ip','type','model']

registry = CollectorRegistry()

#### DEVICE
# gauge device usage power_usage
gauge_device_usage_power_usage = Gauge(
    'tapo_p304m_device_usage_power_usage', 
    'Tapo P304m device power usage (in milliwatt).', 
    ['device_id', 'hw_id', 'fw_ver', 'ip', 'type', 'model', 'period'],
    registry=registry
)

# gauge device usage saved_power
gauge_device_usage_saved_power = Gauge(
    'tapo_p304m_device_usage_saved_power', 
    'Tapo P304m device saved power (in milliwatt).', 
    ['device_id', 'hw_id', 'fw_ver', 'ip', 'type', 'model', 'period'],
    registry=registry
)

# gauge device usage time_usage
gauge_device_usage_time_usage = Gauge(
    'tapo_p304m_device_usage_time_usage', 
    'Tapo P304m device time usage (in second).', 
    ['device_id', 'hw_id', 'fw_ver', 'ip', 'type', 'model', 'period'],
    registry=registry
)

#### PLUGS
# gauge plug current reading
gauge_plug_current_ma = Gauge(
    'tapo_p304m_plug_current_ma', 
    'Tapo P304m plug currents (in milliampere).', 
    ['device_id', 'hw_id', 'fw_ver', 'ip', 'type', 'model', 'plug_position', 'plug_device_id'],
    registry=registry
)

# gauge plug voltage reading
gauge_plug_voltage_mv = Gauge(
    'tapo_p304m_plug_voltage_mv', 
    'Tapo P304m plug voltage (in millivolt).', 
    ['device_id', 'hw_id', 'fw_ver', 'ip', 'type', 'model', 'plug_position', 'plug_device_id'],
    registry=registry
)

# gauge plug uptime
gauge_plug_on_time = Gauge(
    'tapo_p304m_plug_on_time', 
    'Tapo P304m plug uptime (in second).', 
    ['device_id', 'hw_id', 'fw_ver', 'ip', 'type', 'model', 'plug_position', 'plug_device_id'],
    registry=registry
)

# gauge plug power reading
gauge_plug_power_mw = Gauge(
    'tapo_p304m_plug_power_mw', 
    'Tapo P304m plug power used (in milliwatt).', 
    ['device_id', 'hw_id', 'fw_ver', 'ip', 'type', 'model', 'plug_position', 'plug_device_id'],
    registry=registry
)

# gauge plug energy reading
gauge_plug_total_wh = Gauge(
    'tapo_p304m_plug_total_wh', 
    'Tapo P304m plug energy used (in watt-hour).', 
    ['device_id', 'hw_id', 'fw_ver', 'ip', 'type', 'model', 'plug_position', 'plug_device_id'],
    registry=registry
)

# enum plug overcurrent status
enum_plug_overcurrent_status = Enum(
    'tapo_p304m_plug_overcurrent_status', 
    'Tapo P304m plug overcurrent status ( normal / abnormal )',
    states=['normal', 'abnormal'],
    labelnames=['device_id', 'hw_id', 'fw_ver', 'ip', 'type', 'model', 'plug_position', 'plug_device_id'],
    registry=registry
)

# enum plug overheat status
enum_plug_overheat_status = Enum(
    'tapo_p304m_plug_overheat_status', 
    'Tapo P304m plug overheat status ( normal / abnormal )',
    states=['normal', 'abnormal'],
    labelnames=['device_id', 'hw_id', 'fw_ver', 'ip', 'type', 'model', 'plug_position', 'plug_device_id'],
    registry=registry
)

# enum plug charging status
enum_plug_charging_status = Enum(
    'tapo_p304m_plug_charging_status', 
    'Tapo P304m plug charging status ( normal / abnormal )',
    states=['normal', 'abnormal'],
    labelnames=['device_id', 'hw_id', 'fw_ver', 'ip', 'type', 'model', 'plug_position', 'plug_device_id'],
    registry=registry
)

# enum plug status
enum_plug_device_on = Enum(
    'tapo_p304m_plug_device_on', 
    'Tapo P304m plug power status ( ON / OFF)',
    states=['ON','OFF'],
    labelnames=['device_id', 'hw_id', 'fw_ver', 'ip', 'type', 'model', 'plug_position', 'plug_device_id'],
    registry=registry
)


async def get_tapo_p304m_device_usage():
    """Get Tapo P304m device metrics"""
    device_usage = tapo_p304m.tapo_p304m_device_usage()
    await asyncio.sleep(1)
    return device_usage


async def update_tapo_p304m_device_usage_metrics():
    """Update Tapo P304m device metrics"""
    while True:
        device_usage_data = await get_tapo_p304m_device_usage()
        for key, value in device_usage_data.items():
            for period, amount in value.items():
                globals()[f'gauge_device_usage_{key}'].labels(**default_device_labels, period=period).set(amount)
        await asyncio.sleep(5)


async def get_tapo_p304m_plug_usage():
    """Update Tapo P304m plug metrics"""
    plugs = tapo_p304m.tapo_p304m_plugs()
    await asyncio.sleep(1)
    return plugs


async def update_tapo_p304m_plug_usage_metrics():
    """Update Tapo P304m device metrics"""
    while True:
        plugs_data = await get_tapo_p304m_plug_usage()
        
        for plug in plugs_data['child_device_list']:
            gauge_plug_current_ma.labels(**default_device_labels, plug_position=plug['position'], plug_device_id=plug['device_id']).set(plug['current_ma'])
            gauge_plug_voltage_mv.labels(**default_device_labels, plug_position=plug['position'], plug_device_id=plug['device_id']).set(plug['voltage_mv'])
            gauge_plug_on_time.labels(**default_device_labels, plug_position=plug['position'], plug_device_id=plug['device_id']).set(plug['on_time'])
            gauge_plug_power_mw.labels(**default_device_labels, plug_position=plug['position'], plug_device_id=plug['device_id']).set(plug['power_mw'])
            gauge_plug_total_wh.labels(**default_device_labels, plug_position=plug['position'], plug_device_id=plug['device_id']).set(plug['total_wh'])
            enum_plug_overcurrent_status.labels(**default_device_labels, plug_position=plug['position'], plug_device_id=plug['device_id']).state(plug['overcurrent_status'])
            enum_plug_overheat_status.labels(**default_device_labels, plug_position=plug['position'], plug_device_id=plug['device_id']).state(plug['overheat_status'])
            enum_plug_charging_status.labels(**default_device_labels, plug_position=plug['position'], plug_device_id=plug['device_id']).state(plug['charging_status'])
            enum_plug_device_on.labels(**default_device_labels, plug_position=plug['position'], plug_device_id=plug['device_id']).state(plug['device_on'])

        await asyncio.sleep(5)
        
def run_asyncio_loop(loop):
    """Run the asyncio event loop in a separate thread"""
    asyncio.set_event_loop(loop)
    loop.run_forever()


app = Flask(__name__)

app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/metrics': make_wsgi_app(registry)
})


@app.route('/')
def index():
    response = """<h1>Tapo P304M Exporter</h1>
    <p>Power Monitoring for Tapo P304M Smart Wi-Fi Power Strip</p>
    <p><a href="./metrics">Metrics</a></p>"""
    return response


if __name__ == '__main__':
    # Start the asyncio loop in a separate thread
    loop = asyncio.new_event_loop()
    threading.Thread(target=run_asyncio_loop, args=(loop,), daemon=True).start()

    # Schedule the update_metrics coroutine to run in the asyncio loop
    asyncio.run_coroutine_threadsafe(update_tapo_p304m_device_usage_metrics(), loop)
    asyncio.run_coroutine_threadsafe(update_tapo_p304m_plug_usage_metrics(), loop)
    
    # Development setting
    #app.run(host='0.0.0.0', port=8882)
    
    # Production setting 
    from waitress import serve
    serve(app, host="0.0.0.0", port=8882)
