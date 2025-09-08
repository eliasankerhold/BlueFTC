from blueftc.BlueforsController import BlueFTController
from credentials import IP_ADDRESS, PORT_NUMBER, API_KEY, MXC_ID, HEATER_ID

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

controller = BlueFTController(ip=IP_ADDRESS, port=PORT_NUMBER, key=API_KEY, mixing_chamber_channel_id=MXC_ID, mixing_chamber_heater_id=HEATER_ID)

active_channels = [1, 2, 5, 6, 8]

for ch in active_channels:
	print(f"Channel {ch} temp: {controller.get_channel_temperature(ch)} Kelvin")
	print(f"Channel {ch} resistance: {controller.get_channel_resistance(ch)} Ohm")

print(f"MXC heater status: {controller.get_mxc_heater_status()}")
print(f"MXC heater power: {controller.get_mxc_heater_power()} uW")
print(f"MXC heater PID: {controller.get_mxc_heater_mode()}")
print(f"MXC heater setpoint: {controller.get_mxc_heater_setpoint()} K")
print(f"MXC heater PID config: {controller.get_mxc_heater_pid_config()}")