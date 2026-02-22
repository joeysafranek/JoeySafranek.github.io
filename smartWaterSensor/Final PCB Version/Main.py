# -----------
# Wifi capabilites are based on research online from other wifi based raspberry pi projects
# Custom code, circuit design, and implementation based on official Raspberry Pi and Arduino documentation
# Comments are added for readibility
# Created by Joey Safranek 2/5/2025 for State Farm Project 
# ------------



# libraries 
#from picozero import pico_led
from machine import Pin, ADC, PWM
import time
import aioble
import bluetooth
import asyncio
import struct
import network
import urequests
import json
from sys import exit

# Pins as variables for easy changes
redLedPin = 15
greenLedPin = 14
blueLedPin = 13
waterSensorPin = 28
speakerPin = 16
# wifi password and apiWebhook
from waterSensorSecrets import wifiName, wifiPassword, apiWebhook
timeBetweenAttempts = 1
#change to how many attempts you want to try
lastState = 0

dryWaterSensor = None
speaker = PWM(speakerPin) # Pulse with modulation, allows me to change freq
red = Pin(redLedPin, Pin.OUT)
green = Pin(greenLedPin, Pin.OUT)
blue = Pin(blueLedPin, Pin.OUT)# defines the LED
#sets led start to low
red.low() 
green.low()
blue.low()
# Reads ADC2 or GP28 (ground pin 28)
waterSensor = ADC(waterSensorPin)
# takes the average of 3 dry water sensor tests and adds a 3000 threshold to prevent false postives


async def readDryState(): 
    blue.high()
    print("Calibrating Dry Value")
    await asyncio.sleep(2)
    waterSensorValue1 = readWaterSensor()
    await asyncio.sleep(2)
    waterSensorValue2 = readWaterSensor()
    await asyncio.sleep(2)
    waterSensorValue3 = readWaterSensor()
    avgWaterSensor = (waterSensorValue1 + waterSensorValue2 + waterSensorValue3)/3
    thresholdValue = avgWaterSensor / 10
    thresholdWaterSensor = avgWaterSensor + thresholdValue
    print(thresholdWaterSensor)
    blue.low()
    green.high()
    return (thresholdWaterSensor)
    
# Reads the water sensor
def readWaterSensor(): 
    waterSensorValue = waterSensor.read_u16()
     #sends the value of the water sensor
    return waterSensorValue
#sets the variable as a global value so any function could use it--incase I need to use it in the future

async def monitorWater():
    global dryWaterSensor
    global lastState
    await asyncio.sleep(1)
    global wlan
    while True: 
        await asyncio.sleep(.5)

        # Check if connected
        if not wlan or not wlan.isconnected():
            print("WiFi lost. Reconnecting...")
            wlan = await wifiConnection(wifiName, wifiPassword)
        waterSensorValue = readWaterSensor()
        #testing purposes
        print(dryWaterSensor) 
        print(waterSensorValue)
        #if the sensor detects water
        blue.low()
        if waterSensorValue >= dryWaterSensor: 
            green.low()
            red.high()
            #520 hz frequency
            speaker.freq(520)
            # goes to ~60000 for max volumne
            speaker.duty_u16(60000) 
            
            if waterSensorValue >= dryWaterSensor and lastState == 0:
                try: 
                    urequests.post(apiWebhook)
                    print("Sending iMessage")
                except Exception as e:
                    print("iMessage failed:", e)
                lastState = 1
        else:
            green.high() 
            red.low()
            #turns the speaker off
            speaker.duty_u16(0)
            lastState = 0
async def main():
    # use the global value of these variables
    global dryWaterSensor
    global wifiName
    global wifiPassword
    global wlan
    
    dryWaterSensor = await readDryState()
    print("Dry value calculated")
    wlan = await wifiConnection(wifiName, wifiPassword)
    # monitor water never sends a value back, so runs until connection fails
    await monitorWater()
    
# researched examples online and created the following function for the wifi connection
async def wifiConnection(name, password):
    wifiAttempts = 10
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(name, password)
    green.low()
    red.high()
    blue.high()
    #global wifiAttempts
    while wifiAttempts > 0:
        status = wlan.status()
        print("Status:", status)
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        print('trying to connect')
        await asyncio.sleep(2)
        wifiAttempts -= 1
    
    if wlan.status() != 3:
        red.high()
        speaker.duty_u16(40000) 
        print("WiFi failed")
        return None
    else:
        status = wlan.ifconfig()
        print('connected')
        return wlan

asyncio.run(main())
