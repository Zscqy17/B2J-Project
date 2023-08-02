#import sys
from asyncio.windows_events import NULL
import os
import math
import asyncio
import argparse
import socket
from threading import Thread
import threading
import time
from typing import Any, Protocol

from numpy import BUFSIZE, array
#sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from xarm.wrapper import XArmAPI

from pythonosc.osc_server import AsyncIOOSCUDPServer
from pythonosc.dispatcher import Dispatcher
from pythonosc import udp_client
from pythonosc.osc_message_builder import OscMessageBuilder
import binascii

#-------------------Settings----------------------#
arm_ip = '192.168.1.236' # ip address of xArm-A
server_ip = '127.0.0.1' # 受信側のPCのIPアドレス
server_port = 10001 #受信ポート（Touchdesigerのosinと合わせること）
client_port = 13001 #送信ポート（Touchdesigerのosoutと合わせること）
#state = False
arm = XArmAPI(arm_ip)
init_posture = [300, 0, 100,180,0,0] #初期位置[tx ty tz rx ry rz]
global OculusPosture 
global PreviousPosture
 #初期位置[tx ty tz rz rx ry]  [x, y, z, roll, pitch, yaw]
PreviousPosture = [300, 0, 100,180, 0,0.0]
global xArm_pos
global OculusGripper
OculusGripper = 600
#bufsize = 2000

def xArm_connection():
    arm = XArmAPI(arm_ip)

    #アームの位置を初期化する
    connected_ip = arm.motion_enable(enable=True)
    print('connected:{}'.format(connected_ip))
    arm.set_mode(0)                             #position control mode   
    arm.set_state(0)                            #Set the xArm state :param state: default is 0 ,0: sport state
    arm.clean_error()
    arm.clean_warn()
    #arm.set_position = init_posture        #set init position
    arm.set_position(x =300 ,y = 0,z = 100,roll=-180, pitch=0, yaw=0, speed=100, is_radian=False, wait=True)
    print("setted init" )
    arm.set_gripper_mode(0)
    arm.set_tgpio_modbus_baudrate(2000000)
    arm.set_gripper_enable(True)
    arm.set_gripper_position(600,wait=True, speed=5000)

    arm.set_mode(1)
    arm.set_state(0)


def xArm_disconnection(unused_addr, *args):
    print('disconnection')
    #arm.state = 4                               # stoppingarm_init_position
    arm.set_position(init_posture)
    arm.clean_error()
    arm.clean_warn()
    arm.reset(wait=True)
    arm.disconnect()

def clean_error(unused_addr, *args):
    global arm, state
    arm.clean_error()
    arm.clean_warn()
    print('clean error and warn')
    state = True


def updateValue(unused_addr, *args):
    global PreviousPosture
    OculusPosture = [args[0],args[1],args[2],args[3],args[4],args[5],args[6]]
    mode,Cur = arm.get_position(is_radian=True)
    Grip = arm.get_gripper_position
    PreviousPosture = [Cur[0],Cur[1],Cur[2],Cur[3],Cur[4],Cur[5]]
    print('PreviousPosture x :',PreviousPosture)
    print('OculusPosture x :',OculusPosture[0])

    dX = OculusPosture[0] - PreviousPosture[0]
    dY = OculusPosture[1] - PreviousPosture[1]
    dZ = OculusPosture[2] - PreviousPosture[2]
    Diff_sum = dX**2 + dY**2 + dZ**2
    Diff = round(math.sqrt(Diff_sum),1)
    print("Diff: ", Diff)
    
    if  210 < OculusPosture[0] < 600 and -500< OculusPosture[1] < 500 and 20 < OculusPosture[2] < 500:
        #checking limitation
        MAX_STEP_MM = 16
    
        if(Diff > MAX_STEP_MM ):
            #when exceed step value, limiting with MAX_STEP_MM
            dX = dX * ( MAX_STEP_MM / Diff )
            dY = dY * ( MAX_STEP_MM / Diff )
            dZ = dZ * ( MAX_STEP_MM / Diff )
            print("dX dY dZ",dX,dY,dZ)
        
        cmdPosX = round(PreviousPosture[0] + dX,1)
        cmdPosY = round(PreviousPosture[1] + dY,1)
        cmdPosZ = round(PreviousPosture[2] + dZ,1)

        cmd_posture = [ cmdPosX, cmdPosY, cmdPosZ, OculusPosture[3], OculusPosture[4], OculusPosture[5],OculusPosture[6]]
       
        arm.set_servo_cartesian(cmd_posture)
        #これだと動かない
        #arm.set_position(x=args[0], y=args[1], z=args[2], roll=args[3], pitch=args[4], yaw=args[5])
        arm.getset_tgpio_modbus_data(ConvertToModbusData(args[6]))
        print('arm posture : ' ,cmd_posture)
        PreviousPosture = cmd_posture
    else:
        print("out of limit")


def ConvertToModbusData(value: int):
    """
    Converts the data to modbus type.

    Parameters
    ----------
    value: int
        The data to be converted.
        Range: 0 ~ 800
    """

    if int(value) <= 255 and int(value) >= 0:
        dataHexThirdOrder = 0x00
        dataHexAdjustedValue = int(value)

    elif int(value) > 255 and int(value) <= 511:
        dataHexThirdOrder = 0x01
        dataHexAdjustedValue = int(value)-256

    elif int(value) > 511 and int(value) <= 767:
        dataHexThirdOrder = 0x02
        dataHexAdjustedValue = int(value)-512

    elif int(value) > 767 and int(value) <= 1123:
        dataHexThirdOrder = 0x03
        dataHexAdjustedValue = int(value)-768

    modbus_data = [0x08, 0x10, 0x07, 0x00, 0x00, 0x02, 0x04, 0x00, 0x00]
    modbus_data.append(dataHexThirdOrder)
    modbus_data.append(dataHexAdjustedValue)
    
    return modbus_data
    

if __name__ == '__main__': #インポートされただけでは実行しない　プログラム実行時のみ実行
    from pythonosc import dispatcher
    from pythonosc import osc_server
    xArm_connection()

    print('test')
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default="127.0.0.1", help="The ip to listen on")
    parser.add_argument("--port", type=int, default=client_port, help="The port to listen on")
    args = parser.parse_args()

    dispatcher = dispatcher.Dispatcher()
    dispatcher.map('/connection', xArm_connection)
    dispatcher.map('/disconnection', xArm_disconnection)
    #dispatcher.map("/debug", print)
    dispatcher.map("/clean", clean_error)
    dispatcher.map("/motion", updateValue)

    server = osc_server.ThreadingOSCUDPServer((args.ip, args.port), dispatcher)
    print("Serving on {}".format(server.server_address))
    #client = udp_client.SimpleUDPClient(args.ip,client_port)
    server.serve_forever()



    
