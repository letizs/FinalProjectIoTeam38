import paho.mqtt.client as PahoMQTT
import json
import random
import time
import numpy as np
import schedule
import os

class Smartwatch_pub:
    def __init__(self,clientID,broker,port,topic):
        self.clientID=clientID
        self.broker=broker 
        self.port=port
        self.topic=topic

        self._paho_mqtt=PahoMQTT.Client(self.clientID, clean_session=True) 
        self._paho_mqtt.on_connect=self.MyOnConnect 

    def MyOnConnect(self,paho_mqtt, userdata, flags, rc):
        if rc==0:
            print(f"Connected to {self.broker} with status {rc}.")
        else:
            print(f"Error! It's not possible to connect to {self.broker}.")
    
    def start(self):
        self._paho_mqtt.connect(self.broker,self.port)
        self._paho_mqtt.loop_start()


    def stop(self):
        self._paho_mqtt.loop_stop()
        self._paho_mqtt.disconnect()
        print(f"Disconnected from broker {self.broker}.")
    
    def MyPublish(self): #Simulated sensor for heartrate/min data 
        base_heart_rate = int(np.random.uniform(40,100))
        heart_rate = self.HRSensor(base_heart_rate)
        now=str(time.time())
        message={"heart_rate": heart_rate, "timestamp":now}
        
        self._paho_mqtt.publish(self.topic, json.dumps(message), qos=2, retain=False) #Publishes to send a message in the TelegramBot acting as a subscriber.
        #self._paho_mqtt.publish(topic="SWbot/GF679TH/heart-rate", payload="", qos=0, retain=True) #(Per ripulire i topic)
        print(f"Message at {self.topic} published: {message}")

    def HRSensor(self,bhr):
        self.bhr = bhr
        num = random.choice([0,1])
        if (num == 0):
            self.bhr += 10
        else:
            self.bhr -= 10
        return self.bhr


if __name__ == '__main__':
    configuration_file="smartwatch_settings.json"

    try:
        with open(configuration_file) as conf:
                conf=json.load(conf)
                clientID=conf["clientID"]
                broker=conf["broker"]
                port=conf["port"]
                Topic=conf["topic"]
    except:
        raise FileNotFoundError(f"File {configuration_file} not found in the current directory {os.getcwd()}")

    publisher=Smartwatch_pub(clientID,broker,port,Topic)
    publisher.start()
    time.sleep(1)
    publisher.MyPublish()
    schedule.every(10).seconds.do(publisher.MyPublish)      # Message at topic SWbot/1236/heart-rate published every 60

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except:
        publisher.stop()
        print("Publisher stopped!")
