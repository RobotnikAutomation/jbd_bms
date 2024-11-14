#!/usr/bin/env python3
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
ROS2 node for the JBD SMART Battery Management System (BMS).

This module initializes and runs a ROS2 node that interfaces with the
JBD SMART Battery Management System. It provides functionality to:

1. Initialize the ROS2 system.
2. Create and set up a JbdBMSROS2 node.
3. Start the node's main processing loop.
4. Handle proper shutdown of the node and ROS2 system.

The JbdBMSROS2 class (imported from .jbd_bms_ros) handles the
core functionality, including communication with the BMS hardware,
data processing, and publishing of battery status information.

Usage
-----
    This module can be run directly as a script to start the BMS node:
        $ python3 <path_to_this_file>

    It can also be imported and used in other Python scripts:
        import <this_module>
        <this_module>.main()

Notes
-----
    Proper setup of the ROS2 environment is required before running this node.

"""
import sys
import rclpy
from .jbd_bms_ros import JbdBMSROS2


def main(args=None):
    """
    Initialize and run the JBD SMART BMS ROS2 node.

    This function performs the following steps:
    1. Initializes the ROS2 system.
    2. Creates a JbdBMSROS2 node.
    3. Sets up the node.
    4. Enters the ROS2 event loop (spin).
    5. Handles graceful shutdown.

    Parameters
    ----------
    args : sys, optional
           Command line arguments passed to rclpy.init().

    """
    rclpy.init(args=args)
    node = JbdBMSROS2()
    node.get_logger().info(
        f"Starting JBD BMS Node as: { node.get_name() }"
    )
    node.setup()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main(sys.argv)
