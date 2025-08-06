# jbd_bms

ROS2 package to communicate with the JBD Smart Battery Management System (BMS). This package is  transforms readings from a serial port of JBD BMS to ROS2 messages using robotnik_interfaces.

## Features

- Communicates with JBD Smart BMS via serial port
- Publishes battery status information using robotnik_interfaces
- Configurable publishing frequency and serial port
- Supports ROS2 Humble and superior versions

## Prerequisites

- ROS2 (Humble or newer)
- Python 3.6+
- robotnik_interfaces package
- pyserial

## Installation

1. Clone this repository into your ROS2 workspace:

```bash
cd ~/ros2_ws/src
git clone -b ros2-devel https://github.com/RobotnikAutomation/jbd_bms.git
```

2. Install the robotnik_interfaces package:

```bash
git clone -b ros2-devel https://github.com/RobotnikAutomation/robotnik_interfaces.git
```

3. Install dependencies:

```bash
cd ~/ros2_ws
rosdep install --from-paths src --ignore-src -r -y
```

4. Build the workspace:

```bash
colcon build
```

5. Source the setup file:

```bash
source ~/ros2_ws/install/setup.bash
```

6. Set up udev rules:

Copy the `rules/47-jbd-bms.rules` file into the `/etc/udev/rules.d/` folder, modifying the serial number to match your device:

```bash
sudo cp ~/ros2_ws/src/jbd_bms/rules/47-jbd-bms.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
```

## Usage

Launch the jbd_bms node:

```bash
ros2 launch jbd_bms jbd_bms.launch.xml
```

### Parameters

- `port` (String, default: /dev/ttyUSB_BMS): Port name of the BMS serial USB connection.
- `publish_freq` (Float, default: 2.0): Desired publishing frequency in Hz.
- `node_name` (String, default: battery_estimator): Name of the ROS2 node.
- `robot_id` (String, default: robot): Namespace for the node.
- `log_level` (String, default: INFO): Logging level for the node.

### Published Topics

- `~/data` (robotnik_battery_msgs/msg/BatteryStatus): Publishes the BMS information.

## Containers

### Setup the containers
The container setup is controlled by the [`setup-container.yaml`](./setup-container.yaml) file. This file contains essential variables for creating the required Docker image files. Review and edit this file as needed before proceeding with the setup.

```yaml
---
images:
  version: devel
  sites:
    local: docker-hub
    # local: robotnik

ros:
  general:
    distro: humble
    domain_id: 50
    robot_id: robot
    log_level: INFO
  bms:
    port: /dev/ttyUSB_BMS
```

#### Key Configuration Parameters

- `images.version`: Specifies the version tag for the Docker image.
- `images.sites`: Defines the Docker registry locations for local environment. (Options are `docker-hub` or `robotnik`)
- `ros.general`: Contains ROS 2 specific configurations, including the distribution and robot settings.
- `ros.bms`: Specifies hardware-related settings, such as the BMS port.

#### Creating Container Files

To create the container files use the following command
```bash
setup-container/scripts/setup.sh
```
This script will process the `setup-container.yaml` file and create all required Docker-related files in the appropriate directories.

### Create Container
To build the container, navigate to the builder directory and use Docker Compose. This step compiles the necessary images based on the Dockerfile provided in the directory.
```bash
cd container/builder
docker compose build
```
### Run in container
To run the Daly BMS application inside a Docker container, execute the following commands. This will start the container in detached mode, allowing the application to run in the background.
```bash
cd container/run
docker compose up -d
```
### Debug in container
For debugging purposes, you can access the container's shell. This allows you to interact with the application directly, inspect logs, and troubleshoot issues. the source is mounted on your container and you can edit with your favourite ide.
```bash
cd container/debug
docker compose up -d
docker compose exec bms bash
```

### Obtaining DEB Files
To generate Debian packages:
```bash
cd container/debs
docker compose up --build
```

### Pass unitary tests
To run the unitary tests:
```bash
cd container/test
docker compose build
```

## License

This project is licensed under the BSD 3-Clause License. See the [LICENSE](LICENSE) file for details.

## Authors

- José Gómez <jgomez@robotnik.es>
- Guillem Gari <ggari@robotnik.es>

## Contributing

Contributions to improve this driver are welcome. Please follow the standard fork-and-pull request workflow.

## Support

For any questions or issues, please open an issue on this repository or contact the maintainers.
