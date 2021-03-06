# -*- coding: utf-8 -*-
"""
@author: quentin
@descript: We meet again, at last.
"""

import sys
import time
import cv,cv2
import almath
from naoqi import ALProxy
import numpy as np
import Image
import random
import math
import reset
import kmeans
import nao_live

global motionProxy
global tts
global post
global sonarProxy
global memoryProxy

def rockandload(fighter):
	global motionProxy
	global post
	if fighter=="obi":
		tts.say("I need my blue lightsaber")
	if fighter=="dark":
		tts.say("I need my red lightsaber")
	names  = ["RHand", "LHand"]
	angles = [1,1]
	fractionMaxSpeed  = 0.2
	motionProxy.setAngles(names, angles, fractionMaxSpeed)
	time.sleep(3)
	angles = [0.15,0.15]
	motionProxy.setAngles(names, angles, fractionMaxSpeed)
	time.sleep(1)

def line_intersection(line1, line2):
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line2[1][1], line2[0][1] - line2[1][1])

    def det(a, b):
        return a[0] * b[1] - a[1] * b[0]

    div = det(xdiff, ydiff)
    if div == 0:
       return False

    d = (det(*line1), det(*line2))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    return x, y


def swordcenterdetection(enemy):
	global motionProxy
	global post
	global sonarProxy
	global memoryProxy
	# work ! set current to servos
	stiffnesses  = 1.0
	time.sleep(0.5)

	# init video
	cameraProxy = ALProxy("ALVideoDevice", IP, PORT)
	resolution = 1    # 0 : QQVGA, 1 : QVGA, 2 : VGA
	colorSpace = 11   # RGB
	camNum = 0 # 0:top cam, 1: bottom cam
	fps = 1; # frame Per Second
	cameraProxy.setParam(18, camNum)
	try:
		videoClient = cameraProxy.subscribe("python_client", 
														resolution, colorSpace, fps)
	except:
		cameraProxy.unsubscribe("python_client")
		videoClient = cameraProxy.subscribe("python_client", 
														resolution, colorSpace, fps)
	print "Start videoClient: ",videoClient
	# Get a camera image.
	# image[6] contains the image data passed as an array of ASCII chars.
	naoImage = cameraProxy.getImageRemote(videoClient)
	imageWidth = naoImage[0]
	imageHeight = naoImage[1]

	found = True
	posx=0
	posy=0
	mem = cv.CreateMemStorage(0)
	i=0
	cv.NamedWindow("Real")
	cv.MoveWindow("Real",0,0)
	cv.NamedWindow("Threshold")
	cv.MoveWindow("Real",imageWidth+100,0)
	error=0.0
	nframe=0.0
	closing = 1
	tstp,tu=0,0
	K=2
	pb = 0.5 # low pass filter value 
	try:
		while found:
			nframe=nframe+1
			# Get current image (top cam)
			naoImage = cameraProxy.getImageRemote(videoClient)
			# Get the image size and pixel array.
			imageWidth = naoImage[0]
			imageHeight = naoImage[1]
			array = naoImage[6]
			# Create a PIL Image from our pixel array.
			pilImg = Image.fromstring("RGB", (imageWidth, imageHeight), array)
			# Convert Image to OpenCV
			cvImg = cv.CreateImageHeader((imageWidth, imageHeight),cv.IPL_DEPTH_8U, 3)
			cv.SetData(cvImg, pilImg.tostring())
			cv.CvtColor(cvImg, cvImg, cv.CV_RGB2BGR)
			hsv_img = cv.CreateImage(cv.GetSize(cvImg), 8, 3)
			cv.CvtColor(cvImg, hsv_img, cv.CV_BGR2HSV)
			thresholded_img =  cv.CreateImage(cv.GetSize(hsv_img), 8, 1)
			thresholded_img2 =  cv.CreateImage(cv.GetSize(hsv_img), 8, 1)
			temp =  cv.CreateImage(cv.GetSize(hsv_img), 8, 1)
			eroded =  cv.CreateImage(cv.GetSize(hsv_img), 8, 1)
			skel = cv.CreateImage(cv.GetSize(hsv_img), 8, 1)
			img = cv.CreateImage(cv.GetSize(hsv_img), 8, 1)
			edges = cv.CreateImage(cv.GetSize(hsv_img), 8, 1)
			# Get the orange on the image
			cv.InRangeS(hsv_img, (110, 80, 80), (150, 200, 200), thresholded_img)
			storage = cv.CreateMemStorage(0)

			lines = cv.HoughLines2(thresholded_img, storage, cv.CV_HOUGH_PROBABILISTIC, 1, cv.CV_PI/180, 30, param1=0, param2=0)
			print lines

			first = 1
			sl=0
			Mx=[]
			My=[]
			for l in lines:
				sl=sl+1
			for i in range((sl-1)):
				l=lines[i]
				print l
				rho = l[0]
				theta = l[1]
				a = np.cos(theta)
				b = np.sin(theta)
				x0 = a*rho
				y0 = b*rho
				cf1,cf2  = 300,300
				# xpt11 = int(cv.Round(x0 + cf1*(-b)))
				# ypt11 = int(cv.Round(y0 + cf1*(a)))
				# xpt12 = int(cv.Round(x0 - cf2*(-b)))
				# ypt12 = int(cv.Round(y0 - cf2*(a)))
				pt11 = l[0]
				pt12 = l[1]
				cv.Line(cvImg, pt11, pt12, cv.CV_RGB(255,255,255), thickness=1, lineType=8, shift=0)

				l=lines[(i+1)]
				rho = l[0]
				theta = l[1]
				a = np.cos(theta)
				b = np.sin(theta)
				x0 = a*rho
				y0 = b*rho
				cf1,cf2  = 300,300
				# xpt1 = int(cv.Round(x0 + cf1*(-b)))
				# ypt1 = int(cv.Round(y0 + cf1*(a)))
				# xpt2 = int(cv.Round(x0 - cf2*(-b)))
				# ypt2 = int(cv.Round(y0 - cf2*(a)))

				# A = np.array(((xpt1,ypt1),(xpt2,ypt2)))
				# B = np.array(((xpt11,ypt11),(xpt12,ypt12)))

				# try:
				# 	m = line_intersection(A, B)
				# 	mx = m[0]
				# 	my = m[1]
				# 	Mx.append(mx)
				# 	My.append(my)
				# except:
				# 	error=1 #intersection return False we don't add the point

				pt1 = l[0]
				pt2 = l[1]
				cv.Line(cvImg, pt1, pt2, cv.CV_RGB(255,255,255), thickness=1, lineType=8, shift=0)
			cMx,cMy=[],[]
			for x in Mx:
				cMx.append((1-pb)*x)
			for y in My:
				cMy.append((1-pb)*y)
			try:
				for i in range(len(cMx)):
					Mx[i] = cMx[i]+cMtx[i]
					My[i] = cMy[i]+cMty[i]
				Mm = (int(np.mean(Mx)),int(np.mean(My)))
				print "M",Mm
				cv.Circle(cvImg,Mm,5,(254,0,254),-1)
			except:
				error=1 # we are at first iteration
			cMtx,cMty=[],[]
			Mtx = Mx
			Mty = My
			for x in Mtx:
				cMtx.append(pb*x)
			for y in Mty:
				cMty.append(pb*y)
			
			cv.ShowImage("Real",cvImg)
			cv.ShowImage("Threshold",thresholded_img)
			cv.WaitKey(1)

	except KeyboardInterrupt:
		print
		print "Interrupted by user, shutting down" 
		end()

def end():
	global motionProxy
	global post
	global sonarProxy
	global memoryProxy
	pNames = "Body"
	post.goToPosture("Crouch", 1.0)
	time.sleep(1.0)
	pStiffnessLists = 0.0
	pTimeLists = 1.0
	proxy = ALProxy("ALMotion",IP, 9559)
	proxy.stiffnessInterpolation(pNames, pStiffnessLists, pTimeLists)
	#tts.say("exit")
	print
	print "This is the END"
	cameraProxy.unsubscribe(videoClient)
	sys.exit(0)

def init(IP,PORT):
	global motionProxy
	global tts
	global post
	global sonarProxy
	global memoryProxy

	post = ALProxy("ALRobotPosture", IP, PORT)
	tts = ALProxy("ALTextToSpeech", IP, PORT)
	motionProxy = ALProxy("ALMotion", IP, PORT)
	sonarProxy = ALProxy("ALSonar", IP, PORT)
	sonarProxy.subscribe("myApplication")
	memoryProxy = ALProxy("ALMemory", IP, PORT)
	post.goToPosture("Crouch", 1.0)
	time.sleep(2)


if __name__ == "__main__":
	IP = "172.20.12.26"
	PORT = 9559
	# Read IP address from first argument if any.
	if len(sys.argv) > 1:
		IP = sys.argv[1]
	if len(sys.argv) > 2:
		IP = sys.argv[1]
		enemy = sys.argv[2]

	init(IP,PORT)
	#rockandload(fighter)
	swordcenterdetection(enemy)