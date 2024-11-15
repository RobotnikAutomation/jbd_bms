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

from dataclasses import dataclass, field


@dataclass
class ReceivedData:
    header: int = 0x00
    command: int = 0x00
    response: int = 0x00
    length: int = 0x00
    data: list = None
    checksum: list = None
    footer: int = 0x00


@dataclass(frozen=True)
class JBDProtocolLenght:
    header: int = 4
    footer: int = 3
    total: int = field(init=False)

    def __post_init__(self):
        object.__setattr__(
            self,
            'total',
            self.header + self.footer
        )


@dataclass(frozen=True)
class JBDProtocolStructure:
    header: int = 0xDD
    footer: int = 0x77
    valid_response: int = 0x00


@dataclass(frozen=True)
class JBDProtocolCommands:
    prefix: int = 0xA5
    status: int = 0x03
    cell: int = 0x04


@dataclass(frozen=True)
class JBDProtocol:
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
