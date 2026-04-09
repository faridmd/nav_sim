#!/usr/bin/env python3
# from __future__ import print_function

import argparse

import rospy
import sys, select, termios, tty
from tf.transformations import quaternion_from_euler
from sensor_msgs.msg import Joy
from std_msgs.msg import Header, Float64
from geometry_msgs.msg import PoseStamped, TwistStamped, Vector3, Quaternion, Point
from mavros_msgs.msg import OverrideRCIn
from mavros_msgs.srv import CommandBool
from mavros_msgs.srv import CommandTOL
from mavros_msgs.srv import SetMode

def getKey():
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
    if rlist:
        key = sys.stdin.read(1)
    else:
        key = ''

    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key


def arm(args, state):
    try:
        arming_cl = rospy.ServiceProxy(args.mavros_ns + "/cmd/arming", CommandBool)
        ret = arming_cl(value=state)
    except rospy.ServiceException as ex:
        rospy.logerr(ex)

    if not ret.success:
        rospy.loginfo("ARM Request failed.")
    else:
        rospy.loginfo("ARM Request success.")

def takeoff(args):
    try:
        takeoff_cl = rospy.ServiceProxy(args.mavros_ns + "/cmd/takeoff", CommandTOL)
        
        ret = takeoff_cl(altitude=2, latitude=0, longitude=0, min_pitch=0, yaw=0)
    except rospy.ServiceException as ex:
        rospy.logerr(ex)

    if not ret.success:
        rospy.loginfo("TAKEOFF Request failed.")
    else:
        rospy.loginfo("TAKEOFF Request success.")

def set_mode(args, mode):
    try:
        setmode_cl = rospy.ServiceProxy(args.mavros_ns + "/set_mode", SetMode)
        
        ret = setmode_cl(base_mode=0, custom_mode=mode)
        rospy.loginfo(ret)
    except rospy.ServiceException as ex:
        rospy.logerr(ex)

    if not ret.mode_sent:
        rospy.loginfo("SET MODE Request failed.")
    else:
        rospy.loginfo("SET MODE Request success.")


def rc_override_control(args):
    
    rospy.init_node("mavteleop")
    rospy.loginfo("MAV-Teleop: RC Override control type.")
    

    override_pub = rospy.Publisher(args.mavros_ns + "/rc/override", OverrideRCIn, queue_size=4)
    
    throttle_ch = 1000

        
    while(1):
        if throttle_ch < 1000:
            throttle_ch = 1000
        elif throttle_ch > 2000:
            throttle_ch = 2000

        roll = 1500
        pitch = 1500
        yaw = 1500
        print('ROLL PITCH THROTTLE YAW')
        print([roll, pitch, throttle_ch, yaw])
        key = getKey()
        print('KEY :', key)
        #rospy.loginfo("Key: %s", key)
        if key == 'a':
            arm(args, True)
        elif key == 'd':
            arm(args, False)
        elif key == 't':
            takeoff(args)
        elif key == 'h':
            if throttle_ch == 1000:
                throttle_ch = 1500
            set_mode(args, "ALT_HOLD")
        elif key == 'g':
            if throttle_ch != 1000:
                throttle_ch = 1000
            set_mode(args, "GUIDED")
        elif key == 's':
            throttle_ch = 1500
            set_mode(args, "STABILIZE")
        elif key == 'c':
            set_mode(args, "LAND")
        elif key == 'b':
            set_mode(args, "BRAKE")
        elif key == 'r': #UP
            throttle_ch+=10
        elif key == 'f': #FIX
            throttle_ch=1500
        elif key == 'v': #DOWN
            throttle_ch-=10 
        elif key == 'j': #LEFT
            roll=1400   
        elif key == 'l': #RIGHT
            roll=1600   
        elif key == 'i': #FORWARD
            pitch=1400 
        elif key == 'k': #BACKWARD
            pitch=1600  
        elif key == 'n': #yaw left
            yaw=1400  
        elif key == 'm': #yaw right
            yaw=1600  	    
        if (key == '\x03'):
            set_mode(args, "GUIDED")
            break
        
        rc = OverrideRCIn()
        rc.channels[0] = roll
        rc.channels[1] = pitch
        rc.channels[2] = throttle_ch
        rc.channels[3] = yaw #yaw
        rc.channels[4] = 0
        rc.channels[5] = 0
        rc.channels[6] = 0
        rc.channels[7] = 0
        
        #rospy.loginfo("Channels: %d %d %d %d", rc.channels[0], rc.channels[1],rc.channels[2] , rc.channels[3])
        
        override_pub.publish(rc)


def main():
    parser = argparse.ArgumentParser(description="Teleoperation script for Copter-UAV")
    parser.add_argument('-n', '--mavros-ns', help="ROS node namespace", default="/mavros")
    parser.add_argument('-v', '--verbose', action='store_true', help="verbose output")
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('-rc', '--rc-override', action='store_true', help="use rc override control type")
    mode_group.add_argument('-att', '--sp-attitude', action='store_true', help="use attitude setpoint control type")
    mode_group.add_argument('-vel', '--sp-velocity', action='store_true', help="use velocity setpoint control type")
    mode_group.add_argument('-pos', '--sp-position', action='store_true', help="use position setpoint control type")

    args = parser.parse_args(rospy.myargv(argv=sys.argv)[1:])

    if args.rc_override:
        rc_override_control(args)


if __name__ == '__main__':
    settings = termios.tcgetattr(sys.stdin)
    main()
