import numpy
import random
import schedule
import time
import json
from http import client
from MyMQTT import *
from pymongo import MongoClient

class Optionals:
    def __init__(self,broker,port,baseTopic,clientID,plate,clienturlSC):
        client = MongoClient(clienturlSC)
        db = client.SmartCarCatalog
        self.cars = db.Cars

        self.plate = plate
        self.client = MyMQTT(clientID,broker,port,self)

        self.topicDoors = baseTopic + "/" + self.plate + "/doors"
        self.topicWindows = baseTopic + "/" + self.plate + "/windows"
        self.topicLigths = baseTopic + "/" + self.plate + "/lights"
        self.topicAirConditioning = baseTopic + "/" + self.plate + "/airConditioning"
        self.topicTemperature = baseTopic + "/" + self.plate + "/airConditioning/temperature"
        self.topicHumidity = baseTopic + "/" + self.plate + "/airConditioning/humidity"
        self.topicTempHum = baseTopic + "/" + self.plate + "/temp&hum"

        self.message = {"bn":"CarSensors",
                        "e":
                        [
                            {"n":"temperature","u":"Cel°","t":"","v":""},
                            {"n":"humidity","u":"%","t":"","v":""}
                        ]
        }

    def start (self):
        self.client.start()
        self.client.mySubscribe(self.topicDoors)
        self.client.mySubscribe(self.topicWindows)
        self.client.mySubscribe(self.topicLigths)
        self.client.mySubscribe(self.topicAirConditioning)
        self.client.mySubscribe(self.topicTemperature)
        self.client.mySubscribe(self.topicHumidity)

    def stop (self):
        self.client.stop()

    def notify(self,topic,msg):
        payload = json.loads(msg)
        optional = payload["optional"]
        status = payload["status"]
        timestamp = payload["lastUpdate"]

        carOptionals = self.cars.find_one({"_id":self.plate})["carOptionals"]
        for op in carOptionals:
            if (op["optional"] == optional and optional != "airConditioning"):
                op["status"] = status
                op["lastUpdate"] = timestamp
                self.cars.find_one_and_update({"_id":self.plate},{"$set":{"carOptionals":carOptionals}})
                print(f'The {optional} of the car with {plate} as plate are {status} ({timestamp}, client: {client}).')
            elif (op["optional"] == optional and optional == "airConditioning"):
                if (status == "off"):
                    op["status"] = status
                    op["temperature"] = 0
                    op["humidity"] = 0
                    op["lastUpdate"] = timestamp
                    self.cars.find_one_and_update({"_id":self.plate},{"$set":{"carOptionals":carOptionals}})
                    print(f'The air conditioning system of the car with {plate} as plate is {status} ({timestamp}, client: {client}).')
                else:
                    op["status"] = status
                    if (payload["measure"] == "temperature"):
                        op["temperature"] = payload["value"]
                        op["lastUpdate"] = timestamp
                        self.cars.find_one_and_update({"_id":self.plate},{"$set":{"carOptionals":carOptionals}})
                        print(f'The temperature for the air conditioning system of the car with {plate} as plate has been set up to {payload["value"]}° ({timestamp}, client: {client}).')
                    elif (payload["measure"] == "humidity"):
                        op["humidity"] = payload["value"]
                        op["lastUpdate"] = timestamp
                        self.cars.find_one_and_update({"_id":self.plate},{"$set":{"carOptionals":carOptionals}})
                        print(f'The humidity for the air conditioning system of the car with {plate} as plate has been set up to {payload["value"]}° ({timestamp}, client: {client}).')

    def sendData(self):
        carOptionals = self.cars.find_one({"_id":self.plate})["carOptionals"]
        carSensors = self.cars.find_one({"_id":self.plate})["carSensors"]
        payload = self.message.copy()

        for op in carOptionals:
            if (op["optional"] == "airConditioning"):
                if (op["status"] == "off"):
                    for sensor in carSensors:
                        if (sensor["bn"] == "TS"):
                            temperature = sensor["e"][0]["v"]
                            if (temperature == ""):
                                temperature = int(numpy.random.uniform(10,40))
                            else:
                                if (random.choice([0,1]) == 0):
                                    temperature += 0.5
                                else:
                                    temperature -= 0.5
                        elif (sensor["bn"] == "HS"):
                            humidity = sensor["e"][0]["v"]
                            if (humidity == ""):
                                humidity = int(numpy.random.uniform(50,90))
                            else:
                                if (random.choice([0,1]) == 0):
                                    humidity += 1
                                else:
                                    humidity -= 1

                    payload['e'][0]['v'] = temperature
                    payload['e'][1]['v'] = humidity
                    t = time.time()
                    payload['e'][0]['t'] = time.strftime("%A, %d %B %Y %H:%M:%S",time.localtime(t))
                    payload['e'][1]['t'] = time.strftime("%A, %d %B %Y %H:%M:%S",time.localtime(t))
                    self.client.myPublish(self.topicTempHum,json.dumps(payload))
                else:
                    temperature = op["temperature"]
                    payload['e'][0]['v'] = temperature
                    humidity = op["humidity"]
                    payload['e'][1]['v'] = humidity
                    t = time.time()
                    payload['e'][0]['t'] = time.strftime("%A, %d %B %Y %H:%M:%S",time.localtime(t))
                    payload['e'][1]['t'] = time.strftime("%A, %d %B %Y %H:%M:%S",time.localtime(t))
                    self.client.myPublish(self.topicTempHum,json.dumps(payload))

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
        file = open("car_settings.json")
        conf = json.load(file)
        broker = conf["broker"]
        port = conf["port"]
        baseTopic = conf["mqttTopic"]
        clientID = conf["clientID2"]
    except:
        raise FileNotFoundError("Problem with the file 'car_setting.json'")
    finally:
        file.close()
    
    plate = clientID.split("_")[0]
    opt = Optionals(broker,port,baseTopic,clientID,plate,clienturlSC)
    opt.start()
    opt.sendData()
    schedule.every(120).seconds.do(opt.sendData)

    while True:
        schedule.run_pending()
        time.sleep(1)

    opt.stop()