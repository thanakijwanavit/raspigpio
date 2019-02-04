#!/home/nic/miniconda3/envs/gpio/bin/python

from datetime import datetime
import RPi.GPIO as GPIO
import time
GPIO.setmode(GPIO.BCM)
GPIO.setup(23, GPIO.IN)




def readpulse(pin):
	start = datetime.now().microsecond
	stop = datetime.now().microsecond
	while GPIO.input(pin) == 0:
		continue
	start = datetime.now().microsecond
	while GPIO.input(pin) == 1:
		continue
	stop = datetime.now().microsecond
	Elapsed = stop - start
	return Elapsed

while 1:
	#time.sleep(1)
	#print(GPIO.input(23))
	dustlevel= float(readpulse(23))/1000-2
	print("the dust level is :", dustlevel)
