import numpy as np
from xarm.wrapper import XArmAPI
from transforms3d.quaternions import quat2mat
import csv
import math

def quaternion_to_euler(qx, qy, qz,qw ):
    x, y, z,w = qx, qy, qz,qw 

    roll = math.atan2(2*(w*x + y*z), 1 - 2*(x**2 + y**2))
    pitch = math.asin(2*(w*y - z*x))
    yaw = math.atan2(2*(w*z + x*y), 1 - 2*(y**2 + z**2))
    return [roll, pitch, yaw]  # return  [roll, pitch, yaw]


def main():
    
    arm = XArmAPI('192.168.1.223',is_radian=True)
    arm.motion_enable(True)
    arm.set_mode(0)
    arm.set_state(0)
    arm.set_servo_angle(angle=[-0.1,-20.1, 0.2,21.9,0.1,42.5,1.4], speed=50, is_radian=False, wait=True)
    pre_position = arm.get_position()[1]
    original_position = arm.get_position()[1]
    data=[]
    #data=[[-0.1,-20.1, 0.2,21.9,0.1,42.5,1.4],[-0.1,-27.2,0.1,100.4,0.2,-23.3,1.2],[63.2,-39.2,-36.8,112.5,-25.5,-11.3,-12.5],[-62.2,-38.7,36.9,112.1,26.2,-118,13.5],[-0.1,-27.2,0.1,100.4,0.2,-23.3,1.2]]
    with open('models/smallwave.csv', 'r') as f:
        reader = csv.reader(f)
        next(reader)  #skip first line
        for row in reader:
            x = float(row[0])
            y = float(row[1])
            z = float(row[2])
            qx = float(row[3])
            qy = float(row[4])
            qz = float(row[5])
            qw= float(row[6])
            roll, pitch, yaw = quaternion_to_euler(qx,qy,qz,qw)
            data.append([x,y,z,roll,pitch,yaw])
        
    #for i in range(len(data)-1):
        #j=i+1
        # changed_data = [data[j][0]-data[i][0],data[j][1]-data[i][1],data[j][2]-data[i][2],data[j][3]-data[i][3],data[j][4]-data[i][4],data[j][5]-data[i][5]]
        # next_position = [original_position[0]-changed_data[0]*2000000,original_position[1]-changed_data[1]*2000000,original_position[2]-changed_data[2]*2000000,original_position[3]-changed_data[3], original_position[4]-changed_data[4], original_position[5]-changed_data[5]]
        # arm.set_position(next_position[0],next_position[1],next_position[2],next_position[3],next_position[4],next_position[5],is_radian=True,wait=False)

    for i in range(0,len(data),100):
        changed_data = [data[i][0]-data[0][0],data[i][1]-data[0][1],data[i][2]-data[0][2],data[i][3]-data[0][3],data[i][4]-data[0][4],data[i][5]-data[0][5]]
        next_position=[original_position[0]-1000*changed_data[0],original_position[1]-1000*changed_data[1],original_position[2]-1000*changed_data[2],original_position[3]-changed_data[3],original_position[4]-changed_data[4],original_position[5]-changed_data[5]]

        arm.set_position(next_position[0],next_position[1],next_position[2],next_position[3],next_position[4],next_position[5],is_radian=True,wait=False)

        # print(arm.get_position())
        # print(next_position)
    arm.disconnect()
    # for angles in data:
    #     print(angles)
    #     arm.set_servo_angle(angle=angles, speed=50, is_radian=False, wait=True)
    # arm.set_servo_angle(angle=[-0.1,-20.1, 0.2,21.9,0.1,42.5,1.4], speed=50, is_radian=False, wait=True)
    # arm.disconnect()
    # f.close()
    #arm.set_position(x=300, y=100, z=200, roll=-3.14, pitch=0, yaw=0, is_radian=True,wait=True)
    # for i in range(len(data)):
    #     arm.set_position(data[i][0],data[i][1],data[i][2],data[i][3],data[i][4],data[i][5], speed=50, is_radian=True, wait=True)
    #arm.set_servo_angle(angle=[-20.1, -23.1, 123.2, 21.9, 234.1, 42.5, 1.4], speed=50, is_radian=True, wait=True)
    
if __name__ == "__main__":
    main()
