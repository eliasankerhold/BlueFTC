import requests
from datetime import datetime, timedelta
import json
from logging import Formatter, FileHandler, StreamHandler, INFO, getLogger
import sys

simple_formatter = Formatter("%(levelname)s: %(message)s")
detailed_formatter = Formatter('[%(asctime)s] %(levelname)s - %(message)s')

file_handler = FileHandler(filename='BlueForsTemperatureController.log')
stdout_handler = StreamHandler(stream=sys.stdout)
file_handler.setLevel(INFO)
stdout_handler.setLevel(INFO)
file_handler.setFormatter(detailed_formatter)
stdout_handler.setFormatter(simple_formatter)

my_logger = getLogger(name='BlueForsTemperatureController Logger')
my_logger.addHandler(file_handler)
my_logger.addHandler(stdout_handler)
my_logger.setLevel(INFO)


class BlueFTController:
    def __init__(self, ip):
        self.ip = ip
        self.port = 5001
        self.httpiport = f"http://{self.ip}:{self.port}"
        self.channels = {}
        self.heaters = {}
        self.cycle_time = None
        self.time_delta = None

        self.update_heaters()
        self.update_channels()
        self.get_cycle_time()
        self.get_time_delta()

        self.log_info(f"Controller driver initialized.")

    # general functions

    @staticmethod
    def generic_request(path: str, payload: dict = None):

        if payload is None:
            response = requests.get(path)
        else:
            headers = {'Content-Type': 'application/json'}
            response = requests.post(path, data=json.dumps(payload), headers=headers)
        response.raise_for_status()

        return response.json()

    def make_time_str(self, dt: datetime, use_time_delta: bool = True):
        if use_time_delta:
            dt = dt - self.time_delta
        return dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    @staticmethod
    def log_info(msg: str):
        my_logger.info(msg=msg)

    @staticmethod
    def log_error(msg: str):
        my_logger.error(msg=msg)

    def _make_endpoint(self, *args):
        return self.httpiport + '/' + '/'.join(args)

    def _make_past_time_str(self, delta_seconds):
        return self.make_time_str(datetime.now() - timedelta(seconds=delta_seconds))

    def generic_toggle(self, status: str, endpoint: str, payload: dict):
        if status.lower() == 'on':
            toggle = True

        elif status.lower() == 'off':
            toggle = False

        else:
            raise NotImplementedError("Toggle status must be on or off.")

        payload['active'] = toggle
        self.generic_request(path=endpoint, payload=payload)

        return True

    # initialization

    def update_heaters(self):
        path = self._make_endpoint('heaters')
        response = self.generic_request(path=path)['data']

        for heater in response:
            self.heaters[heater['heater_nr']] = heater

    def update_channels(self):
        path = self._make_endpoint('channels')
        response = self.generic_request(path=path)['data']

        for channel in response:
            if channel['active']:
                self.channels[channel['channel_nr']] = channel

    def get_cycle_time(self):
        time = 0
        for c in self.channels.values():
            if c['active']:
                time += c['meas_time'] + c['wait_time']

        self.cycle_time = time

    def get_time_delta(self):
        path = self._make_endpoint('system')
        state_info = self.generic_request(path=path)
        controller_time = datetime.strptime(state_info['datetime'], '%Y-%m-%dT%H:%M:%S.%fZ')
        self.log_info(f"Current system time of controller: {controller_time}")

        self.time_delta = datetime.now() - controller_time

    def show_overview(self):
        print("\nHEATERS\n")
        for ind, heater in self.heaters.items():
            print("{:-^48s}".format(heater['name']))
            print(f"[Number]: {heater['heater_nr']}\n"
                  f"[Power (uW)]: {heater['power']}\n"
                  f"[Active]: {heater['active']}\n"
                  f"[PID]: {heater['control_algorithm_settings']}")

        print("\nTEMPERATURE CHANNELS\n")
        for ind, channel in self.channels.items():
            print("{:-^48s}".format(channel['name']))
            print(f"[Number]: {channel['channel_nr']}\n"
                  f"[Active]: {channel['active']}")
            coup_heat_ind = int(channel['coupled_heater_nr'])
            if coup_heat_ind != 0 and coup_heat_ind in self.heaters.keys():
                  print(f"[Coupled Heater]: {self.heaters[coup_heat_ind]['name']} (Number {coup_heat_ind})")
            else:
                print("[Coupled Heater]: Not coupled")

    # channel control

    def toggle_channel(self, channel_nr: int, status: str):
        endpoint = self._make_endpoint('channel', 'update')
        payload = {'channel_nr': channel_nr}
        if self.generic_toggle(status=status, payload=payload, endpoint=endpoint):
            self.log_info(f"Turned channel {channel_nr} ({self.channels[channel_nr]['name']}) {status.lower()}.")

        self.update_channels()

    def get_channel_temps_in_time(self, channel_nr, time_seconds):
        path = self._make_endpoint('channel', 'historical-data')
        payload = {
            'start_time': self._make_past_time_str(time_seconds),
            'stop_time': self.make_time_str(datetime.now()),
            'channel_nr': channel_nr,
            'fields': ['temperature', 'timestamp']
        }
        meas = self.generic_request(path, payload)
        d = [datetime.fromtimestamp(ts) for ts in meas['measurements']['timestamp']]
        temps = [t for t in meas['measurements']['temperature']]

        return {'temperature': temps, 'timestamp': d}

    def get_latest_channel_temp(self, channel_nr):
        data = self.get_channel_temps_in_time(channel_nr, self.cycle_time * 2)
        try:
            return data['temperature'][-1], data['timestamp'][-1]
        except IndexError as ex:
            self.log_error(str(ex) + f'Returned value: {data}')

    # heater control

    def toggle_heater(self, heater_nr: int, status: str):
        endpoint = self._make_endpoint('heater', 'update')
        payload = {'heater_nr': heater_nr}
        if self.generic_toggle(status=status, payload=payload, endpoint=endpoint):
            self.log_info(f"Turned heater {heater_nr} ({self.heaters[heater_nr]['name']}) {status.lower()}.")

        self.update_heaters()

    def set_heater_power(self, heater_nr, setpower: float):
        path = self._make_endpoint('heater', 'update')
        payload = {
            'heater_nr': heater_nr,
            'power': setpower * 1e-6
        }
        self.generic_request(path, payload)
        self.log_info(f"Set heater {heater_nr} to {setpower} uW.")

        self.update_heaters()

    def get_heater_power(self, heater_nr):
        path = self._make_endpoint('heater')
        payload = {
            'heater_nr': heater_nr,
        }
        answer = self.generic_request(path, payload)
        return answer['power'] * 1e6
