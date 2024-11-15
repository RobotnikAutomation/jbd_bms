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
JBD BMS Communication Module.

This module provides functionality for communicating with JBD Battery
Management Systems (BMS) over a serial connection. It includes classes and
methods for sending commands, receiving and parsing data, and managing the
battery state.

Classes
-------
JbdBMS : SerialPort
    Main class for interacting with the JBD BMS.

Functions
---------
None

Constants
---------
JBDPROTCONST : JBDProtocol
    Constants for JBD protocol.
COMMANDS : dict
    Predefined commands for BMS communication.

Notes
-----
This module relies on the serial communication protocol defined by JBD BMS.
It handles command sending, data reception, parsing, and validation.


"""

import time
from dataclasses import asdict

import serial

from .serial import SerialPort
from .utils import DefaultLogger
from .jbd_bms_dataclasses import JBDProtocol, JBDCommand
from .jbd_bms_dataclasses import ReceivedData, BatteryData

JBDPROTCONST = JBDProtocol()
COMMANDS = {
    "status": JBDCommand(
        command=JBDPROTCONST.commands.status
    ),
    "cell": JBDCommand(
        command=JBDPROTCONST.commands.cell
    ),
}


class JbdBMS(SerialPort):
    """
    A class to manage and communicate with JDB Battery Management System.

    This class handles the serial communication, data processing,
    and publishing of battery status information.
    """

    def __init__(
        self,
        port="/dev/ttyUSB_BMS",
        logger=DefaultLogger(),
    ):
        super().__init__(
            port=port,
            logger=logger
        )

        self._battery_data = BatteryData()
        self._preparsed_raw_data = ReceivedData()
        self._commands = COMMANDS
        self._charge_time = 0

    def retrieve_data(self):
        """
        Read data from the serial port, process it.

        Returns
        -------
        bool
            If everything ok True
            In any failure False.

        """
        full_command = self._commands['status'].full_command
        command = self._commands['status'].command
        if not self._send_command(
            full_command
        ):
            self._logger.info("Command not sent")
            return False
        if not self._read_serial_data(command):
            self._logger.info("No data received")
            return False
        if not self._process_serial_data():
            self._logger.info("Error parsing data")
            return False
        return True

    def get_data(self):
        """
        Return the summary data.

        Returns
        -------
        Class
            Return the summary data.

        """
        return self._battery_data

    def _print_hex(
        self,
        data,
        message
    ):
        """
        Print hexadecimal representation of data with a message.

        This method formats the input data as a string of hexadecimal values
        and logs it using the debug level of the logger.

        Parameters
        ----------
        data : bytes or bytearray
            The data to be printed in hexadecimal format.
        message : str
            A message to prepend to the hexadecimal data in the log.

        """
        formatted_bytes = [f'0x{byte:02X}' for byte in data]
        formatted_data = ' '.join(formatted_bytes)
        self._logger.debug(f"{message} RAW DATA: {formatted_data}")

    def _clear_buffer(self):
        """
        Clear the internal data buffer and log the action.

        This method resets the internal data buffer to an empty bytearray
        and logs a debug message indicating that the buffer has been cleared,
        along with the new buffer size.
        """
        self._serial.data = bytearray()
        self._logger.debug(
            "clearer buffer"
            f" buffer size: {len(self._serial.data)}"
        )

    def _send_command(
        self,
        command
    ):
        """
        Send command to the BMS.

        Returns
        -------
        bool
            If everything ok True
            In any failure False.

        """
        self._logger.debug("Sending command")
        if self._serial.processing:
            self._logger.debug(
                "Petition in progress, ignoring new command"
            )
            return False
        try:
            self._clear_buffer()
            self._serial.device.write(command)
            self._serial.device.flush()
            self._print_hex(
                data=command,
                message="SENT"
            )
            self._serial.processing = True
            return True
        except serial.SerialException as var:
            self._handle_serial_exception(var)
            return False

    def _read_serial_data(
        self,
        command
    ):
        """
        Read data from the serial port.

        This method reads and processes data from the serial port, including
        header and payload data.

        Parameters
        ----------
        command : int
            The command code sent to the device.

        Returns
        -------
        bool
            True if the data was successfully read and processed,
            False otherwise.

        Raises
        ------
        serial.SerialException
            If there's an issue with the serial communication.

        """

        def read_chunk():
            """
            Read a chunk of data from the serial port.

            This function reads available data from the serial port and
            appends it to the internal buffer.

            Returns
            -------
            bool
                True if data was read successfully, False if a timeout occurred
                or no data was available.

            Notes
            -----
            This function updates the internal data buffer and logs debug
            information.

            """
            start_time = time.time()
            if self._serial.device.in_waiting == 0:
                return False
            if time.time() - start_time > total_timeout:
                self._logger.debug(
                    "Total timeout exceeded. "
                    f"Received only {len(self._serial.data)} bytes."
                )
                return False
            chunk = self._serial.device.read(
                self._serial.device.in_waiting
            )
            self._print_hex(chunk, "CHUCK")
            if chunk:
                # Append the received bytes to our buffer
                self._serial.data.extend(chunk)
                self._logger.debug(
                    f"Received {len(chunk)} bytes. "
                    f"Total: {len(self._serial.data)} bytes."
                )
            return True

        def check_data_length(length):
            """
            Check if the received data meets the expected length.

            Parameters
            ----------
            length : int
                The expected length of the data.

            Returns
            -------
            bool
                True if the data length is sufficient, False otherwise.

            Notes
            -----
            If the data is incomplete, this function logs debug information,
            prints the received data, and clears the buffer.

            """
            if len(self._serial.data) < length:
                self._logger.debug(
                    "Incomplete data. "
                    f"Received: {len(self._serial.data)} bytes."
                    f"Expected: {length} bytes."
                )
                self._print_hex(
                    data=self._serial.data,
                    message="RECEIVED"
                )
                self._clear_buffer()
                self._serial.processing = False
                return False
            return True

        def read_serial_data_amount(length):
            """
            Read a specific amount of data from the serial port.

            This function reads data until the specified length is reached or
            a timeout occurs.

            Parameters
            ----------
            length : int
                The number of bytes to read.

            Returns
            -------
            bool
                True if the required amount of data was read, False otherwise.

            """
            while len(self._serial.data) < length:
                if not read_chunk():
                    break
                time.sleep(0.001)
            if not check_data_length(length):
                return False
            return True

        def process_header():
            """
            Process the header of the received data.

            This function reads and validates the header of the incoming data.

            Returns
            -------
            bool
                True if the header was successfully processed and validated,
                False otherwise.

            Notes
            -----
            This function updates internal state based on the received header.

            """
            header_length = JBDPROTCONST.length.header
            if not read_serial_data_amount(header_length):
                return False
            header = self._serial.data
            self._print_hex(
                data=header,
                message="RECEIVED HEADER"
            )
            self._preparse_rawdata_header(header)
            if not self._validate_header(command):
                self._serial.processing = False
                return False
            return True

        def process_data():
            """
            Process the payload data of the received message.

            This function reads the payload data, validates it, and updates
            the internal state accordingly.

            Returns
            -------
            bool
                True if the data was successfully processed and validated,
                False otherwise.

            Notes
            -----
            This function performs data parsing, validation, and updates the
            internal ready state.

            """
            footer = JBDPROTCONST.length.footer
            data_length = self._preparsed_raw_data.length
            data_length += footer
            if not read_serial_data_amount(data_length + footer):
                return False

            self._print_hex(
                data=self._serial.data,
                message="RECEIVED"
            )
            parse_result = self._preparse_rawdata(self._serial.data)
            validate_result = self._validate_data()
            self._clear_buffer()
            self._serial.processing = False
            if parse_result and validate_result:
                self._serial.ready = True
                return True
            return False

        total_timeout = self._serial.device.timeout
        self._serial.ready = False
        try:
            if not process_header():
                return False
            if not process_data():
                return False
            return True
        except serial.SerialException as var:
            self._handle_serial_exception(var)
            return False

    def _process_serial_data(self):
        """
        Process the received serial data.

        Returns
        -------
        bool
            True if the data could be processeed
            False if the data could not be processed

        """
        if not self._serial.ready:
            return False
        self._serial.ready = False
        # if not self._preparse_rawdata(self._serial.data):
        #     return False
        self._fill_summary()
        return True

    def _preparse_rawdata_header(
        self,
        raw_data
    ):
        """
        Separate the fields of the raw data array into structured components.

        This method parses the raw data received from the BMS and assigns
        each component to the corresponding attribute of the
        _preparsed_raw_data object. It extracts the header, command, response,
        length, data, checksum, and footer from the raw data array.

        Parameters
        ----------
        raw_data : list or bytes
            The raw data array received from the BMS.

        Returns
        -------
        bool
            True if parsing was successful, False otherwise.

        Notes
        -----
        The method assumes a specific structure for the raw_data:
        - Index 0: Header
        - Index 1: Command
        - Index 2: Response
        - Index 3: Length (N)

        The parsed data is stored in the self._preparsed_raw_data object,
        which is assumed to have attributes corresponding to each component.

        This method updates the internal _preparsed_raw_data object.

        """
        attributes = [
            'header',
            'command',
            'response',
            'length',
        ]
        for index, attr in enumerate(attributes):
            value = raw_data[index]
            setattr(self._preparsed_raw_data, attr, value)

    def _preparse_rawdata(
        self,
        raw_data
    ):
        """
        Separate the fields of the raw data array into structured components.

        This method parses the raw data received from the BMS and assigns
        each component to the corresponding attribute of the
        _preparsed_raw_data object. It extracts the
        data, checksum, and footer from the raw data array.

        Parameters
        ----------
        raw_data : list or bytes
            The raw data array received from the BMS.

        Returns
        -------
        bool
            True if parsing was successful, False otherwise.

        Notes
        -----
        The method assumes a specific structure for the raw_data:
        - Index 0: Header
        - Index 1: Command
        - Index 2: Response
        - Index 3: Length (N)
        - Index 4 to N-3: Data payload
        - Index N-3 to N-1: Checksum (2 bytes)
        - Index N: Footer

        The parsed data is stored in the self._preparsed_raw_data object,
        which is assumed to have attributes corresponding to each component.

        This method updates the internal _preparsed_raw_data object.

        """
        if len(raw_data) < JBDPROTCONST.length.total:
            self._logger.warn(
                "Data length below minimun "
                f" Minimum: {JBDPROTCONST.length.total} "
                f" Received: {len(raw_data)}"
            )
            return False
        length = self._preparsed_raw_data.length
        length += JBDPROTCONST.length.header
        footer_pos = length + JBDPROTCONST.length.footer - 1
        self._preparsed_raw_data.data = raw_data[4:length]
        self._print_hex(
            data=self._preparsed_raw_data.data,
            message="PURE DATA"
        )
        self._preparsed_raw_data.checksum = raw_data[
            length:length + 2
        ]
        self._preparsed_raw_data.footer = raw_data[footer_pos]
        return True

    def _validation_engine(self, validations):
        """
        Perform a series of validations on the received data.

        This method iterates through a list of validation checks, comparing
        received values against expected values. It handles different formats
        for the comparisons and logs errors for any mismatches.

        Parameters
        ----------
        validations : list of dict
            A list of dictionaries, each containing:
            - 'description': str, description of the validation
            - 'received': any, the received value
            - 'expected': any, the expected value
            - 'format': str, the format for comparison ('hex', 'int', or other)

        Returns
        -------
        bool
            True if all validations pass, False otherwise.

        Notes
        -----
        For each failed validation, an error is logged with
        the discrepancy details.
        The method stops at the first failed validation.

        """
        for validation in validations:
            self._logger.debug(
                f"Validating {validation['description']}"
            )
            if validation["received"] != validation["expected"]:
                if validation["format"] == "hex":
                    received = f'0x{validation["received"]:02X}'
                    expected = f'0x{validation["expected"]:02X}'
                elif validation["format"] == "int":
                    received = int(validation["received"])
                    expected = int(validation["expected"])
                else:
                    received = validation["received"]
                    expected = validation["expected"]
                self._logger.warn(
                    f"Data stream error: Wrong {validation['description']} "
                    f"received: {received} "
                    f"expected: {expected}"
                )
                return False
            self._logger.debug(
                f"{validation['description']} Valid"
            )
        self._logger.debug("Received header is Valid")
        return True

    def _validate_header(
        self,
        command
    ):
        """
        Validate the header of the received data.

        This method checks the header, command, and response fields of the
        received data against expected values.

        Parameters
        ----------
        command : int
            The expected command value.

        Returns
        -------
        bool
            True if the header is valid, False otherwise.

        Notes
        -----
        The method performs the following checks comparing:
        1. the received header with the expected header constant.
        2. the received command with the provided command parameter.
        3. the received response with the expected valid response constant.

        If any of these checks fail, an error is logged with
        the discrepancy details.

        """
        validations = [
            {
                "description": "Header",
                "received": self._preparsed_raw_data.header,
                "expected": JBDPROTCONST.structure.header,
                "format": "hex"
            },
            {
                "description": "Command",
                "received": self._preparsed_raw_data.command,
                "expected": command,
                "format": "hex"
            },
            {
                "description": "Response",
                "received": self._preparsed_raw_data.response,
                "expected": JBDPROTCONST.structure.valid_response,
                "format": "hex"
            }
        ]
        return self._validation_engine(validations)

    def _validate_data(self):
        """
        Validate the received data stream from the JBD BMS.

        This method performs a series of checks on the
        preparsed raw data to ensure its integrity and compliance
        with the JBD protocol. It verifies the length,
        checksum, and footer of the data stream.

        Returns
        -------
        bool
            True if the data stream is valid, False otherwise.

        Notes
        -----
        The method checks the following components of the data stream:
        - Length: Must match the actual length of the data.
        - Checksum: Calculated checksum must match the received checksum.
        - Footer: Must match the expected protocol footer.

        If any check fails, an error message is logged,
        and the method returns False.

        Notes
        -----
        The XOR operation with 0xffff
        is used to invert all bits of the result checksum.

        """
        received_checksum = int.from_bytes(
            self._preparsed_raw_data.checksum,
            byteorder='big',
            signed=False
        )
        data = self._preparsed_raw_data.data
        length = self._preparsed_raw_data.length
        calculated_checksum = (sum(data) + length - 1) ^ 0xffff

        validations = [
            {
                "description": "Length",
                "received": len(self._preparsed_raw_data.data),
                "expected": self._preparsed_raw_data.length,
                "format": "int"
            },
            {
                "description": "Checksum",
                "received": received_checksum,
                "expected": calculated_checksum,
                "format": "hex"
            },
            {
                "description": "Footer",
                "received": self._preparsed_raw_data.footer,
                "expected": JBDPROTCONST.structure.footer,
                "format": "hex"
            }
        ]
        return self._validation_engine(validations)

    def _fill_summary(self):
        """
        Process raw data and update battery information.

        This method extracts and calculates various battery parameters from
        the raw data stored in `self._preparsed_raw_data.data`. It updates
        the `self._battery_data` object with the processed information.

        The following battery parameters are updated:
        - Voltage
        - Current
        - Remaining time (if discharging)
        - Battery level
        - Charging status
        - Charging time (if charging)

        Notes
        -----
        - Voltage and current are converted from raw data and rounded.
        - Remaining time is calculated only when discharging (current < 0).
        - Charging status is determined by the current (> 0 means charging).
        - Charging time is calculated and updated only when charging.

        """
        data = self._preparsed_raw_data.data
        voltage = data[0:2]
        voltage = int.from_bytes(
            voltage,
            byteorder='big',
            signed=False
        )
        voltage = round(float(voltage / 100), 2)
        current = data[2:4]
        current = int.from_bytes(
            current,
            byteorder='big',
            signed=True
        )
        current = round(float(current / 100), 3)
        capacity = data[4:6]
        capacity = int.from_bytes(
            capacity,
            byteorder='big',
            signed=False
        )
        capacity = round(float(capacity / 100), 2)
        if current < 0.0:
            remaining_time = abs((capacity / current) * 60)
            remaining_time = round(remaining_time, 0)
            remaining_time = int(remaining_time)
        else:
            remaining_time = 0
        self._battery_data.voltage = voltage
        self._battery_data.current = current
        self._battery_data.time_remaining = remaining_time
        self._battery_data.level = float(data[19])
        prev_charging = self._battery_data.is_charging

        if current > 0.0:
            charging = True
            if prev_charging != charging:
                self._battery_data.time_charging = 0
                self._charge_time = time.time()
            time_charging = time.time() - self._charge_time
            time_charging = time_charging / 60
            time_charging = round(time_charging, 0)
            time_charging = int(time_charging)

        else:
            charging = False
            time_charging = 0
        self._battery_data.is_charging = charging
        self._battery_data.time_charging = time_charging
        for attr, value in asdict(self._battery_data).items():
            self._logger.debug(f"{attr}: {value}")
