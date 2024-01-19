<a name="readme-top"></a>

<div align="center">
  <h3 align="center">BlueFTC</h3>

  <p align="center">
    A simple Python interface for Bluefors cryostat temperature controllers.
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#installation">Installation</a></li>
        <li><a href="#basic-usage">Basic Usage</a></li>
      </ul>
    </li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

The control software for Bluefors cryostat and their temperature controller does not come with a native Python interface. At the same time, Python is widely used as a measurement scripting language among users of Bluefors devices. This driver uses HTTP GET/POST commands to remotely read and write to a temperature controller within the same local network. A command history is automatically logged to file. 

*It does not yet make use of the latest update of the Bluefors control software, which integrates the temperature control into the main cryostat control.*

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- GETTING STARTED -->
## Getting Started

The package is not yet uploaded on PyPi, but can be installed through ``pip``. Only native Python libraries are used, there are no external dependencies.

<!-- INSTALLATION -->
### Installation

To install the package, navigate to its root folder, i.e. where ``pyproject.toml`` is located, and install it using pip:
   ```shell
   python -m pip install .
   ```

<!-- BASIC USAGE -->
### Basic Usage

Once installed, the package can be easily integrated into measurement scripts.

```python
# import 
from blueftc.BlueFTController import BlueFTController

# create controller object
tcontrol = BlueFTController(ip="YOUR_IP_HERE")

# show basic information
tcontrol.show_overview()

# HEATER CONTROL
# set and get heater power in uW
tcontrol.set_heater_power(heater_nr=1, setpower=100)
power = tcontrol.get_heater_power(heater_nr=1)
print(power)

# turn heater on or off
tcontrol.toggle_heater(heater_nr=1, status='on')
tcontrol.toggle_heater(heater_nr=1, status='off')

# TEMPERATURE CHANNEL CONTROL
# get latest temperature in Kelvin
temp = tcontrol.get_latest_channel_temp(channel_nr=1)
print(temp)

# get all temperatures in last hour
temps = tcontrol.get_channel_temps_in_time(channel_nr=1, time_seconds=3600)
print(temps['temperature'])
print(temps['timestamp'])

# turn channel on or off
tcontrol.toggle_channel(channel_nr=1, status='on')
```

*The internal clock of the temperature controller deviates over time and is usually not synced with a timeserver. If the Python 
control script is running for an extented period of time, the time interval provided in the function ``get_channel_temps_in_time`` may become imprecise.
In this case, it is advised to call the function ``get_time_delta`` to recompute the time difference between system times
of the controller and the host computer.*

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ROADMAP -->
## Roadmap

- [ ] Write proper documentation
- [ ] Update to latest version of Bluefors control software
- [ ] Improve Error Handling
- [ ] Upload to PyPi

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- CONTACT -->
## Contact

Elias Ankerhold - elias.ankerhold[at].aalto.fi

<p align="right">(<a href="#readme-top">back to top</a>)</p>