#!/usr/bin/env python
import rospy
from geometry_msgs.msg import Twist

def walking_test():
    # init node
    rospy.init_node('walking_test_node', anonymous=True)
    # set publisher
    pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
    # 10 Hz
    rate = rospy.Rate(10)

    # create message
    msg = Twist()
    msg.linear.x = 0.2

    while not rospy.is_shutdown():
        # publish the message
        pub.publish(msg)
        rate.sleep()

if __name__ == '__main__':
    try:
        walking_test()
    except rospy.ROSInterruptException:
        pass
