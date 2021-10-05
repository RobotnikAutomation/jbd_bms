#!/usr/bin/env python
# -*- coding: utf-8 -*-

import rospy
from jbd_bms import JbdBms


def main():

    rospy.init_node("jbd_bms_node")

    rc_node = JbdBms()

    rospy.loginfo('%s: starting' % (rospy.get_name()))

    rc_node.start()


if __name__ == "__main__":
    main()
