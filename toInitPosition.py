
from xarm.wrapper import XArmAPI
ip = "192.168.1.240"
speed = 50
arm = XArmAPI(ip)
arm.clean_warn()
arm.clean_error()
arm.motion_enable(enable=True)
arm.set_mode(0)
arm.set_state(state=0)
arm.set_servo_angle(angle=[-0.1, -20.1, 0.2, 21.9, 0.1,
                    42.5, 1.4], speed=speed, is_radian=False, wait=False)
arm.disconnect()