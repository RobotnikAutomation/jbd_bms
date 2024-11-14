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
        command=JBDProtocol.status_cmd
    ),
    "cell": JBDCommand(
        command=JBDProtocol.cell_cmd
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
        if not self._read_serial_data():
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
            self._serial.processing = True
            return True
        except serial.SerialException as var:
            self._handle_serial_exception(var)
            return False

    def _read_serial_data(
        self,
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
        minimal_response = 4
        self._serial.ready = False
        try:
            while len(self._serial.data) < minimal_response:
                if time.time() - start_time > total_timeout:
                    self._logger.debug(
                        "Total timeout exceeded. "
                        f"Received only {len(self._serial.data)} bytes."
                    )
                    break
                chunk = self._serial.device.read(
                    minimal_response - len(self._serial.data)
                )
                if chunk:
                    # Append the received bytes to our buffer
                    self._serial.data.extend(chunk)
                    self._logger.debug(
                        f"Received {len(chunk)} bytes. "
                        f"Total: {len(self._serial.data)} bytes."
                    )
            if not len(self._serial.data) == minimal_response:
                self._logger.debug(
                    "Incomplete data. "
                    f"Received {len(self._serial.data)} bytes:"
                )
                self._serial.processing = False
                return False

            formatted_bytes = [f'0x{byte:02X}' for byte in self._serial.data]
            formatted_data = ' '.join(formatted_bytes)
            self._logger.debug(f'RAW DATA: {formatted_data}')
            self._serial.ready = True
            self._serial.processing = False

            return True
        except serial.SerialException as var:
            self._handle_serial_exception(var)
            return False

    def _process_serial_data(self, command):
        """
        Process the received serial data.

        Returns
        -------
        bool
            True if the data could be processeed
            False if the data could not be processed

        """

        def clear_buffer():
            # clear the buffer
            self._serial.data = bytearray()
            self._logger.debug(
                "clearer buffer"
                f" buffer size: {len(self._serial.data)}"
            )
        if not self._serial.ready:
            return False
        self._serial.ready = False
        self._preparse_rawdata(self._serial.data)
        if self._validate_data(command):
            return False
        return True

    def _preparse_rawdata(
        self,
        raw_data
    ):
        """
        Separate the fields of the raw data array into structured components.

        This method parses the raw data received from the BMS and assigns
        each component to the corresponding attribute of the
        _preparsed_raw_data object. It extracts the
        header, command, response, length, data,
        checksum, and footer from the raw data array.

        Parameters
        ----------
        raw_data : list or bytes
            The raw data array received from the BMS.

        Notes
        -----
        The method assumes a specific structure for the raw_data:
        - Index 0: Header
        - Index 1: Command
        - Index 2: Response
        - Index 3: Length
        - Index 4 to -3: Data payload
        - Index -3 to -1: Checksum (2 bytes)
        - Index -1: Footer

        The parsed data is stored in the self._preparsed_raw_data object,
        which is assumed to have attributes corresponding to each component.

        This method does not return any value but updates the internal
        _preparsed_raw_data object.
        """
        self._preparsed_raw_data.header = raw_data[0]
        self._preparsed_raw_data.command = raw_data[1]
        self._preparsed_raw_data.response = raw_data[2]
        self._preparsed_raw_data.length = raw_data[3]
        self._preparsed_raw_data.data = raw_data[4:-3]
        self._preparsed_raw_data.checksum = raw_data[-3:-1]
        self._preparsed_raw_data.footer = raw_data[-1]

    def _validate_data(self, command):
        """
        Validate the received data stream from the JBD BMS.

        This method performs a series of checks on the preparsed
        raw data to ensure its integrity and compliance with the JBD protocol.
        It verifies the header, command, response, length, checksum,
        and footer of the data stream.

        The method uses internal helper functions to
        calculate the checksum and print error messages.

        Parameters
        ----------
        command : int
            The expected command value to validate against.

        Returns
        -------
        bool
            True if the data stream is valid, False otherwise.

        Notes
        -----
        The method checks the following components of the data stream:
        - Header: Must match the expected protocol header.
        - Command: Must match the provided command parameter.
        - Response: Must be a valid response as defined by the protocol.
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

        def print_error(
            description,
            received,
            expected,
        ):
            self._logger.warn(
                f"Data stream error: {description} "
                f"received: {received} "
                f"expected: {expected}"
            )
        result = True
        if self._preparsed_raw_data.header != JBDPROTCONST.header:
            print_error(
                description="Wrong Header",
                received=hex(self._preparsed_raw_data.header),
                expected=hex(JBDPROTCONST.header)
            )
            result = False

        if result and (
            self._preparsed_raw_data.command != command
        ):
            print_error(
                description="Wrong Command",
                received=hex(self._preparsed_raw_data.command),
                expected=hex(command)
            )
            result = False

        if result and (
            self._preparsed_raw_data.response != JBDPROTCONST.valid_response
        ):
            print_error(
                description="Wrong Response",
                received=hex(self._preparsed_raw_data.response),
                expected=hex(JBDPROTCONST.valid_response)
            )
            result = False

        data_length = len(self._preparsed_raw_data.data)
        if result and (
            self._preparsed_raw_data.length != data_length
        ):
            print_error(
                description="Wrong Length",
                received=self._preparsed_raw_data.length,
                expected=data_length
            )
            result = False

        received_checksum = int(
            self._preparsed_raw_data.checksum,
            byteorder='big',
            signed=False
        )
        if result:
            calculated_checksum = calculate_checksum(
                data=self._preparsed_raw_data.data,
                length=self._preparsed_raw_data.length,
            )
            if received_checksum != calculated_checksum:
                print_error(
                    description="Wrong checksum",
                    received=hex(received_checksum),
                    expected=hex(calculated_checksum)
                )
            result = False

        if result and (
            self._preparsed_raw_data.footer != JBDPROTCONST.footer
        ):
            print_error(
                description="Wrong Footer",
                received=hex(self._preparsed_raw_data.footer),
                expected=hex(JBDPROTCONST.footer)
            )
            result = False

        if result:
            self._logger.debug(
                "Data stream Valid"
            )
        return result

    def _fill_summary(self):
        data = self._preparsed_raw_data
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

        self._battery_data.level = float(data[9])

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

