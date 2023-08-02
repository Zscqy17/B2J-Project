# me - this DAT
# 
# frame - the current frame
# state - True if the timeline is paused
# 
# Make sure the corresponding toggle is enabled in the Execute DAT.
import warnings
import sys, os
path = ".\\Lib\\site-packages\\xArm_Python_SDK-1.8.0-py3.9.egg"
pyVersion = sys.version
if '3.9.5' in pyVersion:
	path = ".\\Lib\\site-packages\\xArm_Python_SDK-1.8.0-py3.9.egg"
elif '3.7.2' in pyVersion:
	path = ".\\Lib_2021\\site-packages\\xArm_Python_SDK-1.8.0-py3.7.egg"
sys.path.insert(0,path)
import time
import numpy as np
import traceback
with warnings.catch_warnings():
	warnings.simplefilter('ignore', DeprecationWarning)
	from xarm.wrapper import XArmAPI
import xArmTransform
# ----- Set variables ----- #
participantNum 	= int(op('numSettings')['participantNum'])
xArmNum			= int(op('numSettings')['xArmNum'])
xArmIpAddress	= ['192.168.1.' + str(int(name[0])) for name in op('xArmNameSettings').numpyArray()]
# ----- Get operator ----- #
dictPositionOp 	= {}
dictRotationOp 	= {}
dictGripperOp	= {}
for i in range(xArmNum):
	dictPositionOp['arm'+str(i+1)] 	= op('positionArm'+str(i+1))
	dictRotationOp['arm'+str(i+1)] 	= op('rotationArm'+str(i+1))
	dictGripperOp['arm'+str(i+1)]	= op('gripperArm'+str(i+1))
# ----- Process info ----- #
loopCount      = 0
taskTime       = 0
errorCount     = 0
taskStartTime  = 0
# ----- xArm settings ----- #
xArms = []
xArmTransforms = []
isEnablexArm = op(me.parent()).par.Isenable
# ----- task settings ----- #
executionTime = op('taskSettings')['execTime']
# ----- Control flags ----- #
isTaskReady     = False
isMoving        = False
isCompleteTask  = False
isMovingToInit	= False
isEnableFixedTaskTime = False
# ----- Internal flags ----- #
isPrintData         = False     # For debug
def onStart():
	# ----- Initialize robot arm ----- #
	for i in range(xArmNum):
		t = xArmTransform.xArmTransform()
		xArmTransforms.append(t)
		if isEnablexArm:
			xarm = XArmAPI(xArmIpAddress[i])
			xArms.append(xarm)
			InitRobotArm(xarm, t)
			
			if me.parent().par.Isenablegripper:
				InitGripper(xarm)
	
	global executionTime
	executionTime = op('taskSettings')['execTime']
	return
def onCreate():
	return
def onExit():
	global xArms
	for arm in xArms:
		arm.disconnect()
	
	xArms = []
	return
def onFrameStart(frame):
	global isTaskReady, isMoving, isMovingToInit, isCompleteTask, taskStartTime, taskTime, loopCount, errorCount
	if isCompleteTask:
		# ----- Complete task ----- #
		isCompleteTask 	= False
		isMoving 		= False
		taskTime 		= time.perf_counter() - taskStartTime
		
		PrintProcessInfo()
		print('----- RobotArmController.execute_robot_control >>  Finish task -----')
	if isEnableFixedTaskTime and time.perf_counter() - taskStartTime > executionTime:
		# ----- Exit processing after `executionTime` elapses ----- #
		isMoving        = False
		isCompleteTask  = True
	
	if op(me.parent()).par.Initall:
		isTaskReady 	= True
		isCompleteTask	= False
		isMovingToInit	= False
	
	if isTaskReady and op(me.parent()).par.Taskstart:
		isTaskReady 	= False
		isMoving 		= True
		taskStartTime 	= time.perf_counter()
	
	if isMoving and op(me.parent()).par.Taskstop:
		isMoving 		= False
		isTaskReady 	= False
		isCompleteTask 	= True
	
	if isMoving:
		# ----- Send to xArm ----- #
		for i in range(xArmNum):
			# ----- Get transform ----- #
			position = op('positionArm'+str(i+1)).numpyArray().transpose()[0]
			rotation = op('rotationArm'+str(i+1)).numpyArray().transpose()[0]
			gripperValue = op('gripperArm'+str(i+1))['arm'+str(i+1)]
			# ----- Set xArm transform ----- #
			position = position * 1000
			xArmTransforms[i].x, xArmTransforms[i].y, xArmTransforms[i].z           = -position[2], -position[0], position[1]
			xArmTransforms[i].roll, xArmTransforms[i].pitch, xArmTransforms[i].yaw  = -rotation[2], -rotation[0], rotation[1]
			if isEnablexArm:
				try:
					opMagnifications = op('robotArmMagnificationSettings').numpyArray().transpose()[0]
					
					xArms[i].set_servo_cartesian(xArmTransforms[i].Transform(posMagnification=opMagnifications[0], rotMagnification=opMagnifications[1], isOnlyPosition=False))
					if me.parent().par.Isenablegripper:
						code, ret = xArms[i].getset_tgpio_modbus_data(ConvertToModbusData(gripperValue))
				except ValueError:
					isMoving = False
					traceback.print_exc()
					errorCount += 1
					taskTime = time.perf_counter() - taskStartTime
				
				# ----- If xArm error has occured ----- #
				if any([arm.has_err_warn for arm in xArms]):
					isMoving    = False
					errorCount += 1
					taskTime = time.perf_counter() - taskStartTime
					print('[ERROR] >> xArm Error has occured.')
			# ----- (Optional) Check data ----- #
			if isPrintData:
				print('xArm transform > ' + str(np.round(xArmTransforms[i].Transform(), 1)) + '   Bending sensor > ' + str(gripperValue))
		
		loopCount += 1
	
	# ----- Move to initial position ----- #
	if not isMovingToInit and op(me.parent()).par.Initialposition:
		print('Move to initial position')
		isMovingToInit = True
		for i in range(len(xArms)):
			initPos = np.array([float(val) for val in xArmTransforms[i].GetInitialTransform()])
			
			xArms[i].motion_enable(enable=True)
			xArms[i].set_mode(0)
			xArms[i].set_state(state=0)
			xArms[i].set_position(x=initPos[0], y=initPos[1], z=initPos[2], roll=initPos[3], pitch=initPos[4], yaw=initPos[5], speed=100, wait=True)
			xArms[i].set_mode(1)
			xArms[i].set_state(0)
			time.sleep(0.1)
			xArmTransforms[i].ResetBeforTransform()
	# print(op('gripperArm'+str(1))['arm'+str(1)])
	# print(op(me.parent()).par.Taskend)
	
	return
def onFrameEnd(frame):
	return
def onPlayStateChange(state):
	return
def onDeviceChange():
	return
def onProjectPreSave():
	return
def onProjectPostSave():
	return
def InitRobotArm(robotArm, transform, isSetInitPosition = True):
	"""
	Initialize the xArm
	Parameters
	----------
	robotArm: XArmAPI
		XArmAPI object.
	transform: xArmTransform
		xArmTransform object.
	isSetInitPosition: (Optional) bool
		True -> Set to "INITIAL POSITION" of the xArm studio
		False -> Set to "ZERO POSITION" of the xArm studio
	"""
	
	robotArm.connect()
	robotArm.motion_enable(enable=True)
	robotArm.set_mode(0)             # set mode: position control mode
	robotArm.set_state(state=0)      # set state: sport state
	if isSetInitPosition:
		robotArm.clean_error()
		robotArm.clean_warn()
		initX, initY, initZ, initRoll, initPitch, initYaw = transform.GetInitialTransform()
		robotArm.set_position(x=initX, y=initY, z=initZ, roll=initRoll, pitch=initPitch, yaw=initYaw, wait=True)
	else:
		robotArm.reset(wait=True)
	robotArm.motion_enable(enable=True)
	robotArm.set_mode(1)
	robotArm.set_state(state=0)
	time.sleep(0.5)
	print('Initialized > xArm')
def InitGripper(robotArm):
	"""
	Initialize the gripper
	Parameters
	----------
	robotArm: XArmAPI
		XArmAPI object.
	"""
	robotArm.set_tgpio_modbus_baudrate(2000000)
	robotArm.set_gripper_mode(0)
	robotArm.set_gripper_enable(True)
	robotArm.set_gripper_position(0, speed=5000)
	robotArm.getset_tgpio_modbus_data(ConvertToModbusData(425))
	time.sleep(0.5)
	print('Initialized > xArm gripper')
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
def PrintProcessInfo():
	"""
	Print process information. 
	"""
	print('----- Process info -----')
	print('Total loop count > ', loopCount)
	print('Task time\t > ', taskTime, '[s]')
	print('Error count\t > ', errorCount)
	print('------------------------')
#################### DEBUG ####################
def __TestInterpolate():
	initPos = [100, 200, 300, 400, 500, 600]
	currentPos = [200, 300, 400, 500, 600, 700]
	linSpaceX = np.linspace(0, 1, num=11)
	linSpaceY = np.linspace(initPos[1], currentPos[1], num=11)
	lerp = interpolate.interp1d(linSpaceX, linSpaceY, kind='linear')
	
	print(linSpaceX)
	print(linSpaceY)
	print(lerp(linSpaceX))