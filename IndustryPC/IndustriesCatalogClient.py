# Industries Catalog MQTT Client to update statistics about consumes, kilometers and airbag activations and to send data to NodeRed

import paho.mqtt.client as PahoMQTT
import json
import time
import os
import requests

from pymongo import MongoClient

class IndustriesSystem():
    def __init__(self,clientID,topic1,topic2,broker,port,clienturlI):
        self.clientID=clientID
        self.topic1=topic1
        self.topic2=topic2
        self.broker=broker
        self.port=port
        
        self.clienturlI=clienturlI

        client2 = MongoClient(self.clienturlI)
        dbSC=client2.SmartCarCatalog
        self.cars=dbSC.Cars
        dbI=client2.IndustriesCatalog
        self.statcars=dbI.Cars

        self.monthly_consumes=[]
        self.last_month_daily_km=[]
        self.annual_airbag_act=[]
        
        self._paho_mqtt=PahoMQTT.Client(self.clientID, clean_session=True) #False to remember comunication

        self._paho_mqtt.on_connect=self.MyOnConnect
        self._paho_mqtt.on_message=self.MyOnMessageReceived
        
    def MyOnConnect(self, paho_mqtt, userdata, flags, rc):
        if rc==0:
            print(f"Connected to {self.broker} with status {rc}.")  
        else:
            print(f"Error! It's not possible to connect to {self.broker}.")

    def start(self):
        self._paho_mqtt.connect(self.broker,self.port)
        self._paho_mqtt.loop_start()
        self._paho_mqtt.subscribe(self.topic1,2) 
        #self._paho_mqtt.subscribe(self.topic1,0)   #(Per ripulire il topic)
        self._paho_mqtt.subscribe(self.topic2,2)
        #self._paho_mqtt.subscribe(self.topic2,0)   #(Per ripulire il topic)
        print(f"Subscribed to topic(s):\n-{self.topic1} \n-{self.topic2}")

    def stop(self):
        self._paho_mqtt.unsubscribe(self.topic1)
        self._paho_mqtt.unsubscribe(self.topic2)
        print(f"Unsubscribed from topic(s):\n-{self.topic1} \n-{self.topic2}")
        self._paho_mqtt.loop_stop()
        self._paho_mqtt.disconnect()
        print(f"Disconnected from {self.broker}.")
        
    def MyOnMessageReceived(self, paho_mqtt, userdata, message):
        if "consumesandkm" in message.topic: 
            msg_topic1=str(message.topic) 
            topic_split1=msg_topic1.split("/")
            plate=topic_split1[1]
            message1=message.payload 
            msg1=json.loads(message1) 

            daily_consumes=msg1["daily_consumes"]
            daily_km=msg1["daily_km"]

            #Publishing for ThingsPeak channel:
            rightcar=self.cars.find_one({"_id":plate})
            ts_channel=str(rightcar["thingspeakChannel"])
            #print(ts_channel)
            self.TS_channel(daily_consumes,daily_km,ts_channel)  # Sending data to ThingSpeak car channel
            
            #Creating lists to wait for 30 data
            self.monthly_consumes.append(daily_consumes)
            self.last_month_daily_km.append(daily_km)
            
            
            if len(self.monthly_consumes)==30 and len(self.last_month_daily_km)==30:         # After 1 month...
                mc=round(sum(self.monthly_consumes)/len(self.monthly_consumes),1)
                dkm=round(sum(self.last_month_daily_km)/len(self.last_month_daily_km),0)
                self.NodeRedPublisher(mc,dkm,plate)                     #Publishing for NodeRed
                self.monthly_consumes=[]
                self.last_month_daily_km=[]
                try:
                    car=self.statcars.find_one({"plate":plate})
                    if car==None:
                        print("Plate not found in the catalog.")
                    else:
                        stats=car["statistics"]
                        stats["last_month_consumes(L/100km)"]=mc
                        stats["last_month_daily_km"]=dkm
                        self.statcars.find_one_and_update({"plate":plate},{"$set":{"statistics":stats}})
                        print(f"Consumes and kilometers of the car {plate} just updated.")
                except:
                    raise FileNotFoundError("It was not possible to reach the database.")
            else:
                print(f"Waiting for other {30-len(self.monthly_consumes)} data about consumes and km.") 

        elif "airbag" in message.topic:
            msg_topic2=str(message.topic) 
            topic_split2=msg_topic2.split("/")
            plate=topic_split2[1]
            message2=message.payload 
            msg2=json.loads(message2) 

            airbag_act=msg2["monthly_airbag_activaction"]
            self.annual_airbag_act.append(airbag_act)

            if len(self.annual_airbag_act)==12:           # After 1 year...
                a=sum(self.annual_airbag_act)
                self.annual_airbag_act=[]
                try:
                    car=self.statcars.find_one({"plate":plate})
                    if car==None:
                        print("Plate not found in the catalog.")
                    else:
                        stats=car["statistics"]
                        stats["annual_airbag_activations"]=a
                        self.statcars.find_one_and_update({"plate":plate},{"$set":{"statistics":stats}})
                        print(f"Airbag activations of the car {plate} just updated.")
                except:
                    raise FileNotFoundError("It was not possible to connect to the database.")
            else:
                print(f"Waiting for other {12-len(self.annual_airbag_act)} data about airbag activations.")  

    def NodeRedPublisher(self,mc,dkm,plate):
        pub_topic=str("CarSystem/"+plate+"/consumesandkm"+ "/NodeRedSystem")
        monthly_statistics={"consumes": mc,"km":dkm}
        self._paho_mqtt.publish(pub_topic, json.dumps(monthly_statistics), qos=2, retain=False) 
        print(f"Message at {pub_topic} published: {monthly_statistics}")

    def TS_channel(self,dc,dk,ts_channel):
        t=requests.get(ts_channel+"&field1={}&field2={}".format(str(dc),str(dk)))
        print(f"ThingSpeak data delivered with status \t{t}")
        


if __name__ == '__main__':
    configuration_file="IC_settings.json"
    resourcesfilenameI="IndustriesCatalog.json"
    try:
        with open(configuration_file, "r") as conf:
            conf=json.load(open("IC_settings.json"))
            broker=conf["broker"]
            port=conf["port"]
            clientID=conf["clientID"]
            # The subscriber receives the messages from all the cars (plates) and the messages from the 2 sensors.
            topic1=conf["topic1"]
            topic2=conf["topic2"]
    except:
        raise FileNotFoundError(f"File {configuration_file} not found in the current directory {os.getcwd()}")

    try:
        username=str(input("Enter the username to obtain necessary catalogs: "))
        password=str(input("Enter the password to obtain necessary catalogs: "))
        if username=="Settings" and password=="pr0jecti0t":
            print("Accessing the ServiceCatalog to discover resources...")
            client1 = MongoClient(f"mongodb+srv://{username}:{password}@icar.bpz7hb7.mongodb.net/?retryWrites=true&w=majority")
            dbService = client1.ServiceCatalog
            resources=dbService.Resources
            catalogI=resources.find_one({"filename": resourcesfilenameI})
            clienturlI=catalogI["client"]
        else:
            print("Wrong username or password!")
    except:
        raise FileNotFoundError("It's not possible to access the database containing the resources needed!")

    Client=IndustriesSystem(clientID,topic1,topic2,broker,port,clienturlI) 
    Client.start()
    try:
        while True:
            time.sleep(1)
    except:
        Client.stop()
        print("Client stopped!")
        
