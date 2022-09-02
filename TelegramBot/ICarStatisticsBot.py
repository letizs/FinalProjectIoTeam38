# Telegram Bot 'CarManager' to alert the drivers if the car airbags are on and to let the car owner to manage statistics about car damages into the Industries Catalog

import json
import time
import os
from datetime import datetime
from threading import Timer
import paho.mqtt.client as PahoMQTT
import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

from pymongo import MongoClient

class MQTT_CarBot():
    def __init__(self,clientID,broker,port,sub_topic,token,clienturlI,clienturlSC):
        self.clientID=clientID
        self.broker=broker 
        self.port=port
        self.sub_topic=sub_topic
        self.token = token
        self.clienturlI=clienturlI
        self.clienturlSC=clienturlSC

        client2 = MongoClient(self.clienturlI)
        dbI=client2.IndustriesCatalog
        dbSC=client2.SmartCarCatalog
        self.users=dbSC.Users
        self.cars=dbSC.Cars
        self.statcars=dbI.Cars
        
        self._paho_mqtt=PahoMQTT.Client(self.clientID,clean_session=True)  #False to remeber comunication
        self._paho_mqtt.on_connect=self.MyOnConnect
        self._paho_mqtt.on_message=self.MyOnMessageReceived
        
        self.bot = telepot.Bot(self.token)
        MessageLoop(self.bot, {'chat': self.on_chat_message, 'callback_query': self.on_callback_query}).run_as_thread()
        
        self.chatID=[]
        self.__message1=[]
        self.__message2 = {}
    
    
    def MyOnConnect(self, paho_mqtt, userdata, flags, rc):
        if rc==0:
            print(f"Connected to {self.broker} with status {rc}.")
        else:
            print(f"Error! It's not possible to connect to {self.broker}.")
            
               
    def start(self):
        self._paho_mqtt.connect(self.broker,self.port)
        self._paho_mqtt.loop_start()
        self._paho_mqtt.subscribe(self.sub_topic,2) 
        #self._paho_mqtt.subscribe(self.sub_topic,0)  #(Per ripulire il topic)
        print(f"Subscribed to topic(s):\n-{self.sub_topic}")

    def stop(self):
        self._paho_mqtt.unsubscribe(self.sub_topic)
        print(f"Unsubscribed from topic(s):\n-{self.sub_topic}")
        self._paho_mqtt.loop_stop()
        self._paho_mqtt.disconnect()
        print(f"Disconnected from broker {self.broker}.")
    

    def on_chat_message(self, msg):
        content_type, chat_type, chat_ID = telepot.glance(msg)
        find=0
        for element in self.__message1:
            if chat_ID in element.values():  
                find=1
        if find==0:          #If there isn't already a message at that chat ID in the list, create one
            self.__message1.append({"chatID": chat_ID, "plate": "", "date": "", "code": "", "type": "", "details": ""}) #One dict for every chatID, data overwritten everytime
        message = msg['text']
        if message=="/start":
            self.bot.sendMessage(chat_ID, text="Click on 'Menu' to have a complete list of possible commands 🔍📌")
        elif message=="/new_damage":
            self.bot.sendMessage(chat_ID, text='Please, write the plate 🏷️ of your car using the format:\n/plate+XXnnnXX')
        elif "/plate" in message:
            plate=message.split("+")
            if len(plate)>1:
                pp=plate[1].upper()
                for p in self.__message1:
                    if p["chatID"]==chat_ID:
                        p['plate']=pp
                buttons = [[InlineKeyboardButton(text=f'1 - Mechanical 🛠️', callback_data=f'1,Mechanical'), 
                        InlineKeyboardButton(text=f'2 - Electrical 🔋', callback_data=f'2,Electrical')]] 
                keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
                self.bot.sendMessage(chat_ID, text='Please, choose the type of your damage:', reply_markup=keyboard)
            else:
                self.bot.sendMessage(chat_ID, text="⚠️ Something went wrong: please, try again following the previous instructions ⬆️")
        elif "/new_damage_date" in message:
            date=message.split("+")
            if len(date)>1:
                date_format_ddmmyyyy = "%d/%m/%Y"
                try:
                    d = datetime.strptime(date[1], date_format_ddmmyyyy)
                    for d in self.__message1:
                        if d["chatID"]==chat_ID:
                            d['date']=date[1]
                    self.bot.sendMessage(chat_ID, text="✏️ If you want to add more details about your damage use the format:\n/new_damage_details+info\n\n💾 Otherwise type /finish to save your data.")
                except:
                    self.bot.sendMessage(chat_ID, text="⚠️ The data format you use is not valid: please, try again following the previous instructions ⬆️")   
            else:
                self.bot.sendMessage(chat_ID, text="⚠️ Something went wrong: please, try again following the previous instructions ⬆️")
        elif "/new_damage_details" in message:
            info=message.split("+")
            if len(info)>1:
                for e in self.__message1:
                    if e["chatID"]==chat_ID:
                        e['details']=info[1]
                self.bot.sendMessage(chat_ID, text="💾 Please, type /finish to save your data not to loose them❕")
            else:
                self.bot.sendMessage(chat_ID, text="⚠️ Something went wrong: please, try again following the previous instructions ⬆️")  
        elif message=="/finish":
            i=0    
            for e in self.__message1:
                if e["chatID"]==chat_ID and e["code"]!="":
                    ppp=e["plate"]
                    payload=e.copy()
                    del payload["chatID"]
                    del payload["plate"]
                    flag=0
                    try:
                        car=self.cars.find_one({"_id": ppp})
                        statcar=self.statcars.find_one({"plate":ppp})
                        if car==None:
                            print("Plate not found in the catalog.")
                        else:
                            for id in car["chatID_drivers"]:
                                if id==chat_ID:  #If the chat ID is associated to the plate
                                    flag=1
                            if flag==1:
                                stats=statcar["statistics"]
                                stats["damage_number"]+=1
                                stats["damages"].append(payload)
                                self.statcars.find_one_and_update({"plate":ppp},{"$set":{"statistics":stats}})
                                self.bot.sendMessage(chat_ID, text=f'The car with plate {ppp} has been correctly updated with your damage infos in the Catalog ✅\n\nℹ️ A complete list of your damages is available at http://127.0.0.1:8089/CarManager/myDamagesList?plate={ppp} only accessing from your PC 💻')
                                del self.__message1[i]       
                            else:
                                self.bot.sendMessage(chat_ID, text=f"⚠️ Warning! Your chatID is not present in the Catalog 🚘 or the plate {ppp} is not associated with your chatID: if you aren't the registered owner 👤 of the car, some features may not be available. 🔐\nFor more infos please contact your Car Industry!")  
                    except:
                        raise FileNotFoundError("It was not possible to reach the database.")   
                elif e["chatID"]==chat_ID and e["code"]=="":
                    self.bot.sendMessage(chat_ID, text="⚠️ The message is empty! Please try again to insert your data 📝")
                else:
                    i=i+1
        else:
            self.bot.sendMessage(chat_ID, text="⚠️ Command not supported ‼️")
    
    def on_callback_query(self,msg):
        query_ID , chat_ID , query_data = telepot.glance(msg,flavor='callback_query')
        cb_data=query_data.split(",")
        if len(cb_data)>1:
            for e in self.__message1:
                if e["chatID"]==chat_ID:
                    e['code']=cb_data[0]
                    e['type']=cb_data[1]      
            self.bot.sendMessage(chat_ID, text="🗓️ Please write the date when your damage occured in the format:\n/new_damage_date+DD/MM/YYYY")
        elif len(cb_data)==1:
            m2 = self.__message2.copy()
            m2['e'][0]['v'] = query_data
            m2['e'][0]['t'] = time.time()
            self.bot.sendMessage(chat_ID, text=f"Alarm switched {query_data} ✅")
            
    def MyOnMessageReceived(self, paho_mqtt, userdata, message):
        if "alarm" in message.topic: 
            self.chatID=[]
            msg_topic=str(message.topic) 
            topic_split=msg_topic.split("/")
            plate=str(topic_split[1])
            rightcar=self.cars.find_one({"_id":plate})
            for id in rightcar["chatID_drivers"]:
                self.chatID.append(id)   #List of all chat IDs associated with that car in the catalog
            m=message.payload
            self.__message2=json.loads(m)
            button = [[InlineKeyboardButton(text='SWITCH OFF ❌', callback_data='off')]]
            keyboard = InlineKeyboardMarkup(inline_keyboard=button)
            for chatID in self.chatID:
                self.bot.sendMessage(chatID, text=f"🚨AIRBAG OF THE CAR {plate} IS ON!🚨\nIf you won't switch off this alarm in 3 minutes emergency number will automatically be called!⏱️", reply_markup=keyboard)
                delay = 180                            
                t = Timer(delay,self.EmergencyCall,[chatID])
                t.start()                                #After 3 minutes "EmergencyCall" will be called
        else:
            pass

    def EmergencyCall(self,chatID):
        m2 = self.__message2.copy()
        if m2['e'][0]['v']=="on":
            self.bot.sendMessage(chatID, text="📞Calling 112...🆘🚑🚒🚓")
        elif m2['e'][0]['v']=="off":
            self.bot.sendMessage(chatID, text="Alarm already switched off 🔇")
        else:
            pass
        


if __name__=="__main__":
    configuration_file="bot_settings.json"
    resourcesfilenameI="IndustriesCatalog.json"
    resourcesfilenameSC="SmartCarCatalog.json"
    try:
        with open(configuration_file, "r") as conf:
            conf=json.load(open("bot_settings.json"))
            broker=conf["broker"]
            port=conf["port"]
            token=conf["token1"]
            clientID=conf["clientID1"]
            sub_topic="CarSystem/+/alarm"
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
            catalogSC=resources.find_one({"filename": resourcesfilenameSC})
            clienturlI=catalogI["client"]
            clienturlSC=catalogSC["client"]
        else:
            print("Wrong username or password!")
    except:
        raise FileNotFoundError("It's not possible to access the database containing the resources needed!")

    bot=MQTT_CarBot(clientID,broker,port,sub_topic,token,clienturlI,clienturlSC)
    bot.start()
    try:
        while True:
            time.sleep(2)
    except:
        bot.stop()
        print("Telegram Bot stopped!")