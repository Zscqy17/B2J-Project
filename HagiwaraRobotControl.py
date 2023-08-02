# -----------------------------------------------------------------------
# Author:   Takayoshi Hagiwara (KMD)
# Created:  2021/8/20
# Summary:  Cybernetic avatar motion behaviour
# -----------------------------------------------------------------------
import sys, os
pyVersion = sys.version
if '3.9.5' in pyVersion:
	path = ".\\Lib\\site-packages"
elif '3.7.2' in pyVersion:
	path = ".\\Lib_2021\\site-packages"
sys.path.insert(0,path)
import numpy as np
import scipy.spatial.transform as scitransform
import math

class CyberneticAvatarMotionBehaviour:
	originPositions     	= {}
	inversedMatrix      	= {}
	def __init__(self, defaultParticipantNum: int = 2) -> None:
		for i in range(defaultParticipantNum):
			self.originPositions['participant'+str(i+1)] 		= np.zeros(3)
			self.inversedMatrix['participant'+str(i+1)] 		= np.array([[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]])
		
		self.participantNum = defaultParticipantNum
		
	
	def GetSharedTransformWithCustomWeight(self, position: dict, rotation: dict, weightPos: list, weightRot: list, beforePositions: dict, beforeRotations: dict, weightedPositions: dict, weightedRotations: dict, controller: str = 'p', positionAdjustment: str = 'cartesian', isRelativePosition: bool = True, isRelativeRotation: bool = True):
		"""
		Calculate the shared Transform with custom weights for each participant.
		
		----- CAUTION -----
			Since the angle is converted to Euler angle during the calculation, the exact angle may not be provided.
			In addition, the behavior near the singularity is unstable.
​
		Parameters
		----------
		position: dict or numpy array
			Participants' rigid body position. 
			[x, y, z]
		rotation: dict or numpy array
			Participants' rigid body rotation as Quaternion.
			[x, y, z, w]
		weightPos: list
			Weights of position for each participant.
			A list corresponding to the number of participants
​
			Example: Number of participant = 2
				-> [0.5 (p1), 0.5 (p2)]
		weightRot: list
			Weights of rotation for each participant.
			A list corresponding to the number of participants
​
			Example: Number of participant = 2
				-> [0.5 (p1), 0.5 (p2)]
		controller: (Optional) str
			A control loop mechanism employing feedback.
			Options: 'p', 'pi', 'pid (TODO)'
		positionAdjustment: (Optional) str
			Position adjustment method.
			Options: 'cartesian', 'polar'
		isRelativePosition: (Optional) bool
			Use relative position
		isRelativeRotation: (Optional) bool
			Use relative rotation
		
		Returns
		----------
		sharedPosition: numpy array
			Shared position.
			[x, y, z]
		sharedRotation_euler: numpy array
			Shared rotation as Euler angles.
			[x, y, z]
		"""

		# ----- numpy array to dict: position ----- #
		if type(position) is np.ndarray:
			position = self.NumpyArray2Dict(position)
		
		# ----- numpy array to dict: rotation ----- #
		if type(rotation) is np.ndarray:
			rotation = self.NumpyArray2Dict(rotation)
		
		if isRelativePosition:
			pos = self.GetRelativePosition(position)
		else:
			pos = position
		
		if isRelativeRotation:
			rot = self.GetRelativeRotation(rotation)
		else:
			rot = rotation
					# ----- Shared transform ----- #
		sharedPosition          = [0, 0, 0]
		sharedRotation_euler    = [0, 0, 0]

		sharedPolarPosition		= [0, 0, 0]

		if controller == 'p':
			for i in range(self.participantNum):
				sharedPosition += pos['participant'+str(i+1)] * weightPos[i]
				sharedRotation_euler += self.Quaternion2Euler(rot['participant'+str(i+1)]) * weightRot[i]
		elif controller == 'pi':
			for i in range(self.participantNum):
				# ----- Position ----- #
				diffPos     = pos['participant'+str(i+1)] - beforePositions['participant'+str(i+1)]
				
				if positionAdjustment == 'cartesian':
					weightedPos = diffPos * weightPos[i] + weightedPositions['participant'+str(i+1)]
					# if i == 1:
					# 	weightedPos = [weightedPos[0], 0, weightedPos[2]]
					sharedPosition += weightedPos
					weightedPositions['participant'+str(i+1)]  = weightedPos
				elif positionAdjustment == 'polar':
					polar = self.Cartesian2Polar(diffPos)
					weightedPolarPos = polar * weightPos[i] + self.Cartesian2Polar(weightedPositions['participant'+str(i+1)])
					sharedPolarPosition += weightedPolarPos
					weightedPositions['participant'+str(i+1)] = self.Polar2Cartesian(weightedPolarPos)

				beforePositions['participant'+str(i+1)]    = pos['participant'+str(i+1)]
				# ----- Rotation ----- #
				qw, qx, qy, qz = beforeRotations['participant'+str(i+1)][3], beforeRotations['participant'+str(i+1)][0], beforeRotations['participant'+str(i+1)][1], beforeRotations['participant'+str(i+1)][2]
				mat4x4 = np.array([ [qw, qz, -qy, qx],
									[-qz, qw, qx, qy],
									[qy, -qx, qw, qz],
									[-qx,-qy, -qz, qw]])
				currentRot = rot['participant'+str(i+1)]
				diffRot = np.dot(np.linalg.inv(mat4x4), currentRot)
				diffRotEuler = self.ScipyQuaternion2Euler(np.array(diffRot))
				
				weightedDiffRotEuler = [weightRot[i] * r for r in diffRotEuler]
				weightedDiffRot = self.ScipyEuler2Quaternion(np.array(weightedDiffRotEuler))

				nqw, nqx, nqy, nqz = weightedDiffRot[3], weightedDiffRot[0], weightedDiffRot[1], weightedDiffRot[2]
				neomat4x4 = np.array([[nqw, -nqz, nqy, nqx],
									  [nqz, nqw, -nqx, nqy],
									  [-nqy, nqx, nqw, nqz],
									  [-nqx,-nqy, -nqz, nqw]])
				weightedRot = np.dot(neomat4x4,  weightedRotations['participant'+str(i+1)])
				sharedRotation_euler += self.ScipyQuaternion2Euler(weightedRot)
				weightedRotations['participant'+str(i+1)]  = weightedRot
				beforeRotations['participant'+str(i+1)]    = rot['participant'+str(i+1)]
			
			if positionAdjustment == 'polar':
				sharedPosition = self.Polar2Cartesian(sharedPolarPosition)

		return sharedPosition, sharedRotation_euler, beforePositions, beforeRotations, weightedPositions, weightedRotations
	
	def SetOriginPosition(self, position) -> None:
		"""
		Set the origin position

		Parameters
		----------
		position: dict, numpy array
			Origin position
		"""
		# ----- numpy array to dict: position ----- #
		if type(position) is np.ndarray:
			position = self.NumpyArray2Dict(position)

		# listParticipant 	= [participant for participant in list(position.keys()) if 'participant' in participant]
		# self.participantNum	= len(listParticipant)

		for i in range(self.participantNum):
			self.originPositions['participant'+str(i+1)] = position['participant'+str(i+1)]
        
	def GetRelativePosition(self, position):
		"""
		Get the relative position

		Parameters
		----------
		position: dict, numpy array
			Position to compare with the origin position.
			[x, y, z]
		
		Returns
		----------
		relativePos: dict
			Position relative to the origin position.
			[x, y, z]
		"""

		# ----- numpy array to dict: position ----- #
		if type(position) is np.ndarray:
			position = self.NumpyArray2Dict(position)
		
		relativePos = {}
		for i in range(self.participantNum):
			relativePos['participant'+str(i+1)] = position['participant'+str(i+1)] - self.originPositions['participant'+str(i+1)]
		
		return relativePos
	
	def Cartesian2Polar(self, position):
		"""
		Get the polar coordinates from cartesian coordinates.

		Parameters
		----------
		position: numpy array
			Position to different from previous position.
			[x, y, z]
		
		Returns
		----------
		polar: numpy array
			Polar coordinates.
			[r, theta, phi]
		"""
		
		r 		= np.linalg.norm(position)
		theta 	= np.arccos(position[2] / r)
		phi 	= np.arctan2(position[1], position[0])

		if np.isnan(theta):
			theta = 0

		return np.array([r, theta, phi])
	
	def Polar2Cartesian(self, position):
		"""
		Get the cartesian coordinates from polar coordinates.

		Parameters
		----------
		position: numpy array
			Polar coordinates.
			[r, theta, phi]
		
		Returns
		----------
		cartesian: numpy array
			Cartesian coordinates.
			[x, y, z]
		"""

		x = position[0] * np.sin(position[1]) * np.cos(position[2])
		y = position[0] * np.sin(position[1]) * np.sin(position[2])
		z = position[0] * np.cos(position[1])

		return np.array([x, y, z])


	def SetInversedMatrix(self, rotation) -> None:
		"""
		Set the inversed matrix

		Parameters
		----------
		rotation: dict, numpy array
			Quaternion.
			Rotation for inverse matrix calculation
		"""

		# ----- numpy array to dict: rotation ----- #
		if type(rotation) is np.ndarray:
			rotation = self.NumpyArray2Dict(rotation)
		
		# listParticipant = [participant for participant in list(rotation.keys()) if 'participant' in participant]
		listOtherRb     = [rb for rb in list(rotation.keys()) if 'otherRigidBody' in rb]
		# self.participantNum     = len(listParticipant)
		self.otherRigidBodyNum  = len(listOtherRb)

		# ----- Participant ----- #
		for i in range(self.participantNum):
			q = rotation['participant'+str(i+1)]
			qw, qx, qy, qz = float(q[3]), float(q[1]), float(q[2]), float(q[0])
			mat4x4 = np.array([ [qw, -qy, qx, qz],
								[qy, qw, -qz, qx],
								[-qx, qz, qw, qy],
								[-qz,-qx, -qy, qw]])
			self.inversedMatrix['participant'+str(i+1)] = np.linalg.inv(mat4x4)
		
		# ----- Rigid body except participants ----- #
		for i in range(self.otherRigidBodyNum):
			q = rotation['otherRigidBody'+str(i+1)]
			qw, qx, qy, qz = float(q[3]), float(q[1]), float(q[2]), float(q[0])
			mat4x4 = np.array([ [qw, -qy, qx, qz],
								[qy, qw, -qz, qx],
								[-qx, qz, qw, qy],
								[-qz,-qx, -qy, qw]])
			self.inversedMatrix['otherRigidBody'+str(i+1)] = np.linalg.inv(mat4x4)

	def GetRelativeRotation(self, rotation):
		"""
		Get the relative rotation

		Parameters
		----------
		rotation: dict, numpy array
			Rotation to compare with the origin rotation.
			[x, y, z, w]
		
		Returns
		----------
		relativeRot: dict
			Rotation relative to the origin rotation.
			[x, y, z, w]
		"""

		# ----- numpy array to dict: rotation ----- #
		if type(rotation) is np.ndarray:
			rotation = self.NumpyArray2Dict(rotation)
		
		relativeRot = {}
		# ----- Participant ----- #
		for i in range(self.participantNum):
			relativeRot['participant'+str(i+1)] = np.dot(self.inversedMatrix['participant'+str(i+1)], rotation['participant'+str(i+1)])
		
		# ----- Rigid body except participants ----- #
		for i in range(self.otherRigidBodyNum):
			relativeRot['otherRigidBody'+str(i+1)] = np.dot(self.inversedMatrix['otherRigidBody'+str(i+1)], rotation['otherRigidBody'+str(i+1)])

		return relativeRot

	def ScipyQuaternion2Euler(self, q, sequence: str = 'xyz', isDeg: bool = True):
		"""
		Calculate the Euler angle from the Quaternion.
		Using scipy.spatial.transform.Rotation.as_euler

		Parameters
		----------
		q: np.ndarray
			Quaternion.
			[x, y, z, w]
		sequence: (Optional) str
			Rotation sequence of Euler representation, specified as a string.
			The rotation sequence defines the order of rotations about the axes.
			The default is xyz.
		isDeg: (Optional) bool
			Returned angles are in degrees if this flag is True, else they are in radians.
			The default is True.
		
		Returns
		----------
		rotEuler: np.ndarray
			Euler angle.
			[x, y, z]
		"""

		quat = scitransform.Rotation.from_quat(q)
		rotEuler = quat.as_euler(sequence, degrees=isDeg)
		return rotEuler
	
	def ScipyEuler2Quaternion(self, e, sequence: str = 'xyz', isDeg: bool = True):
		"""
		Calculate the Quaternion from the Euler angle.
		Using scipy.spatial.transform.Rotation.as_quat

		Parameters
		----------
		e: np.ndarray
			Euler.
			[x, y, z]
		sequence: (Optional) str
			Rotation sequence of Euler representation, specified as a string.
			The rotation sequence defines the order of rotations about the axes.
			The default is xyz.
		isDeg: (Optional) bool
			If True, then the given angles are assumed to be in degrees. Default is True.
		
		Returns
		----------
		rotQuat: np.ndarray
			Quaternion
			[x, y, z, w]
		"""
		
		quat = scitransform.Rotation.from_euler(sequence, e, isDeg)
		rotQuat = quat.as_quat()
		return rotQuat
	
	def InversedRotation(self, rot, axes: list = []):
		"""
		Calculate the inversed rotation.

		----- CAUTION -----
		If "axes" is set, it will be converted to Euler angles during the calculation process, which may result in inaccurate rotation.
		In addition, the behavior near the singularity is unstable.

		Parameters
		----------
		rot: np.ndarray
			Quaternion.
			[x, y, z, w]
		axes: (Optional) list[str]
			Axes to be inversed.
			If length of axes is zero, return inversed quaternion

		Returns
		----------
		inversedRot: np.ndarray
			Inversed rotation
			[x, y, z, w]
		"""

		if len(axes) == 0:
			quat = scitransform.Rotation.from_quat(rot)
			inversedRot = quat.inv().as_quat()
			return inversedRot

		rot = self.ScipyQuaternion2Euler(rot)

		for axis in axes:
			if axis == 'x':
				rot[0] = -rot[0]
			elif axis == 'y':
				rot[1] = -rot[1]
			elif axis == 'z':
				rot[2] = -rot[2]

		inversedRot = self.ScipyEuler2Quaternion(rot)

		return inversedRot

	def NumpyArray2Dict(self, numpyArray, dictKey: str = 'participant'):
		"""
		Convert numpy array to dict.
		Parameters
		----------
		numpyArray: numpy array
			Numpy array.
		dictKey: (Optional) str
			The key name of the dict.
		"""
		
		if type(numpyArray) is np.ndarray:
			dictionary = {}
			if len(numpyArray.shape) == 1:
				dictionary[dictKey+str(1)] = numpyArray
			else:
				for i in range(len(numpyArray)):
					dictionary[dictKey+str(i+1)] = numpyArray[i]
		else:
			print('Type Error: argument is NOT Numpy array')
			return
		
		return dictionary

	def calcValue(_array):
		# calc positions
		_tx = _array[0]*10
		_ty = _array[1]*-10
		_tz = _array[2]*5
		
		# calc postures
		_rx = _array[3]*3
		_ry = _array[4]*-3
		_rz = _array[5]*-1

		print(np.__version__)
		
		return [_tx, _ty, _tz, _rx, _ry, _rz]
