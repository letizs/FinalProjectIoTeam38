# MQTT Car Publisher: managing of airbag activations and statistics about consumes and kilometers.

import paho.mqtt.client as PahoMQTT
import json
import time
import numpy as np
import schedule
import os

class CarSystem:
    
    def __init__(self,clientID,broker,port,topic1,topic2,topic3):   # topic:/CarSystem/plate/sensorName 
        self.clientID=clientID
        self.broker=broker 
        self.port=port
        self.topic1=topic1 
        self.topic2=topic2
        self.topic3=topic3

        self._paho_mqtt=PahoMQTT.Client(self.clientID, clean_session=True)   #False to remember comunication
        self._paho_mqtt.on_connect=self.MyOnConnect
        
        self.monthly_airbag_activations=0
        self.__message3 = {'bn': "CarSystemBot_airbag",
                          'e':
                          [
                              {'n': 'AirbagAlarm','u': 'bool', 't': '','v': ''},
                          ]
                          }


    def MyOnConnect(self, paho_mqtt, userdata, flags, rc):  
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
    
    
    def MyPublish1(self):  # Simulated sensors about daily consumes and daily kilometers data published at the same topic EVERY DAY
        daily_consumes=float(np.random.uniform(0.5,5.5)+ np.random.uniform(0,0.5)*np.random.randn(1))  # Mean consumes L/100km
        daily_consumes=round(daily_consumes,1)
        daily_km= int(np.random.randint(0,1000))                                                     # Kilometers per day
        now=str(time.time())
        message1={"daily_consumes": daily_consumes, "daily_km": daily_km, "timestamp":now}
        
        self._paho_mqtt.publish(self.topic1, json.dumps(message1), qos=2, retain=False)
        #self._paho_mqtt.publish(self.topic1, payload="" , qos=0, retain=True) #(Per ripulire i topic)
        print(f"Message at {self.topic1} published: {message1}")

    def MyPublish2(self): # Data about monthly airbag activation published at a different topic from MyPublish1 EVERY MONTH
        now=str(time.time())
        message2={"monthly_airbag_activaction": self.monthly_airbag_activations, "timestamp":now}   # Airbag activations per month

        self._paho_mqtt.publish(self.topic2, json.dumps(message2), qos=2, retain=False)
        #self._paho_mqtt.publish(self.topic2, payload="" , qos=0, retain=True)  #(Per ripulire i topic)
        print(f"Message at {self.topic2} published: {message2}")
        self.monthly_airbag_activations=0  # Returns to zero for the next month
     
        
    def AirbagSimulator(self): # Simulated sensor for airbag activations publishes only if active to send a message in the TelegramBot acting as a subscriber.
        self.status= np.random.uniform(0.1,0.6)  # We want more 0 than 1 to be realistic
        self.status = int(round(self.status,0))
        if self.status==1:
            print("Airbag activated")
            self.monthly_airbag_activations+=1   #Increase the number of monthly activations
            m3 = self.__message3.copy()
            m3['e'][0]['v'] = 'on'
            m3['e'][0]['t'] = time.time()
            self._paho_mqtt.publish(self.topic3, json.dumps(m3), qos=2, retain=False)  
            #self._paho_mqtt.publish(self.topic3, payload="", qos=0, retain=True)   #(Per ripulire i topic)
            print(f"Message at {self.topic3} published: {m3}")
        else:
            print("Airbag not activated")



if __name__=="__main__":
    configuration_file="car_settings.json"
    try:
        with open(configuration_file, "r") as conf:
            conf=json.load(open("car_settings.json"))
            clientID=conf["clientID1"]
            broker=conf["broker"]
            port=conf["port"]
            p=conf["clientID1"]
            pp=p.split("_")
            plate=pp[0]
            mqttTopic=conf["mqttTopic"]
            topic1=str(mqttTopic+"/"+plate+"/consumesandkm")
            topic2=str(mqttTopic+"/"+plate+"/airbag")
            topic3=str(mqttTopic+"/"+plate+"/alarm")
    except:
        raise FileNotFoundError(f"File {configuration_file} not found in the current directory {os.getcwd()}")

    publisher=CarSystem(clientID,broker,port,topic1,topic2,topic3)
    publisher.start()
    time.sleep(1)
    publisher.MyPublish1()
    publisher.MyPublish2()
    publisher.AirbagSimulator()

    #Following timing settings have to be set to real values but it has been shortened just to view real time the results:
    schedule.every(1).days.do(publisher.MyPublish1)                      # Message at topic .../consumesandkm published every 24h
    schedule.every(30).days.do(publisher.MyPublish2)                     # Message at topic .../airbag published every 30 days
    schedule.every(30).seconds.do(publisher.AirbagSimulator)             # Message at topic .../alarm published every time the airbag status switches to 'on'
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except:
        publisher.stop()
        print("Publisher stopped!")

        
        
