import requests
import json
import logging

logger = logging.getLogger(__name__)


class PIDConfigException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class APIError(Exception):
    def __init__(self, jsonData: dict):

        details = jsonData["error"]["details"]
        errors = []
        for entry in details:
            entryDetails = details[entry]
            if "error" in entryDetails:
                error = entryDetails["error"]
                errors.append(f"Code: {error['code']}, Reason: {error['reason']}")
        self._error_messages = errors
        self.query = jsonData["error"]["query"]
        self.query_data = jsonData["error"]["query_data"]
        message = f"{jsonData['error']['name']}: {jsonData['error']['description']}, due to the following errors{''.join(errors)}"
        super().__init__(message)


def get_value_from_data_response(data: str, device: str, target: str):
    """
    This is a helper function to get the value from a data response.
    """
    if not data["data"][f"{device}.{target}"]["content"]["latest_valid_value"]["status"] == "SYNCHRONIZED":
        print("Warning: The obtained value is not synchronized!")
    return data["data"][f"{device}.{target}"]["content"]["latest_valid_value"]["value"]


def get_synchronization_status(data: str, device: str, target: str):
    """
    This is a helper function to get the synchronization status from a data response.
    """
    return data["data"][f"{device}.{target}"]["content"]["latest_valid_value"]["status"] == "SYNCHRONIZED"


class BlueFTController:
    def __init__(
        self,
        ip: str,
        mixing_chamber_channel_id: int,
        port: int = 49099,
        key: str = None,
    ):
        self.ip = ip
        self.key = key
        self.port = port
        self.mixing_chamber_channel_id = mixing_chamber_channel_id
        self.mixing_chamber_heater = "mapper.heater_mappings_bftc.device.sample"

    # general functions
    def _get_value_request(self, device: str, target: str):
        """
        Get the values currently in the Controller config for the given device
        """
        if self.key == None:
            raise PIDConfigException("No key provided for value request.")
        requestPath = f"https://{self.ip}:{self.port}/values/{device.replace('.','/')}/{target}/?prettyprint=1&key={self.key}"
        print(requestPath)
        response = requests.get(requestPath, verify=False)
        response.raise_for_status()
        # Potentially do some type of processing here, depending on what users want.
        return response.json()

    def _set_value_request(self, device: str, target: str, value: float):
        """
        Set a given target value for a given target device.
        """
        if self.key == None:
            raise PIDConfigException("No key provided for value request.")
        ## This is a two step process. First, we need to set the value and then we need to call the setter method.
        # This is the body for the setting request.
        request_body = {"data": {f"{device}.{target}": {"content": {"value": value}}}}
        requestPath = (
            f"https://{self.ip}:{self.port}/values/?prettyprint=1&key={self.key}"
        )
        response = requests.post(
            requestPath,
            data=json.dumps(request_body),
            headers={"Content-Type": "application/json"},
            verify=False
        )
        response.raise_for_status()
        return response.json()

    def _apply_values_request(self, device: str):
        """
        This method applies all changed values for the target device to the device.
        This is only necessary for some devices, such as the temperature controller,
        where the control unit does not have direct access to the device, but needs
        to update configurations
        """
        if self.key == None:
            raise PIDConfigException("No key provided for value request.")
        # Now we need to call the setter method.
        request_body = {"data": {f"{device}.write": {"content": {"call": 1}}}}
        requestPath = (
            f"https://{self.ip}:{self.port}/values/?prettyprint=1&key={self.key}"
        )
        response = requests.post(
            requestPath,
            data=json.dumps(request_body),
            headers={"Content-Type": "application/json"},
            verify=False
        )
        response.raise_for_status()

    def get_channel_data(self, channel: int, target_value: str):
        """
        Get the specified data from a given channel
        """
        device_id = f"mapper.heater_mappings_bftc.device.c{channel}"
        data = self._get_value_request(device_id, target_value)
        try:
            return get_value_from_data_response(data, device=device_id, target=target_value)
        except KeyError as e:
            raise APIError(data)

    def get_channel_temperature(self, channel: int) -> float:
        """
        Get the temperature of the given channel
        """
        return float(self.get_channel_data(channel, "temperature"))

    def get_channel_resistance(self, channel: int) -> float:
        """
        Get the temperature of the given channel
        """
        return float(self.get_channel_data(channel, "resistance"))

    def get_mxc_temperature(self) -> float:
        """
        Get the temperature of the mixing chamber sensor
        """
        return self.get_channel_temperature(self.mixing_chamber_channel_id)

    def get_mxc_resistance(self) -> float:
        """
        Get the resistance of the mixing chamber sensor
        """
        return self.get_channel_resistance(self.mixing_chamber_channel_id)

    def get_mxc_heater_value(self, target: str):
        """
        Get the value of the mixing chamber heater
        """
        data = self._get_value_request(self.mixing_chamber_heater, target)
        try:
            return get_value_from_data_response(data, device=self.mixing_chamber_heater, target=target)
        except KeyError as e:
            raise APIError(data)

    def check_heater_value_synced(self, target: str):
        """
        Check if the value of the mixing chamber heater is synced
        """
        data = self._get_value_request(self.mixing_chamber_heater, target)
        try:
            return get_synchronization_status(data, device=self.mixing_chamber_heater, target=target)
        except KeyError as e:
            raise APIError(data)

    def set_mxc_heater_value(self, target: str, value):
        """
        Set the value of the mixing chamber heater
        """
        # Set the value
        self._set_value_request(self.mixing_chamber_heater, target, value)
        # Apply the value (otherwise it doesn't get synced to the temperature controller)
        self._apply_values_request(self.mixing_chamber_heater)

        return self.check_heater_value_synced(target)

    def get_mxc_heater_status(self) -> bool:
        """
        Get the status of the mixing chamber heater
        """
        return self.get_mxc_heater_value("active") == "1"

    def set_mxc_heater_status(self, newStatus: bool) -> bool:
        """
        Get the status of the mixing chamber heater
        """
        newValue = "1" if newStatus else "0"
        return self.set_mxc_heater_value("active", newValue)

    def get_mxc_heater_power(self) -> float:
        """
        Get the power of the mixing chamber heater in microwatts
        """
        return float(self.get_mxc_heater_value("power")) * 1000.0

    def set_mxc_heater_power(self, power: float) -> bool:
        """
        Set the power of the mixing chamber heater
        The provided power is in microwatts
        """
        # Sanity check, should be in microwatts
        if power < 0 or power > 1000:
            raise PIDConfigException(
                "Power should be in the range of 0 to 1000 microwatts"
            )
        return self.set_mxc_heater_value("power", power / 1000000.0)

    def get_mxc_heater_setpoint(self) -> float:
        """
        Get the setpoint of the mixing chamber heater
        """
        return float(self.get_mxc_heater_value("setpoint"))

    def set_mxc_heater_setpoint(self, temperature: float) -> bool:
        """
        Set the setpoint of the mixing chamber heater in milli Kelvin
        temperature: float
        """
        return self.set_mxc_heater_value("setpoint", temperature / 1000.0)

    def get_mxc_heater_mode(self) -> bool:
        """
        Get the pid mode of the mixing chamber heater
        """
        return self.get_mxc_heater_value("pid_mode") == "1"

    def set_mxc_heater_mode(self, toggle: bool) -> bool:
        """
        Set the pid mode of the mixing chamber heater
        """
        newValue = "1" if toggle else "0"
        return self.set_mxc_heater_value("pid_mode", newValue)
