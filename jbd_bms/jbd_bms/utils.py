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
This module provides utilities for XOR operations and a simple logging system.

It includes a function for performing XOR operations on arrays and a
DefaultLogger class for basic logging functionality. The module also defines
a LogLevel enumeration for specifying log severity levels.

Functions
---------
    copy_dataclass_to_ros_message(source, destination): Copy matching fields
         from a dataclass instance to a ROS 2 message.

Classes
-------
    LogLevel: Enumeration of log levels in order of increasing severity.
    DefaultLogger: A simple logging class that
                   prints log messages to the console.

Enumerations
------------
    LogLevel: DEBUG, INFO, WARN, ERROR, FATAL

The DefaultLogger class allows setting a minimum log level and only prints
messages at or above that level. It provides methods for logging at different
severity levels and allows for runtime adjustment of the minimum log level.
"""

import datetime
from enum import IntEnum
from dataclasses import fields


def copy_dataclass_to_ros_message(source, destination):
    """
    Copy matching fields from a dataclass instance to a ROS 2 message.

    Parameters
    ----------
    source : dataclass
        The source dataclass instance to copy from.
    destination : ros2_message
        The destination ROS 2 message to copy to.

    Returns
    -------
    ros2_message
        The destination ROS 2 message with updated fields.

    Notes
    -----
    This function iterates through the fields of the source dataclass
    and copies the values of matching fields to the destination ROS 2 message.
    Fields that don't exist in the destination message are skipped.

    """
    for field in fields(source):
        if hasattr(destination, field.name):
            setattr(destination, field.name, getattr(source, field.name))
    return destination


class LogLevel(IntEnum):
    """Enumeration of log levels in order of increasing severity."""

    DEBUG = 1
    INFO = 2
    WARN = 3
    ERROR = 4
    FATAL = 5


class DefaultLogger:
    """
    A simple logging class that prints log messages to the console.

    This logger allows setting a minimum log level and only prints messages
    at or above that level.

    Attributes
    ----------
        name (str): The name of the logger.
        level (LogLevel): The minimum log level to print.

    """

    def __init__(
        self,
        name="Logger",
        level="INFO"
    ):
        """
        Initialize the DefaultLogger.

        Args:
        ----
            name (str, optional): The name of the logger. Defaults to "Logger".
            level (str, optional): The minimum log level to print.
                                   Defaults to "INFO".

        """
        self.name = name
        self.level = LogLevel[level.upper()]

    def _log(self, level, message):
        """
        Print a log message.

        Internal method to log a message if its level is high enough.

        Parameters
        ----------
        level : str
                The log level of the message.
        message : str
                  The message to log.

        """
        if LogLevel[level] >= self.level:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(
                f"[{timestamp}] {self.name} - {level}: {message}",
                flush=True
            )

    def info(self, message):
        """
        Log an INFO level message.

        Parameters
        ----------
        message : str
                  message to display.

        """
        self._log("INFO", message)

    def debug(self, message):
        """
        Log a DEBUG level message.

        Parameters
        ----------
        message : str
                  message to display.

        """
        self._log("DEBUG", message)

    def warn(self, message):
        """
        Log a WARN level message.

        Parameters
        ----------
        message : str
                  message to display.

        """
        self._log("WARN", message)

    def error(self, message):
        """
        Log an ERROR level message.

        Parameters
        ----------
        message : str
                  message to display.

        """
        self._log("ERROR", message)

    def fatal(self, message):
        """
        Log a FATAL level message.

        Parameters
        ----------
        message : str
                  message to display.

        """
        self._log("FATAL", message)

    def set_level(self, level):
        """
        Set the minimum log level.

        Parameters
        ----------
        level : str
                The new minimum log level.

        """
        self.level = LogLevel[level.upper()]
