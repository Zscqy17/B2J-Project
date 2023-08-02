#!/usr/bin/python3
from logging import shutdown
import socket
import threading
import tkinter as tk
from tkinter import ttk
from tkinter.constants import N
from pythonosc import dispatcher
from pythonosc import osc_server
from pymycobot.mycobot import MyCobot
from pymycobot import PI_PORT, PI_BAUD
import re
from enum import Enum
import time
old_stage =0
current_stage=0
currentButtonStage=0
robot_arm_port= "/dev/ttyAMA0" 
baud = 1000000
PI_PORT =robot_arm_port
PI_BAUD=baud
is_calibrated = False 

class OnStageMovements(Enum):
    Rhythm_L=1
    Clap_Hands=2
    Rhythm_R=3
    Hand_Up_L=4
    Fever_Max=5
    Hand_Up_R=6
    Point_Finger_L=7
    Flash_Light=8
    Point_Finger_R=9

class OffStageMovements(Enum):
    Horizontal_Fetch_Left=1
    Horizontal_Fetch_Mid=2
    Horizontal_Fetch_Right=3
    Vertical_Fetch_Left=4
    Vertical_Fetch_Mid=5
    Vertical_Fetch_Right=6
    Hit_Left=7
    Hit_Mid=8
    Hit_Right=9

def get_local_ip():
    """获取本地IP"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.grid()
        self.create_widgets()
        self.mycobot = None
        self.connect_mycobot()
        self.server_BMI=None
        self.server_TAP=None
        self.client_BMI_callback = None
        self.stop_signal = False
        self.is_calibrated = False
        self.server_thread=None
        self.server_tap_thread = None
        self.client_BMI_callback_thread = None
        self.bmi_addr=""

    def destroy(self):
        self.restart_server()
        return super().destroy()

    def create_widgets(self):
        self.ip_label = tk.Label(self, text="Arm IP:")
        self.ip_label.grid(row=0, column=0, sticky='w')

        self.ip_info = tk.Label(self, text=get_local_ip())
        self.ip_info.grid(row=0, column=1, sticky='w')

        self.port_label = tk.Label(self, text="Arm Port:")
        self.port_label.grid(row=1, column=0, sticky='w')

        self.port_entry = tk.Entry(self)
        self.port_entry.insert(0,"12345")
        self.port_entry.grid(row=1, column=1, sticky='w')

        self.confirm_button = tk.Button(self, text="Port Confirm", command=self.confirm, width=20)
        self.confirm_button.grid(row=1, column=2)

        self.mycobot_state = tk.Label(self, text="Mycobot State: ")
        self.mycobot_state.grid(row=2, column=0, sticky='w')

        self.mycobot_state_info = tk.Label(self,text=self.get_mycobot_state_info())
        self.mycobot_state_info.grid(row=2, column=1, sticky='w')

        self.calibrate_button = tk.Button(self, text="Calibrate", command=self.calibrate, width=20)
        self.calibrate_button.grid(row=2, column=2)

        self.tap_system_stage= tk.Label(self, text="Tap System Stage: ")
        self.tap_system_stage.grid(row=3, column=0, sticky='w')

        self.tap_system_info= tk.Label(self, text="Did not link")
        self.tap_system_info.grid(row=3, column=1, sticky='w')

        self.BMI_mode_label = tk.Label(self, text="Change BMI Mode: ")
        self.BMI_mode_label.grid(row=4, column=0, sticky='w')

        self.BMI_mode_var = tk.StringVar(self)
        self.BMI_mode_var.set("3 Selections")
        self.BMI_mode_option = ttk.Combobox(self, textvariable=self.BMI_mode_var, state="readonly")
        self.BMI_mode_option['values'] = ('3 Selections', '9 Selections')
        self.BMI_mode_option.grid(row=4, column=1, sticky='w')
        #self.BMI_mode_option.bind('<<ComboboxSelected>>', self.on_BMI_mode_change)

        self.movement_pattern_label = tk.Label(self, text="Change Movement Pattern: ")
        self.movement_pattern_label.grid(row=5, column=0, sticky='w')
        self.movement_pattern_var = tk.StringVar(self)
        self.movement_pattern_var.set("On Stage")
        self.movement_pattern_option = ttk.Combobox(self, textvariable=self.movement_pattern_var, state="readonly")
        self.movement_pattern_option['values'] = ('On Stage', 'Off Stage')
        self.movement_pattern_option.grid(row=5, column=1, sticky='w')
        #self.movement_pattern_option.bind('<<ComboboxSelected>>', self.on_movement_mode_change)

        self.signal_label = tk.Label(self, text="Get Signal: ")
        self.signal_label.grid(row=6, column=0, sticky='w')

        self.signal_info = tk.Label(self)
        self.signal_info.grid(row=6, column=1, sticky='w')

        self.release_button = tk.Button(self, text="Release Robot", command=self.release, width=20)
        self.release_button.grid(row=7, column=2)

    def release(self):
        self.mycobot.release_all_servos()

    def restart_server(self):
        self.stop_signal = True
        if self.server_BMI is not None:
            self.server_BMI.close()
        if self.server_TAP is not None:
            self.server_TAP.shutdown()
            self.server_TAP.server_close()
        if self.client_BMI_callback is not None:
            
            self.client_BMI_callback.close()


    def confirm(self):
        self.restart_server()
        self.stop_signal = False
        self.port = int(self.port_entry.get())
        self.start_server()

    def calibrate(self):
        if self.mycobot is None:
            return
        self.mycobot_state_info["text"]="Waiting..."
        server_thread = threading.Thread(target=self.calibrate_thread, args=())
        server_thread.start()

        
    def calibrate_thread(self):
        global is_calibrated
        for calibration_num in range(7):
            self.mycobot.set_servo_calibration(calibration_num)
            time.sleep(0.1)
            self.mycobot.send_angle(calibration_num, 0, 0)
            time.sleep(0.1)
            is_calibrated = True
            
        self.calibration_num = None
        self.rectify_mycobot()
        self._calibration_test()
        self.mycobot_state_info["text"]=self.get_mycobot_state_info()

    def rectify_mycobot(self):
        if not self.mycobot:
            return

        data_id = [21, 22, 23, 24, 26, 27]
        data    = [10, 0, 1, 0, 3, 3]
        for i in range(1,7):
            for j in range(len(data_id)):
                self.mycobot.set_servo_data(i, data_id[j], data[j])
                time.sleep(0.2)
                _data = self.mycobot.get_servo_data(i, data_id[j])
                time.sleep(0.2)
                # if _data == data[j]:
                #     self.write_log_to_Text("Servo motor :" + str(i) + "  data_id : " + str(data_id[j]) + "   data: " + str(_data) + "  modify successfully ")
                # else:
                #     self.write_log_to_Text("Servo motor :"  + str(i) + "  data_id : " + str(data_id[j]) + "   data: " + str(_data) + "  modify error ")
    
    def _calibration_test(self):
        #self.write_log_to_Text("开始测试校准.")
        angles = [0, 0, 0, 0, 0, 0]
        test_angle = [-20, 20, 0]
        for i in range(6):
            for j in range(3):
                angles[i] = test_angle[j]
                self.mycobot.send_angles(angles, 0)
                time.sleep(0.7)
        #self.write_log_to_Text("测试校准结束.")
    def get_mycobot_state_info(self):
        global is_calibrated
        if is_calibrated:
            return "Calibrated!"
        else:
            return "Did not Calibrate"

    def start_server(self):
        self.server_thread = threading.Thread(target=self.server, args=(self.port,))
        self.server_thread.start()
        self.server_tap_thread = threading.Thread(target=self.server_tap, args=())
        self.server_tap_thread.start()
        

    def start_client_BMI_callback(self):
        isConnect=False
        while not isConnect and self.bmi_addr!="":
            try:
                self.client_BMI_callback = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_BMI_callback.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
                self.client_BMI_callback.connect((self.bmi_addr,9001))
                isConnect = True
            except socket.error as e:
                time.sleep(0.1)
                

    def process_3BMI_command(self, command):
        if(self.movement_pattern_var.get()=="On Stage"):
            if command in (e.value for e in OnStageMovements):
                command_name = OnStageMovements(command).name
                self.signal_info['text'] = command_name
            else:
                self.signal_info['text']= "Get a wrong Command!"
        else:
            if command in (e.value for e in OffStageMovements):
                command_name = OffStageMovements(command).name
                self.signal_info['text'] = command_name
            else:
                self.signal_info['text']= "Get a wrong Command!"

    def process_9BMI_command(self,r_value, c_value):
        command = 3 * ( int(r_value) - 1) + int(c_value)
        if(self.movement_pattern_var.get()=="On Stage"):
            if command in (e.value for e in OnStageMovements):
                command_name = OnStageMovements(command).name
                self.signal_info['text'] = command_name
            else:
                self.signal_info['text']= "Get a wrong Command!"
        else:
            if command in (e.value for e in OffStageMovements):
                command_name = OffStageMovements(command).name
                self.signal_info['text'] = command_name
            else:
                self.signal_info['text']= "Get a wrong Command!"

    def server(self, port):
        try:
            self.server_BMI = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_BMI.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            self.server_BMI.bind(('0.0.0.0', port))
            self.server_BMI.listen(1)
            self.signal_info['text']="Current port works"
            c, addr = self.server_BMI.accept()
            self.signal_info['text']= "Connected!"
            self.bmi_addr = str(addr[0])
            
            self.client_BMI_callback_thread = threading.Thread(target=self.start_client_BMI_callback, args=())
            self.client_BMI_callback_thread.start()

            r_received = False
            c_received = False
            r_value = None
            c_value = None
            while not self.stop_signal:
                
                data = c.recv(1024).decode('utf-8')
                if not data:
                    break
                # 使用正则表达式解析数据
                
                if self.BMI_mode_var.get()=="9 Selections":
                    match = re.match('^([1-3])([RrCc])$', data)
                    if match:
                        self.signal_info['text']= data
                        value, type = match.groups()
                        if type == 'r' or type == 'R' and not c_received:
                            r_received = True
                            r_value = value
                        elif type == 'c' or type == 'C' and r_received:
                            c_received = True
                            c_value = value
                    else:
                        self.signal_info['text']= "Get a wrong Data!"

                    # 只有当 'r' 和 'c' 都已收到后才处理命令

                    if r_received and c_received:
                        self.process_9BMI_command(r_value, c_value)
                        # 重置标志以便于处理下一个命令
                        r_received = False
                        c_received = False
                        r_value = None
                        c_value = None
                else:
                    match = re.match('^[1-3]$', data)
                    if match:
                        command = int(data)
                        self.process_3BMI_command(command)
                    else:
                        self.signal_info['text']= "Get a wrong Data!"
            c.close()
        except:
            self.signal_info['text']= "Please change another port!"
            # self.robot_command(int(signal))
                # client_socket.close()
        # except:
        #     self.signal_info['text']="Please change to another port"

    def set_the_signal(self,unused_addr, args):
        global currentButtonStage
        global old_stage 
        global current_stage
        global currentButtonStage
        old_stage= current_stage
        currentButtonStage = int(args)
        current_stage= currentButtonStage
        if old_stage != current_stage:
            self.tap_system_info['text'] = "Works"
            ori_str = self.signal_info['text']
            if(self.client_BMI_callback is not None):
                self.client_BMI_callback.sendall(str(current_stage).encode('utf-8'))
            if(current_stage == 1 and (hasattr(OnStageMovements,ori_str) or hasattr(OffStageMovements,ori_str))):
                
                if(self.movement_pattern_var.get()=="On Stage" and hasattr(OnStageMovements,ori_str)):
                    movement = OnStageMovements[ori_str]
                elif(self.movement_pattern_var.get()=="Off Stage" and hasattr(OffStageMovements,ori_str)):
                    movement = OffStageMovements[ori_str]
                
                self.signal_info['text'] = ori_str +"  Activating!"
                self.robot_command(int(movement.value))
                self.signal_info['text']=ori_str+ "  Activated!"
                self.client_BMI_callback.sendall(str(2).encode('utf-8'))
            else:
                return 
        else:
            return
        

    def server_tap(self):
        disp = dispatcher.Dispatcher()
        disp.map("/theport", self.set_the_signal)
        self.server_TAP = osc_server.ThreadingOSCUDPServer(("0.0.0.0", 20000), disp)
        self.server_TAP.socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.server_TAP.serve_forever()

    def robot_move(self,angles1,speed1,angles2,speed2):
        count = 0
        while count<4:
            self.mycobot.wait(1).send_angles(angles1, speed1)
            self.mycobot.wait(1).send_angles(angles2, speed2)           
            count+=1

    def robot_command(self,signal=0):
        if(self.movement_pattern_var.get()=="On Stage"):
            if(signal==1):
                
                self.mycobot.set_color(255, 0, 0)
                self.robot_move([16.34, -14.15, -8.52, 51.15, 59.41, -29.0],50,[17.22, 21.44, -8.52, 0.0, 60.99, -45.96],50)
                self.mycobot.set_gripper_value(154,50)
            elif(signal==2):
                
                self.mycobot.set_color(0, 255, 0)
                self.robot_move([15.02, 0.52, -1.05, -3.51, 71.36, -46.93],80,[15.02, 4.48, -0.96, 3.25, -92.28, -39.81],80)
                self.mycobot.set_gripper_value(154,50)

            elif(signal==3):
                
                self.mycobot.set_color(0, 0, 255)
                self.robot_move([27.68, 8.08, -0.7, -28.91, -47.98, -39.9],50,[28.56, 10.89, -0.79, 11.6, -49.57, -39.9],50)
                self.mycobot.set_gripper_value(154,50)
            elif(signal==4):
                self.mycobot.set_gripper_value(254,50)
                self.mycobot.set_color(255, 125, 125)
                self.mycobot.send_angles([11.42, 0.17, -0.26, 92.54, 51.15, -23.81],50)
                # self.robot_move([-68.2, 4.57, 87.36, -7.11, 93.25, -120.67],70,[-99.75, 6.32, 86.74, -6.85, 92.28, -120.67],70)

            elif(signal==5):
                
                self.mycobot.set_color(125, 255, 125)
                self.mycobot.send_angles([11.42, 0.17, -0.26, 91.05, 0.87, -38.84],50)
                self.mycobot.set_gripper_value(154,50)
                # self.robot_move([-101.25, -17.13, 87.53, 105.99, 54.75, -120.58],70,[-139.83, 0.17, 87.45, 87.89, 24.96, -120.58],70)

            elif(signal==6):
                self.mycobot.set_color(125, 125, 255)
                self.mycobot.send_angles([17.4, 4.57, -0.35, 83.75, -55.81, -50.18],50)
                self.mycobot.set_gripper_value(154,50)
                # self.robot_move([-78.13, -0.08, -86.57, 0.17, 79.1, -120.58],70,[-47.1, -0.08, -86.57, 0.79, 78.57, -120.67],70)
            elif(signal==7):
                
                self.mycobot.set_color(255, 125, 0)
                self.mycobot.send_angles([14.5, 7.38, -0.79, 2.37, 34.62, -138.07],50)
                self.mycobot.set_gripper_value(1,50)
                # self.robot_move([-65.83, 84.37, 6.32, -7.99, 98.34, 1.23],70,[-88.41, 83.67, 6.32, -6.32, 97.47, 1.23],70)

            elif(signal==8):
                self.mycobot.set_color(0, 255, 125)
                self.mycobot.send_angles([14.41, 7.47, -0.26, -0.7, 0.61, -137.81],50)
                self.mycobot.set_gripper_value(1,50)
                # self.robot_move([-56.25, -1.58, 120.32, 48.69, 105.29, 1.23],70,[-130.16, -0.7, 121.2, 52.91, 38.93, 1.23],70)

            elif(signal==9):
                self.mycobot.set_color(125, 0, 255)
                self.mycobot.send_angles([14.5, 6.24, -0.35, 0.08, -30.67, -137.81],50)
                self.mycobot.set_gripper_value(1,50)
                # self.robot_move([-80.24, -82.44, -7.29, 1.4, 78.22, 1.05],70,[-52.2, -80.33, -7.03, 10.19, 75.41, 1.05],70)
        else:
            if(signal==1):
                self.mycobot.set_color(255, 0, 0)
                self.robot_move([131.22, -43.94, -2.63, 54.31, -111.0, -119.09],70,[99.49, -47.19, -3.07, 51.41, -80.94, -119.09],70)

            elif(signal==2):
                self.mycobot.set_color(0, 255, 0)
                self.robot_move([24.08, 18.89, -2.37, -20.21, -11.51, -118.91],70,[23.55, -20.39, -2.19, 20.56, -11.51, -118.91],70)

            elif(signal==3):
                self.mycobot.set_color(0, 0, 255)
                self.robot_move([62.57, 49.13, -1.66, -50.62, -65.3, -119.26],70,[109.16, 50.53, -1.75, -54.93, -111.88, -119.26],70)
            elif(signal==4):
                self.mycobot.set_color(255, 0, 0)
                self.robot_move([-68.2, 4.57, 87.36, -7.11, 93.25, -120.67],70,[-99.75, 6.32, 86.74, -6.85, 92.28, -120.67],70)

            elif(signal==5):
                self.mycobot.set_color(0, 255, 0)
                self.robot_move([-101.25, -17.13, 87.53, 105.99, 54.75, -120.58],70,[-139.83, 0.17, 87.45, 87.89, 24.96, -120.58],70)

            elif(signal==6):
                self.mycobot.set_color(0, 0, 255)
                self.robot_move([-78.13, -0.08, -86.57, 0.17, 79.1, -120.58],70,[-47.1, -0.08, -86.57, 0.79, 78.57, -120.67],70)
            elif(signal==7):
                self.mycobot.set_color(255, 0, 0)
                self.robot_move([-65.83, 84.37, 6.32, -7.99, 98.34, 1.23],70,[-88.41, 83.67, 6.32, -6.32, 97.47, 1.23],70)

            elif(signal==8):
                self.mycobot.set_color(0, 255, 0)
                self.robot_move([-56.25, -1.58, 120.32, 48.69, 105.29, 1.23],70,[-130.16, -0.7, 121.2, 52.91, 38.93, 1.23],70)

            elif(signal==9):
                self.mycobot.set_color(0, 0, 255)
                self.robot_move([-80.24, -82.44, -7.29, 1.4, 78.22, 1.05],70,[-52.2, -80.33, -7.03, 10.19, 75.41, 1.05],70)
            

    def connect_mycobot(self):

        try:
            self.mycobot = MyCobot(robot_arm_port, baud)
            self.mycobot.set_gripper_ini()
            self.mycobot.send_angles([0,0,0,0,0,0],30)
            # self.mycobot = MyCobot("/dev/cu.usbserial-0213245D", 115200)
            print("connect succeed!")
        except Exception as e:
            self.mycobot = MyCobot(robot_arm_port, baud)
            err_log = """\
                \connect failed !!!
                \r=================================================
                {}
                \r=================================================
            """.format(
                e
            )
            print(err_log)

root = tk.Tk()
root.title("Mycobot Control System")
app = Application(master=root)
app.mainloop()
