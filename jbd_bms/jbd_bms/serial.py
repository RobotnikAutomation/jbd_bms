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
Serial communication configuration and management.

This module provides classes for configuring and managing serial communication.
It includes dataclasses for storing configuration parameters and
communication state, as well as a class for
handling the serial port operations.

Classes
-------
SerialConfig
    Dataclass for storing serial port configuration parameters.
SerialData
    Dataclass to represent the state of a serial communication.
SerialPort
    Class to manage and communicate via serial port.

"""

import time
import os
import sys

from typing import Any
from dataclasses import dataclass, field

import serial

from .utils import DefaultLogger


@dataclass
class SerialConfig:
    """
    Dataclass for storing serial port configuration parameters.

    Attributes
    ----------
        port (str): The serial port path.
        baudrate (int): The baud rate for serial communication.
        parity (str): The parity setting for error checking.
        bytesize (int): The number of data bits.
        timeout (int): The read timeout value in seconds.
        stopbits (str): The number of stop bits.

    """

    port: str = ""
    baudrate: int = 9600
    parity: str = serial.PARITY_NONE
    bytesize: int = serial.EIGHTBITS
    timeout: int = 1
    stopbits: str = serial.STOPBITS_ONE


@dataclass
class SerialData:
    """
    A data class to represent the state of a serial communication.

    Attributes
    ----------
        data (bytearray): The data received from the serial port.
                                  Default is an empty bytearray.
        ready (bool): A flag indicating whether the
                      data is ready to be processed.
                      Default is False.
        processing (bool): A flag indicating whether the
                           data is being processing.
                           Default is False.
        device (Any): The pyserial object representing the serial device.
                      This can be any object that provides the necessary
                      methods for serial communication.
        config (SerialConfig): Configuration settings for the serial
                               communication, such as port, baud rate,
                               and timeout.

    """

    data: bytearray = field(default_factory=bytearray)
    ready: bool = False
    processing: bool = False
    device: Any = field(default=None)
    config: SerialConfig = field(default_factory=SerialConfig)


class SerialPort():
    """
    A class to manage serial port communication.

    This class handles serial communication, including connection setup,
    data processing, and error handling.

    Parameters
    ----------
    port : str, optional
        The serial port path. Default is "/dev/ttyUSB0".
    logger : Logger, optional
        Logger object for logging messages. Default is DefaultLogger().

    Attributes
    ----------
    _logger : Logger
        Logger object for logging messages.
    _serial : SerialData
        Object containing serial communication data and configuration.

    Methods
    -------
    check_device()
        Check if the specified serial device exists.
    reconnect()
        Attempt to reconnect to the serial port.
    setup()
        Initialize the necessary components for serial communication.
    select_port(port)
        Change the port after initialization.
    _port_setup()
        Set up the serial connection.
    _handle_serial_exception(exception)
        Handle serial exceptions.

    Notes
    -----
    This class is designed for general serial port communication and can be
    used with various devices that communicate over a serial interface.

    """

    def __init__(
        self,
        port="/dev/ttyUSB0",
        logger=DefaultLogger(),
    ):

        self._logger = logger
        self._serial = SerialData()
        self._serial.config.port = port

    def check_device(self):
        """
        Check if the specified serial device exists.

        This method checks for the existence of the device at the path
        'serial port'. If the device does not exist, an error message
        is logged and the program exits with a non-zero status code.

        Raises
        ------
        SystemExit
            Exits the program if the device does not exist.

        """
        device_path = self._serial.config.port
        if not os.path.exists(device_path):
            self._logger.error(
                f"Device {device_path} does not exist."
            )
            sys.exit(1)

    def reconnect(self):
        """
        Attempt to reconnect to the serial port.

        Tries to establish a connection up to 5 times,
        with a 1-second delay between attempts.
        Updates the component state based on the connection result.
        """
        cnt = 0
        while cnt < 5:
            cnt += 1
            self._logger.info("Trying to reconnect.")
            time.sleep(1)
            try:
                self._serial.device = serial.Serial(
                    port=self._serial.config.port,
                    baudrate=self._serial.config.baudrate,
                    parity=self._serial.config.parity,
                    bytesize=self._serial.config.bytesize,
                    timeout=self._serial.config.timeout,
                    stopbits=self._serial.config.stopbits,
                )
            except serial.SerialException as var:
                self._handle_serial_exception(var)
                # self.switch_to_state(State.EMERGENCY_STATE)
            else:
                self._logger.info('Serial Port Opened')
                # self.switch_to_state(State.READY_STATE)
                break
        if cnt == 5:
            self._logger.error("Unable to open the port.")
            # self.switch_to_state(State.FAILURE_STATE)

    def setup(self):
        """
        Initialize the necessary components for the ROS node.

        This method performs the following actions:
        1. Reads parameters from the ROS parameter server.
        2. Checks for the existence of the required serial device.
        3. Configures the serial port settings.
        4. Sets up ROS-related configurations.

        This method should be called during
        the initialization phase of the node
        to ensure that all components are properly configured before the node
        starts operating. If the required serial device is not found, the node
        will log an error and exit.

        Raises
        ------
        SystemExit
            Exits the program if the required serial device does not exist.

        """
        self.check_device()
        self._port_setup()

    def select_port(
        self,
        port
    ):
        """
        Change the port after initilization.

        Parameters
        ----------
        port : str
               serial port file.

        """
        self._serial.config.port = port
        # self.setup()

    def _port_setup(self):
        """
        Set up the serial connection for the WiferionBMS.

        Attempts to open the serial port and calls
        the reconnect method if an exception occurs.
        """
        try:
            self._serial.device = serial.Serial(
                port=self._serial.config.port,
                baudrate=self._serial.config.baudrate,
                parity=self._serial.config.parity,
                bytesize=self._serial.config.bytesize,
                timeout=self._serial.config.timeout,
                stopbits=self._serial.config.stopbits
            )
        except serial.SerialException as var:
            self._handle_serial_exception(var)
            self.reconnect()
        else:
            self._logger.info(
                f'Serial Port {self._serial.config.port} Opened'
            )

    def _handle_serial_exception(self, exception):
        """
        Handle serial exceptions.

        Parameters
        ----------
        exception : exception
                    serial exception raised.

        """
        self._logger.error('An Exception Occurred')
        self._logger.error(f"Exception Details-> {exception}")
        self.reconnect()
