<a name="readme-top"></a>

<div align="center">
  <h1 align="center">BlueFTC</h1>

  <p align="center">
    A simple Python interface for temperature controllers of Bluefors cryostats..
  </p>
</div>

<!-- TABLE OF CONTENTS -->
## Table of Contents
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#installation">Installation</a></li>
        <li><a href="#quick-start-to-read-mixing-chamber-temperature">Quick Start To Read Mixing Chamber Temperature</a></li>
        <li><a href="#full-usage">Full Usage</a></li>
      </ul>
    </li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>

<!-- ABOUT THE PROJECT -->

## About The Project

The control software for Bluefors cryostat and their temperature controller does not come with a native Python interface. At the same time, Python is widely used as a measurement scripting language among users of Bluefors devices. This driver uses HTTP GET/POST commands within a local network to remotely read and write to a temperature controller using the Bluefors control software's API.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- GETTING STARTED -->

## Getting Started
In the scope of this package, the Bluefors control software API can only be accessed through a local network. Therefore, the measurement computer needs to be part of the same local network as the machine which is running the Bluefors control software and has a direct connection to the cryostat controller.

Next to the local IP address of the server (i.e. the machine running the control software) and the correct port number, an API key is required. It can be created in the Bluefors control software, configured with the required permissions and distributed to users.

<!-- INSTALLATION -->

### Installation

The package can be installed through `pip`. Only native Python libraries are used, there are no external dependencies.
To install the package, activate the desired virtual environment if using one, navigate to the package root folder, i.e. where `pyproject.toml` is located, and install it using pip:

```shell
python -m pip install .
```

<!-- QUICK START TO READ MIXING CHAMBER TEMPERATURE -->

### Quick Start To Read Mixing Chamber Temperature

Make sure the package is installed in the current Python environment!

```python
# import
from blueftc.BlueFTController import BlueforsController

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# define required configuration
API_KEY = '123456789abcdefghijklmnopqrstuvwxyz'
IP_ADDRESS = '123.456.789.0'
PORT_NUMBER = 12345
MXC_ID = 6

# create controller object
controller = BlueFTController(ip=IP_ADDRESS, port=PORT_NUMBER, key=API_KEY, 
                              mixing_chamber_channel_id=MXC_ID)

# read mixing chamber temperature in Kelvin
mxc_temp = controller.get_mxc_temperature()
```

<!-- FULL USAGE -->

### Full Usage

Once installed, the package can be easily integrated into measurement scripts. To initiate a connection to the control software running on the host machine, it is required to provide its IP address, port number and an API key equipped with the required permissions. For convenience, the ID of the mixing chamber thermometer  used by the control software should be defined as well.

To improve security and avoid redundant variable definitions across multiple measurement scripts, is strongly advised to store the IP address, port number and API key in a separate file and import them at the beginning of the measurement program. The ID of the mixing chamber thermometer shall be treated equally.

**A minimal working example of read commands can be found in the `examples` directory.**

Create a file `credentials.py` with the required configuration:

```python
API_KEY = '123456789abcdefghijklmnopqrstuvwxyz'
IP_ADDRESS = '123.456.789.0'
PORT_NUMBER = 12345
MXC_ID = 6

```

After importing the IP and API key, an instance of the BlueforsController class can be initialized and used to read/write data from/to the temperature controller:

```python
# import
from blueftc.BlueFTController import BlueforsController
from credentials import API_KEY, IP_ADDRESS, PORT_NUMBER, MXC_ID

# -------- OPTIONAL --------
'''
The requests package used to handle HTTP communication warns about an insecure connection if 
no HTTPS connection can established. To prevent cluttering of console outputs and log files, 
it is advisable to disable the respective warning.
'''
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
# --------------------------

# create controller object
controller = BlueFTController(ip=IP_ADDRESS, port=PORT_NUMBER, key=API_KEY, 
                              mixing_chamber_channel_id=MXC_ID)

# -------- READ OPERATIONS --------
'''
The following commands only require an API key with read permissions and are always safe 
to execute.
'''

# read mixing chamber temperature, in Kelvin
mxc_temp = controller.get_mxc_temperature()

# read temperature of arbitrary channel by supplying the corresponding channel ID, in Kelvin
temp = controller.get_channel_temperature(channel=1)

# read resistance of mixing chamber sensor or arbitrary channel, in Ohm
mxc_res = controller.get_mxc_resistance()
res = controller.get_channel_resistance(channel=1)

# check if the mixing chamber heater is turned or off
mxc_heater_status = controller.get_mxc_heater_status()

# read power of mixing chamber heater, in microwatts
mxc_power = controller.get_mxc_heater_power()

# check if the mixing chamber heater is operating in manual (0) or PID (1) mode
mxc_mode = controller.get_mxc_heater_mode()

# read the temperature setpoint of the mixing chamber heater PID control, in Kelvin
mxc_setpoint = controller.get_mxc_heater_setpoint()
# ------------------------

# -------- WRITE OPERATIONS --------
'''
These commands require an API key with read and write permission and can potentially cause 
substantial damage to the hardware. Only execute with caution and absolute certainty of 
what is going to happen!

All write commands return True if executed successfully, otherwise False.
'''

# toggle mixing chamber heater
status = controller.toggle_mxc_heater('off')

# set power of the mixing chamber heater, in microwatts
status = controller.set_mxc_heater_power(100)

# set the set point of the mixing chamber PID control, in millikelvin
status = controller.set_mxc_heater_setpoint(30)

# turn the mixing chamber PID control on (True) or off (False)
status = controller.set_mxc_heater_mode(True)

# ---------------------------------

```

<!-- ROADMAP -->

## Roadmap

- [ ] Write proper documentation
- [x] Update to latest version of Bluefors control software
- [ ] Improve Error Handling
- [ ] Upload to PyPi
- [x] Logging

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- LICENSE -->

## License

Distributed under the GNU GPLv3 License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTACT -->

## Contact

Elias Ankerhold - elias.ankerhold[at].aalto.fi <br>
Thomas Pfau - thomas.pfau[at].aalto.fi

<p align="right">(<a href="#readme-top">back to top</a>)</p>
