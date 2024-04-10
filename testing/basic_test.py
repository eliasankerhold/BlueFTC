from blueftc.BlueforsController import BlueFTController
from credentials import server_ip, api_key

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

controller = BlueFTController(ip=server_ip, mixing_chamber_channel_id=6, key=api_key, debug=True, port=49098)

active_channels = [1, 2, 5, 6, 8]

for ch in active_channels:
	print(f"Channel {ch} temp: {controller.get_channel_temperature(ch)} Kelvin")
	print(f"Channel {ch} resistance: {controller.get_channel_resistance(ch)} Ohm")

print(f"MXC heater status: {controller.get_mxc_heater_status()}")
print(f"MXC heater power: {controller.get_mxc_heater_power()} uW")
print(f"MXC heater PID: {controller.get_mxc_heater_mode()}")
print(f"MXC heater setpoint: {controller.get_mxc_heater_setpoint()} K")