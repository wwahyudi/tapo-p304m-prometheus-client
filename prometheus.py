"""# prometheus.py"""
import asyncio
import threading
import os
import sys
import logging
from flask import Flask
from prometheus_client import make_wsgi_app, CollectorRegistry, Gauge, Enum
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from tapo_p304m import TapoP304m

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# Ensure required environment variables are set
REQUIRED_ENV_VARS = ["TAPO_USERNAME", "TAPO_PASSWORD", "TAPO_IP_ADDRESS"]
missing_vars = [var for var in REQUIRED_ENV_VARS if not os.environ.get(var)]
if missing_vars:
    log.error("Missing required environment variable(s): %s", ", ".join(missing_vars))
    sys.exit(1)


# Load environment variables
TAPO_USERNAME   = os.environ.get('TAPO_USERNAME')
TAPO_PASSWORD   = os.environ.get('TAPO_PASSWORD')
TAPO_IP_ADDRESS = os.environ.get('TAPO_IP_ADDRESS')

log.info("All required environment variables are set. Starting up..")

tapo_p304m = TapoP304m(TAPO_IP_ADDRESS, TAPO_USERNAME, TAPO_PASSWORD)
try:
    device_info = tapo_p304m.tapo_p304m_device_info()
    log.info("Device info retrieved: %s", device_info)
except Exception as e:
    log.exception("Failed to get device info: %s", e)
    sys.exit(1)

DEFAULT_LABELS = ['device_id', 'hw_id', 'fw_ver', 'ip', 'type', 'model']
default_device_labels = {k: device_info[k] for k in DEFAULT_LABELS}

print("default_device_labels", default_device_labels)

PLUG_LABELS = DEFAULT_LABELS + ['plug_position', 'plug_device_id', 'plug_nickname']

# Create a Prometheus registry
registry = CollectorRegistry()

# Device Usage Gauges
device_gauges = {
    'power_usage': Gauge(
        'tapo_p304m_device_usage_power_usage',
        'Device power usage (in mW)', DEFAULT_LABELS + ['period'], registry=registry),
    'saved_power': Gauge(
        'tapo_p304m_device_usage_saved_power',
        'Device saved power (in mW)', DEFAULT_LABELS + ['period'], registry=registry),
    'time_usage': Gauge(
        'tapo_p304m_device_usage_time_usage',
        'Device time usage (in sec)', DEFAULT_LABELS + ['period'], registry=registry)
}

# Plug Gauges
plug_gauges = {
    'current_ma': Gauge(
        'tapo_p304m_plug_current_ma',
        'Plug current (in mA)', PLUG_LABELS, registry=registry),
    'voltage_mv': Gauge(
        'tapo_p304m_plug_voltage_mv',
        'Plug voltage (in mV)', PLUG_LABELS, registry=registry),
    'on_time': Gauge(
        'tapo_p304m_plug_on_time',
        'Plug uptime (in sec)', PLUG_LABELS, registry=registry),
    'power_mw': Gauge(
        'tapo_p304m_plug_power_mw',
        'Plug power used (in mW)', PLUG_LABELS, registry=registry),
    'total_wh': Gauge(
        'tapo_p304m_plug_total_wh',
        'Plug energy used (in Wh)', PLUG_LABELS, registry=registry)
}

# Plug Enums
plug_enums = {
    'overcurrent_status': Enum(
        'tapo_p304m_plug_overcurrent_status',
        'Plug overcurrent status', states=['normal', 'abnormal'],
        labelnames=PLUG_LABELS, registry=registry),
    'overheat_status': Enum(
        'tapo_p304m_plug_overheat_status',
        'Plug overheat status', states=['normal', 'abnormal'],
        labelnames=PLUG_LABELS, registry=registry),
    'charging_status': Enum(
        'tapo_p304m_plug_charging_status',
        'Plug charging status', states=['normal', 'abnormal'],
        labelnames=PLUG_LABELS, registry=registry),
    'device_on': Enum(
        'tapo_p304m_plug_device_on',
        'Plug power status', states=['ON', 'OFF'],
        labelnames=PLUG_LABELS, registry=registry)
}

# --- Metrics Updater Tasks ---

async def update_device_usage_metrics():
    """Update device usage metrics periodically."""
    while True:
        try:
            device_usage = tapo_p304m.tapo_p304m_device_usage()
            for metric, gauge in device_gauges.items():
                values = device_usage.get(metric, {})
                for period, value in values.items():
                    gauge.labels(**default_device_labels, period=period).set(value)
            log.debug("Device usage metrics updated successfully")
        except Exception as e:
            log.error("Device usage update failed: %s", e, exc_info=True)
        await asyncio.sleep(5)

async def update_plug_metrics():
    """Update plug metrics periodically."""
    while True:
        try:
            plugs = tapo_p304m.tapo_p304m_plugs()
            count = 0
            for plug in plugs.get('child_device_list', []):
                label_args = dict(
                    default_device_labels,
                    plug_position=plug['position'],
                    plug_device_id=plug['device_id'],
                    plug_nickname=plug['nickname']
                )
                # Gauges
                plug_gauges['current_ma'].labels(**label_args).set(plug['current_ma'])
                plug_gauges['voltage_mv'].labels(**label_args).set(plug['voltage_mv'])
                plug_gauges['on_time'].labels(**label_args).set(plug['on_time'])
                plug_gauges['power_mw'].labels(**label_args).set(plug['power_mw'])
                plug_gauges['total_wh'].labels(**label_args).set(plug['total_wh'])
                # Enums
                plug_enums['overcurrent_status'].labels(**label_args).state(plug['overcurrent_status'])
                plug_enums['overheat_status'].labels(**label_args).state(plug['overheat_status'])
                plug_enums['charging_status'].labels(**label_args).state(plug['charging_status'])
                plug_enums['device_on'].labels(**label_args).state(plug['device_on'])
                count += 1
            log.debug("Plug metrics updated for %d plugs.", count)
        except Exception as e:
            log.error("Plug usage update failed: %s", e, exc_info=True)
        await asyncio.sleep(5)

def start_background_tasks(loop):
    asyncio.set_event_loop(loop)
    loop.create_task(update_device_usage_metrics())
    loop.create_task(update_plug_metrics())
    log.info("Background metric updater tasks started")
    loop.run_forever()

# --- Flask App & Dispatcher ---
app = Flask(__name__)
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/metrics': make_wsgi_app(registry)
})

@app.route('/')
def index():
    return (
        "<h1>Tapo P304M Exporter</h1>"
        "<p>Power Monitoring for Tapo P304M Smart Wi-Fi Power Strip</p>"
        '<p><a href="./metrics">Metrics</a></p>'
    )

if __name__ == '__main__':
    # Start asyncio loop in a background thread
    loop = asyncio.new_event_loop()
    threading.Thread(target=start_background_tasks, args=(loop,), daemon=True).start()
    log.info("Starting Waitress HTTP server on 0.0.0.0:8882")
    # Serve app
    from waitress import serve
    serve(app, host="0.0.0.0", port=8882)
