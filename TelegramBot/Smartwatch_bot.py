import paho.mqtt.client as PahoMQTT
import json
import time
import telepot
from telepot.loop import MessageLoop
import requests

from pymongo import MongoClient


class SWbot:   
    def __init__(self,clientID,token,topic,broker,port,clienturlSC):     
        self.clientID=clientID
        self.tokenBot = token
        self.topic=topic
        self.broker=broker 
        self.port=port
        self.clienturlSC=clienturlSC

        client2 = MongoClient(self.clienturlSC)
        dbSC=client2.SmartCarCatalog
        self.users=dbSC.Users
        

        self.bot = telepot.Bot(self.tokenBot)
        self._paho_mqtt=PahoMQTT.Client(self.clientID, clean_session=True)
        self._paho_mqtt.on_connect=self.MyOnConnect
        self._paho_mqtt.on_message=self.MyOnMessageRecived
        
        self.chatID=""
        MessageLoop(self.bot).run_as_thread()

    def MyOnConnect(self, paho_mqtt, userdata, flags, rc):  
         if rc==0:
            print(f"Connected to {self.broker} with status {rc}.")
         else:
            print(f"Error! It's not possible to connect to {self.broker}.")

    def start(self):
          self._paho_mqtt.connect(self.broker,self.port)
          self._paho_mqtt.loop_start()
          self._paho_mqtt.subscribe(self.topic,2) 
          #self._paho_mqtt.subscribe(self.topic,0)   #(Per ripulire i topic)
          print(f"Subscribed to topic(s):\n-{self.topic}")

    def stop(self):
          self._paho_mqtt.unsubscribe(self.topic)
          print(f"Unsubscribed from topic(s):\n-{self.topic}")
          self._paho_mqtt.loop_stop()
          self._paho_mqtt.disconnect()
          print(f"Disconnected from broker {self.broker}.")     

    def MyOnMessageRecived(self, paho_mqtt, userdata, message):
        if "heart-rate" in message.topic: 
            msg_topic=str(message.topic)
            print(msg_topic) 
            topic_split=msg_topic.split("/")
            smartwatch_ID=int(topic_split[1])
            m=json.loads(message.payload)                                                                
            heart_rate=m['heart_rate']

            rightuser=self.users.find_one({"smartwatchID":smartwatch_ID})
            ts_channel=str(rightuser["thingspeakUser"])
            self.ts_channel_hr(heart_rate,ts_channel)  # Sending data to ThingSpeak user channel

            if heart_rate < 40:
                driver=self.users.find_one({"smartwatchID":smartwatch_ID})
                self.chatID=driver["chatID"]
                self.bot.sendMessage(self.chatID, text=f"💤You are falling asleep as your heart rate is {heart_rate} bpm!!!\nTake a break ☕️and in case you are using your car, stop driving  for a bit!! 🛑🕝")
            elif heart_rate > 120:
                driver=self.users.find_one({"smartwatchID":smartwatch_ID})
                self.chatID=driver["chatID"]
                self.bot.sendMessage(self.chatID, text=f"Warning ⚠️! Your heart rate is {heart_rate} bpm!!!\nTake a break and relax 🛌😴...In case you are using your car, stop driving 🛑  and contact a doctor 👨‍⚕️!! ")

                
    def ts_channel_hr(self,hr,ts_channel):
        t=requests.get(ts_channel+"&field1={}".format(str(hr)))
        print(f"ThingSpeak data delivered with status \t{t}")


if __name__=="__main__":   
    configuration_file="bot_settings.json"
    resourcesfilenameSC="SmartCarCatalog.json"
    try:
        with open(configuration_file, "r") as conf:
            conf=json.load(open("bot_settings.json"))
            broker=conf["broker"]
            clientID=conf["clientID3"]
            port=conf["port"]
            subtopic="SWbot/+/heart-rate"
            token= conf["token3"]     
    except:
        raise FileNotFoundError(f"File {configuration_file} not found!")

    try:
        username=str(input("Enter the username to obtain necessary catalogs: "))
        password=str(input("Enter the password to obtain necessary catalogs: "))
        if username=="Settings" and password=="pr0jecti0t":
            print("Accessing the ServiceCatalog to discover resources...")
            client1 = MongoClient(f"mongodb+srv://{username}:{password}@icar.bpz7hb7.mongodb.net/?retryWrites=true&w=majority")
            dbService = client1.ServiceCatalog
            resources=dbService.Resources
            catalogSC=resources.find_one({"filename": resourcesfilenameSC})
            clienturlSC=catalogSC["client"]
        else:
            print("Wrong username or password!")
    except:
        raise FileNotFoundError("It's not possible to access the database containing the resources needed!")
    
    subscriber=SWbot(clientID,token,subtopic,broker,port,clienturlSC)
    subscriber.start()
    time.sleep(1)

    try:
        while True:
            time.sleep(10)
    except:
        subscriber.stop()
        print("Bot stopped!")
