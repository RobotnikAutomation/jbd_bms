# Copyright 2024 Robotnik Automation S.L.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#    * Neither the name of the copyright holder nor the names of its
#      contributors may be used to endorse or promote products derived from
#      this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# @maintanier Guillem Gari  <ggari@robotnik.es> Robotnik Automation S.L.


"""
Module for managing and communicating with Jbd Battery Management System (BMS).

This module defines the JBD SMART BMS class that handles serial communication,
data processing, and publishing of battery status information to ROS 2 topics.
It also includes utility functions and dataclasses for managing serial
configuration and battery data.

Classes
-------
JbdBMSROS2
    Main class for managing the Jbd BMS for ROS2.
"""

# import statistics

from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy

from robotnik_msgs.msg import BatteryStatus
from .jbd_bms import JbdBMS
from .utils import copy_dataclass_to_ros_message


FREQUENCY = 2.0
PORT = "/dev/ttyUSB_BMS"


class JbdBMSROS2(Node):
    """
    ROS2 Node for interfacing with the Jbd Battery Management System.

    This class extends the ROS2 Node class to provide a complete interface
    for the Jbd BMS. It handles parameter reading, data retrieval, processing,
    and publishing of battery status and raw data.

    Attributes
    ----------
    _battery_data : BatteryStatus
        Object to store battery data.
    _publisher_status : Publisher
        Publisher for battery status.
    _publish_freq : None
        Publisher frecuency.
    _port : str
        Serial port for BMS communication.
    _jbd : JbdBMS
        Interface to the Jbd BMS.
    timer_ : Timer
        ROS2 timer for periodic data reading and publishing.


    Methods
    -------
    ros_read_params()
        Read ROS2 parameters for configuration.
    ros_setup()
        Set up ROS2 publishers and timers.
    setup()
        Perform complete setup of the node and BMS communication.
    read()
        Retrieve and process data from the BMS.
    ros_publish()
        Publish battery status to ROS2 topics.
    """

    def __init__(self):
        """
        Initialize the JbdBMSROS2 object.

        This constructor sets up the initial state of the JbdBMSROS2 object,
        including battery status, publishers, and serial communication.
        """
        super().__init__('battery_estimator')
        self._battery_data = BatteryStatus()
        self._publisher_status = None
        self._publish_freq = None
        self._port = None
        self._jbd = JbdBMS(logger=self.get_logger())
        self._timer = None
        print("Node started", flush=True)

    def ros_read_params(self):
        """
        Read ROS parameters for the JbdBMS.

        This method declares and retrieves the 'serial_port' and 'publish_freq'
        parameters, setting default values if not provided.

        Raises
        ------
        AssertionError
            If the parameters are not of the expected type.
        """
        def declare_and_get_param(
            param,
            default_value,
            description,
            unit,
            param_type
        ):
            """
            Declare and retrieve a parameter, with logging and type checking.

            Parameters
            ----------
            param : str
                The name of the parameter.
            default_value : Any
                The default value for the parameter.
            description : str
                A description of the parameter.
            unit : str
                The unit of the parameter (if applicable).
            param_type : type
                The expected type of the parameter.

            Returns
            -------
            Any
                The value of the parameter.

            Raises
            ------
            AssertionError
                If the parameter is not of the expected type.
            """
            self.declare_parameter(name=param, value=default_value)
            value = self.get_parameter(param).value

            if value is None:
                self.get_logger().warn(
                    f"No {description} provided, "
                    f"using default: {default_value}{unit}"
                )
                value = default_value

            assert isinstance(
                value,
                param_type
            ), f"{param} must be a {param_type.__name__}"
            self.get_logger().info(f"{description}: {value}{unit}")
            return value

        # Serial port parameter
        self._port = declare_and_get_param(
            param="serial_port",
            default_value=PORT,
            description="Serial Port",
            unit="",
            param_type=str
        )

        # Publish frequency parameter
        self._publish_freq = declare_and_get_param(
            param="publish_freq",
            default_value=FREQUENCY,
            description="Publishing frequency",
            unit=" Hz",
            param_type=float
        )

    def ros_setup(self):
        """
        Set up ROS publishers for battery status.

        This method creates a publisher with a specific QoS profile and
        sets up a timer for periodic data reading.
        """
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            depth=10  # Depth can be adjusted based on your needs
        )

        self._publisher_status = self.create_publisher(
            topic="~/data",
            msg_type=BatteryStatus,
            qos_profile=qos_profile,

        )
        timer_period = 1.0 / self._publish_freq
        self._timer = self.create_timer(
            timer_period_sec=timer_period,
            callback=self.read
        )
        self.get_logger().debug(
            f"publisher frecuency: {self._publish_freq}Hz"
        )

    def setup(self):
        """
        Set up the JbdBMS node and its components.

        This method initializes the node by reading parameters, setting up
        publishers, and initializing the BMS communication.

        Returns
        -------
        bool
            True if setup is successful.
        """
        self.ros_read_params()
        self.ros_setup()
        self._jbd.select_port(self._port)
        self._jbd.setup()
        return True

    def read(self):
        """
        Obtain, process, and publish the battery data.

        This method retrieves data from the Jbd BMS, updates the battery
        status, and publishes the information.

        Returns
        -------
        bool
            True if data retrieval and processing are successful,
            False otherwise.
        """
        if not self._jbd.retrieve_data():
            return False
        summary_data = self._jbd.get_data()
        self._battery_data = copy_dataclass_to_ros_message(
            summary_data,
            self._battery_data.status
        )
        self.ros_publish()
        return True

    def ros_publish(self):
        """
        Publish battery status to ROS topics.

        This method publishes the current battery status to its respective
        ROS topic using the previously set up publisher.
        """
        self._publisher_status.publish(self._battery_data.status)
