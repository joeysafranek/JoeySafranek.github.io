# -----------
# Wi-Fi capabilities are based on research online from other Wi-Fi-based Raspberry Pi projects
# Custom code, circuit design, and implementation based on official Raspberry Pi and Arduino documentation
# Comments are added for readability
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
redLedPin = 13
greenLedPin = 14
blueLedPin = 15
waterSensorPin = 28
speakerPin = 6
# wifi password and apiWebhook
from waterSensorSecrets import wifiName, wifiPassword, apiWebhook
timeBetweenAttempts = 1

lastState = 0

dryWaterSensor = None
speaker = PWM(speakerPin) # Pulse with modulation, allows me to change freq
red = Pin(redLedPin, Pin.OUT)
green = Pin(greenLedPin, Pin.OUT)
blue = Pin(blueLedPin, Pin.OUT)# defines the LED
#sets led start to low
red.high() 
green.low()
blue.low()
# Reads ADC2 or GP28 (ground pin 28)
waterSensor = ADC(waterSensorPin)
# takes the average of 3 dry water sensor tests and adds a 10% threshold to prevent false postives

# Algorithm for determining when water is detected 
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

# The function that will monitor the water 
async def monitorWater():
    global dryWaterSensor
    global lastState
    await asyncio.sleep(1)
    global wlan
    while True: 
        await asyncio.sleep(1)

        # Check if connected
        if not wlan or not wlan.isconnected():
            print("WiFi lost. Reconnecting...")
            red.high()
            green.high()
            wlan = await wifiConnection(wifiName, wifiPassword)
        waterSensorValue = readWaterSensor()
        
        #testing purposes
        print(dryWaterSensor) 
        print(waterSensorValue)
        
        #if the sensor detects water
        blue.low()
        if waterSensorValue >= dryWaterSensor: 
            green.high()
            blue.high()
            #520 hz frequency
            speaker.freq(520)
            # goes to ~60000 for max volumne
            speaker.duty_u16(60000) 
            
            #if water sensor value is over the water threshold and will only send the notification once by using lastState
            if waterSensorValue >= dryWaterSensor and lastState == 0:
                try: 
                    response = urequests.post(apiWebhook, timeout=5)
                    response.close()
                    blue.high()
                    print("Sending text message")
                    #If it fails to connect to API 
                except Exception as e:
                    print("Text message failed:", e)
                lastState = 1
        else: # When water isn't detected
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
    print("SSID:", repr(name))
    print("Password:", repr(password))
    #global wifiAttempts
    while wifiAttempts >= 0:
        status = wlan.status()
        print("Status:", status)
        #if wlan.status() < 0 or wlan.status() >= 3:
            #break
        print('trying to connect')
        await asyncio.sleep(2)
        wifiAttempts -= 1
    #Error Codes in wlan

        if status == 2:
            red.high()
            print("Wifi Password is Wrong")
        elif status == 1:
            red.high()
            print("Trying to connect")
        elif status == 0:
            red.high()
            print("Idle")
        elif status == -1:
            red.high()
            print("Failed to connect")
        elif status == -2:
            red.high()
            print("Can not find the SSID; Check SSID")
        elif status == 3:
            status = wlan.ifconfig()
            print('Connected')
            break
        
    return wlan

asyncio.run(main())


