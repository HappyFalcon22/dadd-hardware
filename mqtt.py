import paho.mqtt.client as mqtt
import random
import time
import sys
from datetime import datetime
import serial.tools.list_ports

host = "172.23.144.1"
port = 1883
name = "thang_mqtt"
password = ""
feed = ["Temperature", "Humidity", "LED", "Water Pump", "Timestamp", "Earth Moisture", "GDD"]
feed_format = ["TEMP", "HUMID", "LED", "PUMP", "TIMESTAMP", "EARTH", "GDD"]

# Sensor 1 info
sensor_1 = {"sensor_id": None, "Timestamp": None, "Temperature": None, "Humidity": None, "LED": None, "Water Pump": None, "Earth Moisture": None, "GDD": None}

connected_flag = False

def mqtt_connected(client, userdata, flags, rc):
    print("Connected succesfully!!")
    connected_flag = True
    client.subscribe("LED")
    client.subscribe("Water Pump")
    client.subscribe("sensor_info")

def mqtt_subscribed(client, userdata, mid, granted_qos):
    print("Subscribed to Topic!!!")

def message(client, feed_id, message):
    print("New data :", message.payload.decode())
    pass

def disconnect(client):
    print("Connection interrupted !")
    sys.exit(1)

def getPort():
    ports = serial.tools.list_ports.comports()
    N = len(ports)
    commPort = "None"
    for i in ports:
        str_port = str(i)
        if ("USB-SERIAL CH340" in str_port):
            commPort = str_port.split(" ")[0]
    return commPort


# Register MQTT server
mqttClient = mqtt.Client()
mqttClient.username_pw_set(name, password)
mqttClient.connect(host, int(port), 60)
mqttClient.on_connect = mqtt_connected
mqttClient.on_subscribe = mqtt_subscribed
mqttClient.on_message = message
mqttClient.on_disconnect = disconnect

# Create a server connecting to the YoloBit
isMicrobitConnected = False
if getPort() != "None":
    ser = serial.Serial(port=getPort(), baudrate=115200)
    isMicrobitConnected = True

# A function to process and extract the value of the received data
def processData(data: str):
    # Remove start and end characters
    data = data.replace("!", "").replace("#", "")
    # Split data from ":"
    sensor_id, feed_data, feed_value = data.split(":") # Separate the data to : ID - FIELD - VALUE
    sensor_1["sensor_id"] = int(sensor_id) # The type of ID is an integer
    feed_data = feed[feed_format.index(feed_data)]
    sensor_1[feed_data] = feed_value
    if (feed_data == "LED" or "Water Pump"):
        mqttClient.publish(feed_data, feed_value)

#A function that make the gateway to read the serial data of the microbit
mess = ""
def readSerial():
    bytesToRead = ser.inWaiting()
    if bytesToRead > 0:
        global mess
        mess += ser.read(bytesToRead).decode("UTF-8")
        while (("!" in mess) and ("#" in mess)):
            start, end = int(mess.find("!")), int(mess.find("#"))
            processData(mess[start : end + 1])
            time.sleep(1) # In case of sending too much message at one time
            if (end == len(mess)):
                mess = ""
            else:
                mess = mess[end + 1:]

def JSON_generate(str):
    return str

def send_to_server(info):
    sensor_1["Timestamp"] = datetime.now().isoformat(sep=" ")
    mqttClient.publish("sensor_info", str(sensor_1))


# Interval of sending the data to the server
counter = 10

mqttClient.loop_start()

while not connected_flag: # Wait in loop
    minute_now = datetime.now().minute
    if isMicrobitConnected:
        readSerial()
        counter -= 1
        if (counter <= 0):
            if minute_now % 2 == 0:
                ser.write("A".encode())
                time.sleep(0.2)
                ser.write("C".encode())
                time.sleep(0.2)
                processData("!1:LED:1#")
                processData("!1:PUMP:1#")
            else:
                ser.write("B".encode())
                time.sleep(0.2)
                ser.write("D".encode())
                time.sleep(0.2)
                processData("!1:LED:0#")
                processData("!1:PUMP:0#")
            send_to_server(sensor_1)
            counter = 10
    time.sleep(1)

mqttClient.loop_stop()  # Stop loop 
mqttClient.disconnect() # Disconnect




