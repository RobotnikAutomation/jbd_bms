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
JBD BMS Protocol and Data Structures.

This module defines data structures and protocol specifications for
communicating with JBD Battery Management Systems (BMS). It includes classes
for received data, protocol structure, commands, and battery data.

Classes:
    ReceivedData: Represents data received from the BMS.
    JBDProtocolLenght: Defines protocol message length specifications.
    JBDProtocolStructure: Specifies protocol structural elements.
    JBDProtocolCommands: Defines command codes for the JBD protocol.
    JBDProtocol: Combines protocol specifications.
    JBDCommand: Represents a command to be sent to the BMS.
    BatteryData: Encapsulates battery state information.

Constants:
    jbd_protocol: An instance of JBDProtocol with default settings.
"""

from dataclasses import dataclass, field


@dataclass
class ReceivedData:
    """
    Represents data received from the BMS.

    Attributes
    ----------
    header : int
        The header byte of the received message. Default is 0x00.
    command : int
        The command byte of the received message. Default is 0x00.
    response : int
        The response byte of the received message. Default is 0x00.
    length : int
        The length byte of the received message. Default is 0x00.
    data : list or None
        The data payload of the received message. Default is None.
    checksum : list or None
        The checksum bytes of the received message. Default is None.
    footer : int
        The footer byte of the received message. Default is 0x00.

    """

    header: int = 0x00
    command: int = 0x00
    response: int = 0x00
    length: int = 0x00
    data: list = None
    checksum: list = None
    footer: int = 0x00


@dataclass(frozen=True)
class JBDProtocolLenght:
    """
    Specifies protocol structural elements.

    Attributes
    ----------
    header : int
        The header byte value for the protocol. Default is 0xDD.
    footer : int
        The footer byte value for the protocol. Default is 0x77.
    valid_response : int
        The byte value indicating a valid response. Default is 0x00.

    """

    header: int = 4
    footer: int = 3
    total: int = field(init=False)

    def __post_init__(self):
        """Calculate the total length after initialization."""
        object.__setattr__(
            self,
            'total',
            self.header + self.footer
        )


@dataclass(frozen=True)
class JBDProtocolStructure:
    """
    Specifies protocol structural elements.

    Attributes
    ----------
    header : int
        The header byte value for the protocol. Default is 0xDD.
    footer : int
        The footer byte value for the protocol. Default is 0x77.
    valid_response : int
        The byte value indicating a valid response. Default is 0x00.

    """

    header: int = 0xDD
    footer: int = 0x77
    valid_response: int = 0x00


@dataclass(frozen=True)
class JBDProtocolCommands:
    """
    Defines command codes for the JBD protocol.

    Attributes
    ----------
    prefix : int
        The prefix byte for commands. Default is 0xA5.
    status : int
        The command code for requesting status. Default is 0x03.
    cell : int
        The command code for cell-related operations. Default is 0x04.

    """

    prefix: int = 0xA5
    status: int = 0x03
    cell: int = 0x04


@dataclass(frozen=True)
class JBDProtocol:
    """
    Combines protocol specifications.

    Attributes
    ----------
    structure : JBDProtocolStructure
        The structural elements of the protocol.
    commands : JBDProtocolCommands
        The command codes used in the protocol.
    length : JBDProtocolLenght
        The length specifications for protocol messages.

    """

    structure: JBDProtocolStructure = field(
        default_factory=JBDProtocolStructure
    )
    commands: JBDProtocolCommands = field(
        default_factory=JBDProtocolCommands
    )
    length: JBDProtocolLenght = field(
        default_factory=JBDProtocolLenght
    )


jbd_protocol = JBDProtocol()


@dataclass
class JBDCommand:
    """
    Represents a command to be sent to the BMS.

    Attributes
    ----------
    command : int
        The command code to be sent.
    full_command : bytearray
        The complete command message including header, command, checksum,
        and footer.

    Methods
    -------
    __post_init__()
        Constructs the full command message after initialization.

    """

    command: int
    full_command: bytearray = field(default_factory=bytearray)

    def __post_init__(self):
        checksum = self.command - 1 ^ 0xFFFF
        checksum_bytes = checksum.to_bytes(2, byteorder='big')
        data_length = 0x00
        self.full_command = bytearray([
            jbd_protocol.structure.header,
            jbd_protocol.commands.prefix,
            self.command,
            data_length,
            checksum_bytes[0],
            checksum_bytes[1],
            jbd_protocol.structure.footer
        ])


@dataclass
class BatteryData:
    """
    Represents battery data with various attributes.

    This class encapsulates information about a battery's state, including
    voltage, current, charge level, and charging status. It uses default
    values to indicate uninitialized or invalid states.

    Attributes
    ----------
    voltage : float
        The battery voltage in volts. Default is -100.0, indicating an
        uninitialized or invalid state.
    current : float
        The battery current in amperes. Default is -100.0, indicating an
        uninitialized or invalid state.
    level : float
        The battery charge level as a percentage (0.0 to 100.0). Default
        is -1.0, indicating an uninitialized or invalid state.
    time_remaining : int
        The estimated time remaining until the battery is fully discharged,
        in seconds. Default is -1, indicating an unknown or invalid state.
    time_charging : int
        The time the battery has been charging, in seconds. Default is -1,
        indicating that the battery is not currently charging or the value
        is unknown.
    is_charging : bool
        Indicates whether the battery is currently charging. Default is False.

    Notes
    -----
    - Negative values for voltage, current, level, time_remaining, and
      time_charging are used to represent invalid or uninitialized states.
    - The `is_charging` attribute should be set to True only when the battery
      is actively being charged.

    """

    voltage: float = -100.0
    current: float = -100.0
    level: float = -1.0
    time_remaining: int = -1
    time_charging: int = -1
    is_charging: bool = False
