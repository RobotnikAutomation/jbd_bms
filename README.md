# jbd_bms

The jbd_bms package, based on RComponent structure. ROS package to communicate with the JBD Smart BMS

## Installation

Copy the rules/47-jbd-bms.rules file into the /etc/udev/rules.d folder, modifying the serial number.

## 1 jbd_bms_node

Node that allows to communicate with the JBD Smart BMS

### 1.1 Parameters

* ~port (String, default: /dev/ttyUSB_JBD_BMS)
   port name of the BMS serial USB connection.

### 1.2 Published Topics

* ~/data (robotnik_msgs/BatteryStatus)
  publishes the BMS information

### 1.3 Bringup

```bash
roslaunch jbd_bms jbd_bms.launch
```
