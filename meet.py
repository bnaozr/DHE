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
global cameraProxy
global videoClient

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


def clustering(data,cvImg,nframe,error,K=2):
	flag1=0
	flag2=0
	l0=0
	l1=0
	
	centroid, labels=np.array([]),np.array([])
	if len(data)>1:
		dataarray = np.asarray(data)
		centroid, labels = kmeans.kMeans(dataarray, K, maxIters = 20, plot_progress = None)  
		
		try:
			cv.Line(cvImg,(int(centroid[0][0]),int(centroid[0][1])),(int(centroid[1][0]),int(centroid[1][1])),(255,0,0))
			cv.Circle(cvImg,int(centroid[0][0]),int(centroid[0][1]),5,(0,255,0),-1)
		except:
			per=False
		i=0
		for l in labels:
			if l==0:
				l0=l0+1
			if l==1:
				l1=l1+1

		if l1>l0:
			temp = centroid[0]
			centroid[0] = centroid[1]
			centroid[1] = temp
			for l in labels:
				if l==0:	
					cv.Circle(cvImg,(data[i][0],data[i][1]),5,(254,0,254),-1)
					flag1=1
				if l==1:			
					cv.Circle(cvImg,(data[i][0],data[i][1]),5,(0,255,255),-1)
					flag2=1
				i=i+1
		else:
			for l in labels:
				if l==0:				
					cv.Circle(cvImg,(data[i][0],data[i][1]),5,(0,255,255),-1)
					flag1=1
				if l==1:		
					cv.Circle(cvImg,(data[i][0],data[i][1]),5,(254,0,254),-1)
					flag2=1
				i=i+1
		try:
			cv.Circle(cvImg,(int(centroid[0][0]),int(centroid[0][1])),5,(0,255,0),-1)
		except:
			per=False
		if(flag1 + flag2<2):
			error=error+1
			pcterror = (error/nframe)*100.0
			#print "current error of kmeans = ",pcterror,"%"          	
	return cvImg,error,centroid, labels

def meet(IP,PORT,fighter):
	global motionProxy
	global post
	global sonarProxy
	global memoryProxy
	global cameraProxy
	global videoClient
	# work ! set current to servos
	stiffnesses  = 1.0
	time.sleep(0.5)

	# TEMP
	pNames = "Body"
	pStiffnessLists = 0.0
	pTimeLists = 1.0
	motionProxy.stiffnessInterpolation(pNames, pStiffnessLists, pTimeLists)

	
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
	closing = 3
	tstp,tu=0,0
	K=2
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
			cvImg2 = cv.CreateImageHeader((imageWidth, imageHeight),cv.IPL_DEPTH_8U, 3)
			cv.SetData(cvImg2, pilImg.tostring())
			cv.CvtColor(cvImg, cvImg, cv.CV_RGB2BGR)
			hsv_img = cv.CreateImage(cv.GetSize(cvImg), 8, 3)
			cv.CvtColor(cvImg, hsv_img, cv.CV_BGR2HSV)
			thresholded_img =  cv.CreateImage(cv.GetSize(hsv_img), 8, 1)
			thresholded_img2 =  cv.CreateImage(cv.GetSize(hsv_img), 8, 1)

			imcv2 = cv2.cvtColor(np.asarray(pilImg), cv2.COLOR_RGB2BGR)



			# Get the orange on the image
			cv.InRangeS(hsv_img, (0, 150, 150), (40, 255, 255), thresholded_img)
			cv.InRangeS(hsv_img, (0, 150, 150), (40, 255, 255), thresholded_img2)
			storage = cv.CreateMemStorage(0)
			contour = cv.FindContours(thresholded_img, storage, cv.CV_RETR_CCOMP, cv.CV_CHAIN_APPROX_SIMPLE)
			cv.Smooth(thresholded_img, thresholded_img, cv.CV_GAUSSIAN, 5, 5)
			cv.Erode(thresholded_img,thresholded_img, None, closing)
			cv.Dilate(thresholded_img,thresholded_img, None, closing)
			

			storage = cv.CreateMemStorage(0)
			contour = cv.FindContours(thresholded_img, storage, cv.CV_RETR_CCOMP, cv.CV_CHAIN_APPROX_SIMPLE)
			points = [] 

			d=[]
			data=[]
			while contour:			
				# Draw bounding rectangles
				bound_rect = cv.BoundingRect(list(contour))
				contour = contour.h_next()
				# for more details about cv.BoundingRect,see documentation
				pt1 = (bound_rect[0], bound_rect[1])
				pt2 = (bound_rect[0] + bound_rect[2], bound_rect[1] + bound_rect[3])
				points.append(pt1)
				points.append(pt2)
				cv.Rectangle(cvImg2, pt1, pt2, cv.CV_RGB(255,0,0), 1)
				lastx=posx
				lasty=posy
				posx=cv.Round((pt1[0]+pt2[0])/2)
				posy=cv.Round((pt1[1]+pt2[1])/2)
				data.append([posx,posy])
				d.append(math.sqrt(pt1[0]**2+pt2[0]**2))
				d.append(math.sqrt(pt1[1]**2+pt2[1]**2))

			cvImg2,error,centroid,labels = clustering(data,cvImg2,nframe,error,K)
			# Update the closing size towards the number of found labels
			if labels.size<2:
				closing=1
			if labels.size<6:
				closing = 2
			if labels.size>10:
				closing=3
			if closing < 1:
				closing = 0
			if centroid.size!=0:
		
				uh = 0
				try:
					x = int(centroid[0][0])
					y = int(centroid[0][1])
				except:
					print "NaN"
				l=memoryProxy.getData("Device/SubDeviceList/US/Left/Sensor/Value")
				r=memoryProxy.getData("Device/SubDeviceList/US/Right/Sensor/Value")
				# Commande proportionnelles pour le cap et la distance
				kh = 20.0/(imageWidth/2)
				km = 0.25
				uh = -kh*(x - imageWidth/2)
				um =  km*(math.sqrt(l**2+r**2) - 0.6)
				if (uh>4 or uh<-4):
					motionProxy.moveTo(0.0, 0.0, uh*almath.TO_RAD)
					tu = time.time()
				if (um>0.03 or um<-0.03) and (l>0.6 and r>0.6):
					motionProxy.moveTo(um, 0.0, 0.0)
					tu = time.time()
				else:
					# quand il est proche mettre K=1, on admet qu il n y a plus de parasites, et que les zones oranges sont assez 
					# grosse pour leur appliquer un coef ce fermeture eleve
					# print "-------------------------"
					# print "K = 1"
					K=1
					closing = 5
					tstp = time.time()
				# print "l",l
				# print "r",r
				# print "um ",um	
				#Temps de repos du Nao
				tact = tstp - tu
				#S'il attend plus de 5sec, il admet qu'il est devant sa cible
				if tact>5:
					found=False
					if fighter=="dark":
						#tts.say("I've been waiting for you, Obi-Wan. We meet again, at last. The circle is now complete. When I left you, I was but the learner; now I am the master.")
						#time.sleep(1.0)
						tts.say("I see you")
					if fighter=="obi":
						#time.sleep(15.0)
						#tts.say("Only a master of evil, Darth.")
						tts.say("I see you")

				cv.ShowImage("Real",cvImg)
				#cv.ShowImage("Threshold",thresholded_img2)
				cv.ShowImage("Threshold",thresholded2)
				cv.WaitKey(1)

	except KeyboardInterrupt:
		print
		print "Interrupted by user, shutting down" 
		end(IP,PORT)

def end(IP,PORT):
	global motionProxy
	global sonarProxy
	global memoryProxy
	global post
	global cameraProxy
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
	global cameraProxy
	global videoClient


	post = ALProxy("ALRobotPosture", IP, PORT)
	tts = ALProxy("ALTextToSpeech", IP, PORT)
	motionProxy = ALProxy("ALMotion", IP, PORT)
	cameraProxy = ALProxy("ALVideoDevice", IP, PORT)
	# init video
	resolution = 0    # 0 : QQVGA, 1 : QVGA, 2 : VGA
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
	sonarProxy = ALProxy("ALSonar", IP, PORT)
	sonarProxy.subscribe("myApplication")
	memoryProxy = ALProxy("ALMemory", IP, PORT)

	post.goToPosture("Crouch", 1.0)
	time.sleep(2)




def main(IP,PORT,fighter):
	init(IP,PORT)
	#rockandload(fighter)
	meet(IP,PORT,fighter)


if __name__ == "__main__":
	IP = "172.20.12.26"
	PORT = 9559
	# Read IP address from first argument if any.
	if len(sys.argv) > 1:
		IP = sys.argv[1]
	if len(sys.argv) > 2:
		IP = sys.argv[1]
		fighter = sys.argv[2]
	main(IP,PORT,fighter)
	
