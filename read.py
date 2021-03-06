#!/usr/bin/env python
# coding: utf-8

# In[7]:


#!pip3 install numpy
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import pprint as pprint
pp = pprint.PrettyPrinter(indent=4)
from datetime import datetime
from datetime import timedelta
import RPi.GPIO as GPIO
import time
import progressbar
import inspect, re
#import signal


#get_ipython().run_line_magic('matplotlib', 'inline')


# In[8]:







######### argparse#########
import argparse
import sys

try:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type = int, help="number of samples to take", default=10)
    parser.add_argument('--save_dir', type = str, default = 'saved_classifier/checkpoint.pth',
                    help = 'path to save the trained model')
    args = parser.parse_args()

    #print the square of user input from cmd line.
    print ("take {samples} samples".format(samples=args.samples))

    #print all the sys argument passed from cmd line including the program name.
    #print (sys.argv)

    #print the second argument passed from cmd line; Note it starts from ZERO
    #print (sys.argv[1])
except:
    e = sys.exc_info()[0]
    print (e)
    

#assign pin numbers
msd501pm10pin=27
msd501pm25pin=21
nova10pin=23
nova25pin=24
datasize=args.samples



# In[17]:


##############config system#############


def setupGPIO(pin,mode): #mode is either in or out
    GPIO.setmode(GPIO.BCM)
    if mode=="in": 
        GPIO.setup(pin, GPIO.IN)
    else:
        GPIO.setup(pin, GPIO.OUT)

        
        
###### data processing######################
def varname(p):
  for line in inspect.getframeinfo(inspect.currentframe().f_back)[3]:
    m = re.search(r'\bvarname\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)', line)
    if m:
      return m.group(1)



def checkarray(pulseinfonova): #### check the generated array
    print(pulseinfonova['pulsewidth10'])
    print(pulseinfonova['pulsewidth25'],"\n\n")
    pp.pprint(pulseinfonova)
    
#generate dataframe
def generatedf(pulseinfonova):
    df=pd.DataFrame({'time':pulseinfonova['time'],
                  'pulsewidth10':pulseinfonova['pulsewidth10'],
                  'pulsewidth25':pulseinfonova['pulsewidth25'],
                  'dust10(ng)':pulseinfonova['pulsewidth10']-2000,
                  'dust10(ug)':(pulseinfonova['pulsewidth10']-2000)/1000,
                  'dust25(ng)':pulseinfonova['pulsewidth25']-2000,
                  'dust25(ug)':(pulseinfonova['pulsewidth25']-2000)/1000,  
                  "time(s)":pulseinfonova['second']/1000,
                  "readtime(s)":pulseinfonova['readtime'],
                   "pulsetime10":pulseinfonova["pulsetime10"],
                    "pulsetime25":pulseinfonova["pulsetime25"]})
    #add info
    df["dust10(ppm)"]=df['dust10(ug)']*1.225
    df["dust25(ppm)"]=df['dust25(ug)']*1.225
    df["rolling mean 10(ppm)"] = df["dust10(ppm)"].rolling(10,center=True).mean()
    df["rolling mean 25(ppm)"] = df["dust25(ppm)"].rolling(10,center=True).mean()
    df.fillna(method='bfill',inplace=True)
    df["error10"]= np.power(np.power(df["rolling mean 10(ppm)"]-df["dust10(ppm)"],2),0.4)
    df["error25"]= np.power(np.power(df["rolling mean 25(ppm)"]-df["dust25(ppm)"],2),0.4)
    #fill in na just in case
    df.fillna(method='bfill',inplace=True)
    df.fillna(method='ffill',inplace=True)
    return df


############ reading the pins#######        


def readpulse(pin):   ###read high pulse width
    for i in range(2):
        start = datetime.now()
        stop = datetime.now()
        while GPIO.input(pin) == 0:
            continue
        start = datetime.now()
        while GPIO.input(pin) == 1:
            continue
        stop = datetime.now()
        Elapsed = stop - start
    return Elapsed.total_seconds()*1000000


def readpulsewidth(pin10,pin25,number_of_readings): ###read high pulse width (2 at the same time)
    pulsewidth10=np.array([])
    pulsewidth25=np.array([])
    time=[]
    second=np.array([])
    start_time=datetime.now()
    with progressbar.ProgressBar(max_value=number_of_readings) as bar:
        while True:
            pulsereading10=readpulse(pin10)
            pulsereading25=readpulse(pin25)
            if pulsereading10 > 1000 and pulsereading25 > 1000:
                pulsewidth10=np.append(pulsewidth10,pulsereading10)
                pulsewidth25=np.append(pulsewidth25,pulsereading25)
                time.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                second=np.append(second,(datetime.now()-start_time)*1000)
            if pulsewidth10.size>= number_of_readings:
                break
            bar.update(pulsewidth10.size)
            #print("currently at loop",pulsewidth10.size)
    return {"pulsewidth10":pulsewidth10,"pulsewidth25":pulsewidth25,"time":time,"second":second}


def read_pulsewidth_and_pulse_time(number_of_readings,pin10=None,pin25=None,pinmsd10=None,pinmsd25=None): ###read high pulse width (2 at the same time)
    pulsewidth10=np.array([])
    pulsewidth25=np.array([])
    pulsetime10=np.array([])
    pulsetime25=np.array([])
    time=[]
    second=np.array([])
    start_time=datetime.now()
    readtime_per_channel=np.array([])
    with progressbar.ProgressBar(max_value=number_of_readings) as bar:
        while True:
            startreadtime=datetime.now()
            pulsereading10=readpulse(pin10)
            pulsereading25=readpulse(pin25)
            if pulsereading10 > 1000 and pulsereading25 > 1000:
                pulsewidth10=np.append(pulsewidth10,pulsereading10)
                pulsewidth25=np.append(pulsewidth25,pulsereading25)
                time_for_pulseread=(datetime.now()-startreadtime).total_seconds()*0.25
                readtime_per_channel=np.append(readtime_per_channel,time_for_pulseread)
                time.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                second=np.append(second,(datetime.now()-start_time).total_seconds()*1000)
                if pinmsd10:
                    pulsetime10=np.append(pulsetime10,check_low_pulse_for(pinmsd10,time_for_pulseread)["ratio"])                   
                if pinmsd25:
                    pulsetime25=np.append(pulsetime25,check_low_pulse_for(pinmsd25,time_for_pulseread)["ratio"])
            if pulsewidth10.size>= number_of_readings:
                break
            bar.update(pulsewidth10.size)
            #print("currently at loop",pulsewidth10.size)
    return {"pulsewidth10":pulsewidth10,"pulsewidth25":pulsewidth25,"time":time,"second":second,"pulsetime10":pulsetime10,"pulsetime25":pulsetime25,"readtime":readtime_per_channel}



def readpulselow(pin): ## read low pulse width
    for i in range(1):
        start = datetime.now()
        stop = datetime.now()
        while GPIO.input(pin) == 1:
            continue
        start = datetime.now()
        while GPIO.input(pin) == 0:
            continue
        stop = datetime.now()
        Elapsed = stop - start
    return Elapsed.total_seconds()*1000



def check_low_pulse_for(pin,period):#period in seconds #check low ratio in active low circuits over a period #return dict
    start=datetime.now()
    #signal.alarm(period)
    activeperiod=0
    while (datetime.now()-start).total_seconds()<period:
        activeperiod+=readpulselow(pin)
    
    totalperiod=(datetime.now()-start).total_seconds()*1000
    #print ("Timeout! at {time_elasped}".format(time_elasped=(datetime.now()-start).total_seconds()))
    return {'lowpulse':activeperiod,'total_period':totalperiod,'ratio':activeperiod/totalperiod}
    

    
def readlowsensorasdf(pin,size,period):###output dataframe from readings with specified repitition and period return df
    readings=[]
    output_dict={}
    for i in range(size):
        readings.append(check_low_pulse_for(msd501pm10pin,period))
    for i in readings[0].keys():
        output_dict[i]=[]
    for i in readings:
        for j in i.keys():
            output_dict[j].append(i[j])
    return pd.DataFrame(output_dict)    
    

####### debug functions#####


def infinite_loop():
    start=datetime.now()
    try:
        while True:
            print('the time is {time}'.format(time=(start-datetime.now()).total_seconds()))
            time.sleep(1)
    
    except Exception:
        print ("Timeout! at {time_elasped}".format(time_elasped=(datetime.now()-start).total_seconds()))
        
        
def testpulse(pin,periods):
    #end_time = datetime.now() + timedelta(seconds=20)
    count=0
    while count<periods:
        #time.sleep(1)
        #print(GPIO.input(23))
        dustlevel= float(readpulse(pin)+1-1)-2
        print("the dust level is :", dustlevel)
        count+=1

def testlowpulse(pin,times=5):
    for i in times:
        Lowpulse = readpulselow(pin)
        print(Lowpulse)

# In[10]:


#set up gpio
pin_input=[msd501pm10pin, msd501pm25pin, nova10pin,nova25pin]
pin_name=['msd501pm10pin', 'msd501pm25pin', 'nova10pin','nova25pin']
for pin in pin_input:
    setupGPIO(pin,"in")


# In[11]:


#run test for output
for pin,name in zip(pin_input,pin_name):
    print(name)
    testpulse(pin,5)


# In[12]:


#set data variables


#call data
#pulseinfonova=readpulsewidth(nova10pin,nova25pin,datasize)
pulseinfonova=read_pulsewidth_and_pulse_time(datasize,nova10pin,nova25pin,msd501pm10pin,msd501pm25pin)
checkarray(pulseinfonova)


# In[18]:


df=generatedf(pulseinfonova)
df.head(5)


# In[142]:


#save file
filename="./data/test{time}_{samples}samples.csv".format(time=datetime.now().strftime("%d%b%y_%H:%M"),samples=datasize)
df.to_csv(filename)
print("data saved at {filename}".format(filename=filename))




