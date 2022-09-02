import requests
import telepot
import time
import json
from MyMQTT import *
from pymongo import MongoClient
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

class CarBot:
    def __init__(self,broker,port,token,clientID,baseTopic,clienturlSC):
        client = MongoClient(clienturlSC)
        db = client.SmartCarCatalog
        self.users = db.Users
        self.cars = db.Cars

        self.client = MyMQTT(clientID,broker,port,self)
        self.baseTopic = baseTopic
        self.topicTempHum = self.baseTopic + '/+/temp&hum'

        self.tokenBot = token
        self.bot = telepot.Bot(self.tokenBot)
        MessageLoop(self.bot, {'chat': self.on_chat_message,
                               'callback_query': self.on_callback_query}).run_as_thread()

        self.__messageOptional = {"optional":"","status":"","lastUpdate":""}

        self.communication = False
        self.controlButton = False
        self.temperature = 0
        self.sendTemperature = False
        self.humidity = 0
        self.sendHumidity = False

    def start (self):
        self.client.start()
        self.client.mySubscribe(self.topicTempHum)

    def stop (self):
        self.client.stop()

    def on_chat_message(self,msg):
        content_type, chat_type, chat_ID = telepot.glance(msg)
        message = msg['text']

        if (message == "/manage_optionals"):
            self.bot.sendMessage(chat_ID,text = "Insert car's plate: ")
            self.communication = True
        elif (message == "finish"):
            self.bot.sendMessage(chat_ID,text = "Communication ends. \nHave a good day!")
            self.communication = False
            self.controlOneButton = False
        elif (self.communication):
            plate = message
            car = self.cars.find_one({"_id":plate})

            driver = self.users.find_one({"chatID":chat_ID})
            driverPlates = driver["cars_plate"]

            if (car == None):
                self.bot.sendMessage(chat_ID,text = "The given plate does not exist. \nInsert another car's plate or digit 'finish' to end the communication: ")
            elif (plate in driverPlates):
                buttons = [[InlineKeyboardButton(text = f'DOORS 🚗',callback_data = f'{plate},doors')], 
                        [InlineKeyboardButton(text = f'WINDOWS 🚙',callback_data = f'{plate},windows')],
                        [InlineKeyboardButton(text = f'LIGHTS 💡',callback_data = f'{plate},lights')],
                        [InlineKeyboardButton(text = f'AIR CONDITIONING 🛠',callback_data = f'{plate},airConditioning')]]
                keyboard = InlineKeyboardMarkup(inline_keyboard = buttons)
                self.bot.sendMessage(chat_ID,text = 'Select one of the following optionals: ',reply_markup = keyboard)
            else:
                self.bot.sendMessage(chat_ID,text = "The given plate and your chat ID do not correspond. Insert another car's plate or digit 'finish' to end the communication: ")
        else:
            self.bot.sendMessage(chat_ID,text = "The given command does not exist. In order to manage car's optionals you have to use the command '/manage_optionals'.")

    def on_callback_query(self,msg):
        query_ID , chat_ID , query_data = telepot.glance(msg,flavor = 'callback_query')
        query_data = query_data.split(",")

        if (len(query_data) == 2 and self.communication == True):
            self.controlButton = True
            plate = query_data[0]
            optional = query_data[1]

            car = self.cars.find_one({"_id":plate})
            if (optional == "airConditioning"):
                for op in car["carOptionals"]:
                    if (op["optional"] == optional):
                        temperature = car["carSensors"][0]["e"][0]["v"]
                        humidity = car["carSensors"][1]["e"][0]["v"]
                        self.bot.sendMessage(chat_ID,text = f"The current temperature is around {temperature}°, while the humidity is almost {humidity}%.")

                        status = op["status"]
                        if (status == "off"):
                            self.temperature = car["carSensors"][0]["e"][0]["v"]
                            self.humidity = car["carSensors"][1]["e"][0]["v"]
                            button = [[InlineKeyboardButton(text = f'TURN ON',callback_data = f'{plate},airConditioning,on')]]
                            keyboard = InlineKeyboardMarkup(inline_keyboard = button)
                            self.bot.sendMessage(chat_ID,text = f"Actually the air conditioning system is {status}. \nThe aveilable operations are: \n- press the button 'TURN ON' to turn on the air conditioning system; \n- press one of the buttons above to retrieve information about another car's optional; \n- digit 'finish' to end the communication.",reply_markup = keyboard)
                        else:
                            button = [[InlineKeyboardButton(text = f'TURN OFF',callback_data = f'{plate},airConditioning,off')]]
                            keyboard = InlineKeyboardMarkup(inline_keyboard = button)
                            self.bot.sendMessage(chat_ID,text = f"Actually the air conditioning system is {status}. \nThe aveilable operations are: \n- press the button 'TURN OFF' to turn off the air conditioning system; \n- press one of the buttons above to retrieve information about another car's optional; \n- digit 'finish' to end the communication.",reply_markup = keyboard)
            else:
                for op in car["carOptionals"]:
                    if (op["optional"] == optional and optional == "doors"):
                        status = op["status"]
                        if (status == "open"):
                            button = [[InlineKeyboardButton(text = f'CLOSE',callback_data = f'{plate},doors,close')]]
                            keyboard = InlineKeyboardMarkup(inline_keyboard = button)
                            self.bot.sendMessage(chat_ID,text = f"The doors are actually {status}. \nThe aveilable operations are: \n- press the button 'CLOSE' if you want to close the car; \n- press one of the buttons above to retrieve information about another car's optional; \n- digit 'finish' to end the communication.",reply_markup = keyboard)
                        else:
                            button = [[InlineKeyboardButton(text = f'OPEN',callback_data = f'{plate},doors,open')]]
                            keyboard = InlineKeyboardMarkup(inline_keyboard = button)
                            self.bot.sendMessage(chat_ID,text = f"The doors are actually {status}. \nThe aveilable operations are: \n- press the button 'OPEN' if you want to open the car; \n- press one of the buttons above to retrieve information about another car's optional; \n- digit 'finish' to end the communication.",reply_markup = keyboard)
                    elif (op["optional"] == optional and optional == "windows"):
                        status = op["status"]
                        if (status == "up"):
                            button = [[InlineKeyboardButton(text = f'DOWN ⬇️',callback_data = f'{plate},windows,down')]]
                            keyboard = InlineKeyboardMarkup(inline_keyboard = button)
                            self.bot.sendMessage(chat_ID,text = f"The windows are actually {status}. \nThe aveilable operations are: \n- press the button 'DOWN' if you want to roll down the windows; \n- press one of the buttons above to retrieve information about another car's optional; \n- digit 'finish' to end the communication.",reply_markup = keyboard)
                        else:
                            button = [[InlineKeyboardButton(text = f'UP ⬆️',callback_data = f'{plate},windows,up')]]
                            keyboard = InlineKeyboardMarkup(inline_keyboard = button)
                            self.bot.sendMessage(chat_ID,text = f"The windows are actually {status}. \nThe aveilable operations are: \n- press the button 'UP' if you want to roll up the windows; \n- press one of the buttons above to retrieve information about another car's optional; \n- digit 'finish' to end the communication.",reply_markup = keyboard)
                    elif (op["optional"] == optional and optional == "lights"):
                        status = op["status"]
                        if (status == "on"):
                            button = [[InlineKeyboardButton(text = f'OFF',callback_data = f'{plate},lights,off')]]
                            keyboard = InlineKeyboardMarkup(inline_keyboard = button)
                            self.bot.sendMessage(chat_ID,text = f"The lights are actually {status}. \nThe aveilable operations are: \n- press the button 'OFF' if you want to turn off the lights; \n- press one of the buttons above to retrieve information about another car's optional; \n- digit 'finish' to end the communication.",reply_markup = keyboard)
                        else:
                            button = [[InlineKeyboardButton(text = f'ON',callback_data = f'{plate},lights,on')]]
                            keyboard = InlineKeyboardMarkup(inline_keyboard = button)
                            self.bot.sendMessage(chat_ID,text = f"The lights are actually {status}. \nThe aveilable operations are: \n- press the button 'ON' if you want to turn on the lights; \n- press one of the buttons above to retrieve information about another car's optional; \n- digit 'finish' to end the communication.",reply_markup = keyboard)
        elif (len(query_data) == 3 and self.controlButton == True):
            plate = query_data[0]
            optional = query_data[1]
            status = query_data[2]

            payload = self.__messageOptional.copy()
            payload["optional"] = optional
            payload["status"] = status
            t = time.time()
            payload["lastUpdate"] = time.strftime("%A, %d %B %Y %H:%M:%S",time.localtime(t))

            if (optional == 'doors'):
                self.client.myPublish(self.baseTopic + "/" + plate + "/doors",json.dumps(payload))
                self.bot.sendMessage(chat_ID,text = f"Doors of the car with {plate} as plate are {status}. \nThe operation has been succesfully completed.")
                self.bot.sendMessage(chat_ID,text = "To retrieve information about another car's optional you can use the four buttons above, otherwise digit 'finish'.")
                self.controlButton = False
            elif (optional == "windows"):
                self.client.myPublish(self.baseTopic + "/" + plate + "/windows",json.dumps(payload))
                self.bot.sendMessage(chat_ID,text = f"Windows of the car with {plate} as plate are {status}. \nThe operation has been succesfully completed.")
                self.bot.sendMessage(chat_ID,text = "To retrieve information about another car's optional you can use the four buttons above, otherwise digit 'finish'.")
                self.controlButton = False
            elif (optional == "lights"):
                self.client.myPublish(self.baseTopic + "/" + plate + "/lights",json.dumps(payload))
                self.bot.sendMessage(chat_ID,text = f"Lights of the car with {plate} as plate are {status}. \nThe operation has been succesfully completed.")
                self.bot.sendMessage(chat_ID,text = "To retrieve information about another car's optional you can use the four buttons above, otherwise digit 'finish'.")
                self.controlButton = False
            elif (optional == "airConditioning"):
                if (status == "off"):
                    self.client.myPublish(self.baseTopic + "/" + plate + "/airConditioning",json.dumps(payload))
                    self.bot.sendMessage(chat_ID,text = f"The air conditioning system of the car with {plate} as plate is {status}. \nThe operation has been succesfully completed.")
                    self.bot.sendMessage(chat_ID,text = "To retrieve information about another car's optional you can use the four buttons above, otherwise digit 'finish'.")
                    self.controlOneButton = False
                else:
                    self.sendTemperature = True
                    self.sendHumidity = True

                    buttons = [[InlineKeyboardButton(text = f'+1°',callback_data = f'{plate},{optional},{status},{self.temperature},incr,temperature')], 
                            [InlineKeyboardButton(text = f'-1°',callback_data = f'{plate},{optional},{status},{self.temperature},decr,temperature')],
                            [InlineKeyboardButton(text = f'SEND',callback_data = f'{plate},{optional},{status},{self.temperature},publish,temperature')]]
                    keyboard = InlineKeyboardMarkup(inline_keyboard = buttons)
                    self.bot.sendMessage(chat_ID,text = "The aveilable operations are: \n- press + to increase the temperature of 1°; \n- press - to decrease the temperature of 1°; \n - press 'SEND' to modify the settings of the air conditioning system; \n- press one of the four buttons above to retrieve information about another car's optional; \n- digit 'finish' to end the communication.",reply_markup = keyboard)
                
                    buttons = [[InlineKeyboardButton(text = f'+2%',callback_data = f'{plate},{optional},{status},{self.humidity},incr,humidity')], 
                            [InlineKeyboardButton(text = f'-2%',callback_data = f'{plate},{optional},{status},{self.humidity},decr,humidity')],
                            [InlineKeyboardButton(text = f'SEND',callback_data = f'{plate},{optional},{status},{self.humidity},publish,humidity')]]
                    keyboard = InlineKeyboardMarkup(inline_keyboard = buttons)
                    self.bot.sendMessage(chat_ID,text = "The aveilable operations are: \n- press + to increase the humidity of 2%; \n- press - to decrease the humidity of 2%; \n - press 'SEND' to modify the settings of the air conditioning system; \n- press one of the four buttons above to retrieve information about another car's optional; \n- digit 'finish' to end the communication.",reply_markup = keyboard)
        elif (len(query_data) == 6):
            plate = query_data[0]
            optional = query_data[1]
            status = query_data[2]
            action = query_data[4]
            measure = query_data[5]

            t = time.time()
            t = time.strftime("%A, %d %B %Y %H:%M:%S",time.localtime(t))
            payload = {"optional":optional,"status":status,"measure":"","value":0,"lastUpdate":t}

            if (measure == "temperature" and self.sendTemperature == True):
                payload["measure"] = "temperature"
                if (action == "incr"):
                    self.temperature += 1
                elif (action == "decr"):
                    self.temperature -= 1
                else:
                    payload["value"] = self.temperature
                    self.client.myPublish(self.baseTopic + "/" + plate + "/airConditioning/temperature",json.dumps(payload))
                    self.bot.sendMessage(chat_ID,text = f"The air conditioning system of the car with {plate} as plate is {status}. \nTemperature has been set up to {self.temperature}°. \nThe operation has been succesfully completed.")
                    self.sendTemperature = False
            elif (measure == "humidity" and self.sendHumidity == True):
                payload["measure"] = "humidity"
                if (action == "incr"):
                    self.humidity += 2
                elif (action == "decr"):
                    self.humidity -= 2
                else:
                    payload["value"] = self.humidity
                    self.client.myPublish(self.baseTopic + "/" + plate + "/airConditioning/humidity",json.dumps(payload))
                    self.bot.sendMessage(chat_ID,text = f"Humidity has been set up to {self.humidity}°. \nThe operation has been succesfully completed.")
                    self.bot.sendMessage(chat_ID,text = "To retrieve information about another car's optional you can use the four buttons above, otherwise digit 'finish'.")
                    self.sendHumidity = False

    def notify(self,topic,msg):
        topic = topic.split("/")
        plate = topic[1]

        payload = json.loads(msg)
        temperature = payload["e"][0]["v"]
        humidity = payload["e"][1]["v"]
        timestamp = payload["e"][0]["t"]

        carSensors = self.cars.find_one({"_id":plate})["carSensors"]
        for sensor in carSensors:
            if (sensor["bn"] == "TS"):
                sensor["e"][0]["v"] = temperature
                sensor["e"][0]["t"] = timestamp
            else:
                sensor["e"][0]["v"] = humidity
                sensor["e"][0]["t"] = timestamp
        self.cars.find_one_and_update({"_id":plate},{"$set":{"carSensors":carSensors}})

        url = self.cars.find_one({"_id":plate})["thingspeakChannel"]
        req = requests.get(url + "&field3={}&field4={}".format(str(temperature),str(humidity)))
        print(f"ThingSpeak data delivered with status \t{req}")

if __name__ == "__main__":
    resourcesfilenameSC = "SmartCarCatalog.json"
    try:
        username = str(input("Enter the username to obtain necessary resources: "))
        password = str(input("Enter the password to obtain necessary resources: "))
        if (username == "Settings" and password == "pr0jecti0t"):
            print("Accessing the ServiceCatalog to discover resources...")
            client1 = MongoClient(f"mongodb+srv://{username}:{password}@icar.bpz7hb7.mongodb.net/?retryWrites=true&w=majority")
            dbService = client1.ServiceCatalog
            resources = dbService.Resources
            catalogSC = resources.find_one({"filename": resourcesfilenameSC})
            clienturlSC = catalogSC["client"]
        else:
            print("Wrong username or password!")
    except:
        raise Exception("It's not possible to access the database containing the resources needed!")

    try:
        file = open("bot_settings.json")
        conf = json.load(file)
        broker = conf["broker"]
        port = conf["port"]
        token = conf["token2"]
        clientID = conf["clientID2"]
    except:
        raise FileNotFoundError("Problem with the file 'car_setting.json'")
    finally:
        file.close()

    baseTopic = "CarSystem"
    cb = CarBot(broker,port,token,clientID,baseTopic,clienturlSC)
    cb.start()
    print("Bot started ...")

    while True:
        time.sleep(3)

    cb.stop()