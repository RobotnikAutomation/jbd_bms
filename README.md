# jbd_bms

ROS2 package to communicate with the JBD Smart Battery Management System (BMS). This package is  transforms readings from a serial port of JBD BMS to ROS2 messages using robotnik_msgs.

## Features

- Communicates with JBD Smart BMS via serial port
- Publishes battery status information using robotnik_msgs
- Configurable publishing frequency and serial port
- Supports ROS2 Humble and superior versions

## Prerequisites

- ROS2 (Humble or newer)
- Python 3.6+
- robotnik_msgs package
- pyserial

## Installation

1. Clone this repository into your ROS2 workspace:

```bash
cd ~/ros2_ws/src
git clone -b ros2-devel https://github.com/RobotnikAutomation/jbd_bms.git
```

2. Install the robotnik_msgs package:

```bash
git clone -b ros2-devel https://github.com/RobotnikAutomation/robotnik_msgs.git
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

- `~/data` (robotnik_msgs/BatteryStatus): Publishes the BMS information.

## License

This project is licensed under the BSD 3-Clause License. See the [LICENSE](LICENSE) file for details.

## Authors

- José Gómez <jgomez@robotnik.es>
- Guillem Gari <ggari@robotnik.es>

## Contributing

Contributions to improve this driver are welcome. Please follow the standard fork-and-pull request workflow.

## Support

For any questions or issues, please open an issue on this repository or contact the maintainers.
