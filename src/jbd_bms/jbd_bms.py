#!/usr/bin/env python
# -*- coding: utf-8 -*-

from rcomponent.rcomponent import *

# Insert here general imports:
import serial
from serial import SerialException
from binascii import hexlify, unhexlify

# Insert here msg and srv imports:
from std_msgs.msg import String
from robotnik_msgs.msg import StringStamped, BatteryStatus

from std_srvs.srv import Trigger, TriggerResponse


class JbdBms(RComponent):
    """
    ROS package to communicate with the JBD Smart BMS
    """

    def __init__(self):

        RComponent.__init__(self)

        self.level = 0.0
        self.voltage = 0.0
        self.current = 0.0

        self.serial_device = serial.Serial(
            port= self.port,
            baudrate=9600,
            parity=serial.PARITY_NONE,
            stopbits=1,
            bytesize=8,
            timeout=0.1,
            xonxoff=False,
            dsrdtr=False,
            rtscts=False
        )

    def ros_read_params(self):
        """Gets params from param server"""
        RComponent.ros_read_params(self)

        self.port = rospy.get_param(
            '~port', '/dev/ttyUSB_JBD_BMS')

    def ros_setup(self):
        """Creates and inits ROS components"""

        RComponent.ros_setup(self)

        # Publisher
        self.status_pub = rospy.Publisher(
            '~status', String, queue_size=10)
        self.status_stamped_pub = rospy.Publisher(
            '~status_stamped', StringStamped, queue_size=10)
        self.data_pub = rospy.Publisher(
            '~data', BatteryStatus, queue_size=10)

        return 0

    def init_state(self):
        self.status = String()

        return RComponent.init_state(self)

    def ready_state(self):
        """Actions performed in ready state"""

        # Publish topic with status

        status_stamped = StringStamped()
        status_stamped.header.stamp = rospy.Time.now()
        status_stamped.string = self.status.data

        self.status_pub.publish(self.status)
        self.status_stamped_pub.publish(status_stamped)

        # Get battery values

        try:
            self.writeToSerialDevice("DDA50300FFFD77")
            rospy.sleep(0.1)
            line_read = str(self.readFromSerialDevice())
            hex_data = line_read.split("dd03001b")[1]
            self.voltage = self.twos_complement(hex_data[0:4]) / 100.0
            self.current = self.twos_complement(hex_data[4:8]) / 100.0
            self.level = self.twos_complement(hex_data[38:40])
        except Exception as e:
            rospy.logerr('%s::readyState: error reading BMS values: %s', rospy.get_name(), e)

        # Publish topic with data

        data = BatteryStatus()
        data.current = self.current
        data.voltage = self.voltage
        data.level = self.level
        if (self.current > 0.0):
            data.is_charging = True
        self.data_pub.publish(data)

        return RComponent.ready_state(self)

    def emergency_state(self):
        if(self.check_topics_health() == True):
            self.switch_to_state(State.READY_STATE)

    def shutdown(self):
        """Shutdowns device

        Return:
            0 : if it's performed successfully
            -1: if there's any problem or the component is running
        """

        return RComponent.shutdown(self)

    def switch_to_state(self, new_state):
        """Performs the change of state"""

        return RComponent.switch_to_state(self, new_state)

    def writeToSerialDevice(self, data):
        data_write = unhexlify(data)
        bytes_written = self.serial_device.write(data_write)
        return bytes_written

    def readFromSerialDevice(self):
        try:
            data_read = self.serial_device.read_all()
            return hexlify(data_read)
        except SerialException as e:
            rospy.logwarn(e)
            return

    def to_little_endian(self, val):
        little_hex = bytearray.fromhex(val)
        little_hex.reverse()
        str_little = ''.join(format(x, '02x') for x in little_hex)
        return str_little

    def twos_complement(self, hexval):
        bits = 16 # Number of bits in a hexadecimal number format
        val = int(hexval, bits)
        if val & (1 << (bits-1)):
            val -= 1 << bits
        return val
