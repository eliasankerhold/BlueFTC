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
        <li><a href="#usage-in-matlab">Usage in Matlab</a></li>
      </ul>
    </li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->

## About The Project

The control software for Bluefors cryostat and their temperature controller does not come with a native Python interface. At the same time, Python is widely used as a measurement scripting language among users of Bluefors devices. This driver uses HTTP GET/POST commands to remotely read and write to a controller using the control Software's API.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- GETTING STARTED -->

## Getting Started

The package is not yet uploaded on PyPi, but can be installed through `pip`. Only native Python libraries are used, there are no external dependencies.

<!-- INSTALLATION -->

### Installation

To install the package, navigate to its root folder, i.e. where `pyproject.toml` is located, and install it using pip:

```shell
python -m pip install .
```

<!-- BASIC USAGE -->

### Basic Usage

Once installed, the package can be easily integrated into measurement scripts.

```python
# import
from blueftc.BlueFTController import BlueforsController

# create controller object
# TODO: setup via config file
tcontrol = BlueFTController(ip="YOUR_IP_HERE")

# show basic information
tcontrol.show_overview()

# HEATER CONTROL
# set and get heater power in uW
tcontrol.set_mxc_heater_power(setpower=100)
power = tcontrol.get_mxc_heater_power()
print(power)

# turn heater on or off
tcontrol.toggle_mxc_heater(status='on')
tcontrol.toggle_mxc_heater(status='off')
#

# TEMPERATURE CHANNEL CONTROL
# get latest temperature in Kelvin
temp = tcontrol.get_mxc_temperature()
print(temp)

```

<!-- USAGE IN MATLAB -->

### Usage in Matlab

The controller can also be used from matlab:

```matlab
tcontrol = py.blueftc.BlueforsController(ip="YOUR_IP_HERE")
```

<!-- ROADMAP -->

## Roadmap

- [ ] Write proper documentation
- [x] Update to latest version of Bluefors control software
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
Thomas Pfau - thomas.pfau[at].aalto.fi

<p align="right">(<a href="#readme-top">back to top</a>)</p>
