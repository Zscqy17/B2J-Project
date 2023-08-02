from xarm.wrapper import XArmAPI
import concurrent.futures
import queue
import os
from enum import Enum
import sys
import threading
import time
# 添加当前项目目录到 sys.path
sys.path.append('C:/Users/Midori/OneDrive/桌面/BMI_dj-internproject')
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

task_queue = queue.Queue()
xarm_ip_1 = "192.168.1.207"
xarm_ip_2 = "192.168.1.240"
xarm_ip_3 = "192.168.1.223"
x = op("x")
y = op("y")
z = op("z")

barrier = threading.Barrier(2)
# 列挙型の定義

class LEDMode(Enum):
    Mode1 = 1
    Mode2 = 2
    Mode3 = 3
    Mode4 = 4
    Mode5 = 5
    Mode6 = 6

class PatternMovements_1(Enum):
    Move1_left = "push_hands.traj"
    Move1_mid = "push_hands.traj"
    Move1_right = "push_hands.traj"
    
    Move2_left = "wave_hands.traj"
    Move2_mid = "wave_hands.traj"
    Move2_right = "wave_hands.traj"
    
    Move3_left = "Move1_mid.traj"
    Move3_mid = "Move1_mid.traj"
    Move3_right = "Move1_mid.traj"


class PatternMovements_2(Enum):
    WAVEHANDS_L = "WaveHands_L.traj"
    SHAKEHANDS_L = "shakeHands_L.traj"
    RAISEHANDS_L = "raisehands_L.traj"

    SHACK_R = "ShackHands_R.traj"
    PHOTO_R = "PhotoHands_R.traj"
    HELLO_R = "HelloHands_R.traj"

class UnityController():
    pass

def onValueChange(channel, sampleIndex, val, prev):
    
    is_Trigger = op("Tap_Triger").par.value0
    BMI_signal = op("BMI_signal").par.value0
    if(is_Trigger==1):
        print(BMI_signal)
        task_run(BMI_signal)
        worker_thread = threading.Thread(target=worker, args=())
        worker_thread.start()
        # 延迟放入 None，等待所有任务完成
        task_queue.put(None)
    return

def worker():
    while True:
        task = task_queue.get()
        if task is None:
            break
        excute_movments(*task)
        task_queue.task_done()


def task_run(BMI_signal):
    for i in range(1, 33):
        op("Preset_"+str(i)).par.value0 = 0
    if op("pattern1").par.value0 == 1:
        if BMI_signal == 1:
            task_queue.put((LEDMode.Mode2.value, xarm_ip_1, PatternMovements_1.Move1_left.value,
                           xarm_ip_2, PatternMovements_1.Move1_mid.value,
                           xarm_ip_3, PatternMovements_1.Move1_right.value))
            
        elif BMI_signal == 2:
            task_queue.put((LEDMode.Mode2.value, xarm_ip_1, PatternMovements_1.Move2_left.value,
                           xarm_ip_2, PatternMovements_1.Move2_mid.value,
                           xarm_ip_3, PatternMovements_1.Move2_right.value))
            
        elif BMI_signal == 3:
            task_queue.put((LEDMode.Mode2.value, xarm_ip_1, PatternMovements_1.Move3_left.value,
                           xarm_ip_2, PatternMovements_1.Move3_mid.value,
                           xarm_ip_3, PatternMovements_1.Move3_right.value))
                 
    elif op("pattern2").par.value0 == 1:
        if BMI_signal == 1:
            task_queue.put((LEDMode.Mode2.value, xarm_ip_1, PatternMovements_2.Move1_left.value,
                           xarm_ip_2, PatternMovements_2.Move1_mid.value,
                           xarm_ip_3, PatternMovements_2.Move1_right.value))

        elif BMI_signal == 2:
            task_queue.put((LEDMode.Mode2.value, xarm_ip_1, PatternMovements_2.Move2_left.value,
                           xarm_ip_2, PatternMovements_2.Move2_mid.value,
                           xarm_ip_3, PatternMovements_2.Move2_right.value))

        elif BMI_signal == 3:
            task_queue.put((LEDMode.Mode2.value, xarm_ip_1, PatternMovements_2.Move3_left.value,
                           xarm_ip_2, PatternMovements_2.Move3_mid.value,
                           xarm_ip_3, PatternMovements_2.Move3_right.value))


def led_control(self,mode):
    op("Preset_"+str(mode)).par.value0 = 1
    # Find Table
    tab = op('Presets/load')
    # Light1
    op('pan/switch1').par.index = tab[0, 0]
    op('tilt/switch1').par.index = tab[0, 1]
    op('Colors/switch1').par.index = tab[0, 2]
    # tab[0,3] = 0
    op('Strobe/switch1').par.index = tab[0, 4]
    op('view/brightness1').par.value0 = tab[0, 5]
    # Light2
    op('pan/switch2').par.index = tab[1, 0]
    op('tilt/switch2').par.index = tab[1, 1]
    op('Colors/switch2').par.index = tab[1, 2]
    # tab[0,3] = 0
    op('Strobe/switch2').par.index = tab[1, 4]
    op('view/brightness2').par.value0 = tab[1, 5]
    # Light3
    op('pan/switch3').par.index = tab[2, 0]
    op('tilt/switch3').par.index = tab[2, 1]
    op('Colors/switch3').par.index = tab[2, 2]
    # tab[0,3] = 0
    op('Strobe/switch3').par.index = tab[2, 4]
    op('view/brightness3').par.value0 = tab[2, 5]
    # Light4
    op('pan/switch4').par.index = tab[3, 0]
    op('tilt/switch4').par.index = tab[3, 1]
    op('Colors/switch4').par.index = tab[3, 2]
    # tab[0,3] = 0
    op('Strobe/switch4').par.index = tab[3, 4]
    op('view/brightness4').par.value0 = tab[3, 5]
    # Light5
    op('pan/switch5').par.index = tab[4, 0]
    op('tilt/switch5').par.index = tab[4, 1]
    op('Colors/switch5').par.index = tab[4, 2]
    # tab[0,3] = 0
    op('Strobe/switch5').par.index = tab[4, 4]
    op('view/brightness5').par.value0 = tab[4, 5]
    # Light6
    op('pan/switch6').par.index = tab[5, 0]
    op('tilt/switch6').par.index = tab[5, 1]
    op('Colors/switch6').par.index = tab[5, 2]
    # tab[0,3] = 0
    op('Strobe/switch6').par.index = tab[5, 4]
    op('view/brightness6').par.value0 = tab[5, 5]
    return


def excute_movment(ip, file_name):  # 
    print("recieve")
    speed = 50
    arm = XArmAPI(ip)
    arm.clean_error()
    arm.clean_warn()
    arm.motion_enable(enable=True)
    arm.set_mode(0)
    arm.set_state(state=0)
    arm.set_servo_angle(angle=[-0.1, -20.1, 0.2, 21.9, 0.1,
                        42.5, 1.4], speed=speed, is_radian=False, wait=False)
    arm.load_trajectory(file_name)
    if(ip!="192.168.1.207"):
        barrier.wait()
        time.sleep(1)
    arm.playback_trajectory()
    arm.set_servo_angle(angle=[-0.1, -20.1, 0.2, 21.9, 0.1,
                        42.5, 1.4], speed=speed, is_radian=False, wait=False)
    arm.disconnect()

def threading_method(ip, file_name):
    threading.Thread(target=excute_movment, args=(ip, file_name)).start()
    

def excute_movments(LEDMode=None, ip1=None, file_name1=None, ip2=None, file_name2=None,ip3=None, file_name3=None):
    print("excuting movments") 
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for ip, file_name in [(ip1, file_name1), (ip2, file_name2), (ip3, file_name3)]:
            if ip is not None and file_name is not None:
                print(ip,file_name)
                executor.submit(excute_movment, ip, file_name)
            if(LEDMode!=None):
                executor.submit(led_control, LEDMode)
    return
    