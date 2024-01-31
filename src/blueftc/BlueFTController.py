import requests
from datetime import datetime, timedelta
import json
from logging import Formatter, FileHandler, StreamHandler, INFO, getLogger
import sys
import numpy as np

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


class PIDConfigException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class BlueFTController:
    def __init__(self, ip: str, pid_config: str = None, test_mode: bool = False):
        self.ip = ip
        self.port = 5001
        self.http_ip_port = f"http://{self.ip}:{self.port}"
        self.channels = {}
        self.heaters = {}
        self.cycle_time = None
        self.time_delta = None
        self.log_prefix = f'BlueFors Temperature Controller at {self.ip}: '

        self.test_mode = test_mode

        self.pif_config_path = pid_config
        self.pid_mode_available = False
        self.pid_config = None

        if pid_config is not None:
            self._read_pid_config()
        self.update_heaters()
        self.update_channels()
        self.get_cycle_time()
        self.get_time_delta()
        self.show_overview()

        self.log_info(f"Controller driver initialized.")

    # general functions

    def generic_request(self, path: str, payload: dict = None):

        if self.test_mode:
            print(f"Virtual request sent to {path} with payload {payload}.")
            return None

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

    def log_info(self, msg: str):
        my_logger.info(msg=self.log_prefix + msg)

    def log_error(self, msg: str):
        my_logger.error(msg=self.log_prefix + msg)

    def _make_endpoint(self, *args):
        return self.http_ip_port + '/' + '/'.join(args)

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

    def print_pid_config(self):
        if self.pid_mode_available:
            print("Upper Temp Limit (K) |        P        |        I        |        D        |     Maximum Power (mW)")
            for config in self.pid_config:
                print(
                    f'{config[0]: 20.3f} | {config[1]: 15.3f} | {config[2]: 15.3f} | {config[3]: 15.3f} | {config[4]: 16.6f}')

    def _pid_sanity_checks(self):
        if self.pid_config.shape[1] != 5:
            raise PIDConfigException(f"Unexpected input shape. Expected (n, 5), received {self.pid_config.shape}")

        for i, upper_limit in enumerate(self.pid_config[1:, 0]):
            if upper_limit <= self.pid_config[i, 0]:
                raise PIDConfigException(f"PID temperature ranges are overlapping or inconsistently sorted. "
                                         f"Problematic limits: {self.pid_config[i, 0]}, {upper_limit}")

    def _read_pid_config(self):
        try:
            self.pid_config = np.loadtxt(self.pif_config_path, skiprows=1, delimiter=',')
            self._pid_sanity_checks()
            self.pid_mode_available = True
            self.log_info("Read PID parameters from file. PID mode available.")
            self.print_pid_config()

        except (FileNotFoundError, PIDConfigException, ValueError) as ex:
            self.log_error(f"Error while reading PID config: {ex}. PID mode not available!")

    def _find_pid_param_by_range(self, target_temperature: float):
        for config in self.pid_config:
            if target_temperature <= config[0]:
                return config[1:]

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
            'power': setpower * 1e-6,
            'pid_mode': 0
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

    def set_pid_temperature(self, heater_nr, temp):
        config = self._find_pid_param_by_range(target_temperature=temp)
        path = self._make_endpoint('heater')
        payload = {
            'heater_nr': heater_nr,
            'pid_mode': 1,
            'max_power': config[4],
            'control_algorithm_settings': {'proportional': config[1],
                                           'integral': config[2],
                                           'derivative': config[3]},
            'setpoint': temp
        }

        self.generic_request(path, payload)

        self.update_heaters()
        self.log_info(f'Changed PID parameters: {payload}.')
