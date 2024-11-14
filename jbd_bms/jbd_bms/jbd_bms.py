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

import time
import serial

# Insert here general imports:
# from serial import SerialException
# from binascii import hexlify, unhexlify
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
        if not self._process_serial_data(command):
            self._logger.info("Error parsing data")
            return False
        return True

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
            self._serial.device.write(command)
            self._serial.device.flush()
            formatted_bytes = [f'0x{byte:02X}' for byte in command]
            formatted_data = ' '.join(formatted_bytes)
            self._logger.debug(f'SENT RAW DATA: {formatted_data}')
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

        Returns
        -------
        bool
            True if the data could  be read
            False if the data could not be readed

        """
        # Set a total timeout for the entire operation

        total_timeout = self._serial.device.timeout
        start_time = time.time()
        self._serial.ready = False
        serial_data = bytearray()

        def read_serial_data(length):
            while len(self._serial.data) < length:
                if time.time() - start_time > total_timeout:
                    self._logger.debug(
                        "Total timeout exceeded. "
                        f"Received only {len(self._serial.data)} bytes."
                    )
                    break
                chunk = self._serial.device.read(
                    length - len(self._serial.data)
                )
                if chunk:
                    # Append the received bytes to our buffer
                    self._serial.data.extend(chunk)
                    self._logger.debug(
                        f"Received {len(chunk)} bytes. "
                        f"Total: {len(self._serial.data)} bytes."
                    )

            if len(self._serial.data) < length:
                self._logger.debug(
                    "Incomplete data. "
                    f"Received {len(self._serial.data)} bytes."
                )
                self._print_hex(
                    data=self._serial.data,
                    message="RECEIVED"
                )
                self.clear_buffer()
                self._serial.processing = False
                return False
            return True

        try:
            # process header
            header_length = JBDPROTCONST.length.header
            if not read_serial_data(header_length):
                return False
            header = serial_data
            # REMOVE IT!!! it's for debug
            valid = bytearray(
                [0xDD, 0x03, 0x00, 0x1B]
            )
            # REMOVE IT!!! it's for debug
            header[0:4] = valid
            self._print_hex(
                data=header,
                message="RECEIVED HEADER"
            )
            self._preparse_rawdata_header(header)
            self.clear_buffer()
            if not self._validate_header(command):
                self._serial.processing = False
                return False
            data_length = self._preparsed_raw_data.length
            footer = JBDPROTCONST.length.footer
            if not read_serial_data(data_length + footer):
                return False

            self._print_hex(
                data=self._serial.data,
                message="RECEIVED"
            )
            # REMOVE IT!!! it's for debug
            valid = bytearray([
                0x17, 0x00, 0x00, 0x00, 0x02, 0xD0, 0x03, 0xE8,
                0x00, 0x00, 0x20, 0x78, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x10, 0x48, 0x03, 0x0F, 0x02, 0x0B,
                0x76, 0x0B, 0x82,
                0xFB, 0xFF, 0x77
            ])
            # SWAP IT!!! it's for debug
            # if not self._preparse_rawdata(self._serial.data):
            if not self._preparse_rawdata(valid):
                return False
            self._print_hex(
                data=self._serial.data,
                message="REAL"
            )
            # REMOVE IT!!! it's for debug
            self._print_hex(
                data=valid,
                message="FAKE"
            )
            self._serial.ready = True
            self._serial.processing = False

            return True
        except serial.SerialException as var:
            self._handle_serial_exception(var)
            return False

    def _print_hex(self, data, message):
        formatted_bytes = [f'0x{byte:02X}' for byte in data]
        formatted_data = ' '.join(formatted_bytes)
        self._logger.debug(f"{message} RAW DATA: {formatted_data}")

    def clear_buffer(self):
        # clear the buffer
        self._serial.data = bytearray()
        self._logger.debug(
            "clearer buffer"
            f" buffer size: {len(self._serial.data)}"
        )

    def _process_serial_data(self, command):
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
        if not self._validate_data():
            return False
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
        - Index 4 to N-3: Data payload
        - Index N-3 to N-1: Checksum (2 bytes)
        - Index N: Footer

        The parsed data is stored in the self._preparsed_raw_data object,
        which is assumed to have attributes corresponding to each component.

        This method updates the internal _preparsed_raw_data object.
        """
        self._preparsed_raw_data.header = raw_data[0]
        self._preparsed_raw_data.command = raw_data[1]
        self._preparsed_raw_data.response = raw_data[2]
        self._preparsed_raw_data.length = raw_data[3]

    def _preparse_rawdata(
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
        self._preparsed_raw_data.data = raw_data[0:-3]
        self._preparsed_raw_data.checksum = raw_data[-3:-1]
        self._preparsed_raw_data.footer = raw_data[-1]
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
        """
        def calculate_checksum(
            length,
            data
        ):
            """
            Calculate the checksum for the given data.

            This function computes a checksum based
            on the sum of the data bytes,
            the length of the data, and a bitwise XOR operation.

            Parameters
            ----------
            length : int
                The length of the data.
            data : list or bytes
                The data for which to calculate the checksum.

            Returns
            -------
            int
                The calculated checksum.

            Notes
            -----
            The XOR operation with 0xffff
            is used to invert all bits of the result.

            """
            calculated_checksum = (sum(data) + length - 1) ^ 0xffff
            return calculated_checksum

        received_checksum = int.from_bytes(
            self._preparsed_raw_data.checksum,
            byteorder='big',
            signed=False
        )
        calculated_checksum = calculate_checksum(
            data=self._preparsed_raw_data.data,
            length=self._preparsed_raw_data.length,
        )

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
        data = self._preparsed_raw_data.data
        # self._battery_data.voltage = round(float(data[0] / 100), 3)
        # self._battery_data.current = round(float(data[1] / 100), 3)
        voltage = data[0:2]
        voltage = int.from_bytes(
            voltage,
            byteorder='big',
            signed=False
        )
        voltage = round(float(voltage / 100), 3)
        current = data[2:4]
        current = int.from_bytes(
            current,
            byteorder='big',
            signed=False
        )
        current = round(float(current / 100), 3)
        self._battery_data.voltage = voltage
        self._battery_data.current = current

        self._battery_data.level = float(data[19])
        self._battery_data.time_remaining = 10
        self._battery_data.time_charging = 1
        self._battery_data.is_charging = False

    def get_data(self):
        """
        Return the summary data.

        Returns
        -------
        Class
            Return the summary data.

        """
        return self._battery_data


#############################

    # def ready_state(self):
    #     """Actions performed in ready state"""

    #     # Publish topic with status

    #     status_stamped = StringStamped()
    #     status_stamped.header.stamp = rospy.Time.now()
    #     status_stamped.string = self.status.data

    #     self.status_pub.publish(self.status)
    #     self.status_stamped_pub.publish(status_stamped)

    #     # Get battery values

    #     try:
    #         self.writeToSerialDevice("DDA50300FFFD77")
    #         rospy.sleep(0.1)
    #         line_read = str(self.readFromSerialDevice())
    #         hex_data = line_read.split("dd03001b")[1]
    #         self.voltage = self.twos_complement(hex_data[0:4]) / 100.0
    #         self.current = self.twos_complement(hex_data[4:8]) / 100.0
    #         self.level = self.twos_complement(hex_data[38:40])
    #     except Exception as e:
    #         rospy.logerr('%s::readyState: error reading BMS values: %s', rospy.get_name(), e)

    #     # Publish topic with data

    #     data = BatteryStatus()
    #     data.current = self.current
    #     data.voltage = self.voltage
    #     data.level = self.level
    #     if (self.current > 0.0):
    #         data.is_charging = True
    #     self.data_pub.publish(data)

    #     return RComponent.ready_state(self)




    # def writeToSerialDevice(self, data):
    #     data_write = unhexlify(data)
    #     bytes_written = self.serial_device.write(data_write)
    #     return bytes_written

    # def readFromSerialDevice(self):
    #     try:
    #         data_read = self.serial_device.read_all()
    #         return hexlify(data_read)
    #     except SerialException as e:
    #         rospy.logwarn(e)
    #         return

