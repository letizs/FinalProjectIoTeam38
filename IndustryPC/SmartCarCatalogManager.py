from ast import Delete
import certifi
import cherrypy
import json2table
import time
from pymongo import MongoClient

class DriverCatalogREST():
    exposed = True

    def __init__(self,clienturlSC):
        self.clienturlSC=clienturlSC

        client2 = MongoClient(self.clienturlSC)
        db = client2.SmartCarCatalog
        self.cars = db.Cars
        self.users = db.Users
        self.bots = db.TelegramBots

    def GET(self,*uri,**params):
        if (len(uri) == 2):
            name = uri[0]
            surname = uri[1]
            chatID = int(params["chatID"])
            user = self.users.find_one({"name":name,"surname":surname})

            if (user == None):
                raise cherrypy.HTTPError(400,f"User {name} {surname} does not exists.")
            else:
                if (user["chatID"] == chatID):
                    build_direction = "TOP_TO_BOTTOM"
                    table_attributes = {"style":"width:100%","class":"table table-striped","border":2}
                    table = json2table.convert(user,build_direction = build_direction,table_attributes = table_attributes)
                    title = "Driver's information:\n" 
                    return title,table
                else:
                    raise cherrypy.HTTPError(400,f"The given user and chatID do not correspond.")         
        elif (len(uri) == 1):
            if (uri[0] == "bots"):
                build_direction = "TOP_TO_BOTTOM"
                table_attributes = {"style":"width:100%","class":"table table-striped","border":2}

                dict = {"BOTS":[]}
                for bot in self.bots.find():
                    dict["BOTS"].append(bot)

                table = json2table.convert(dict,build_direction = build_direction,table_attributes = table_attributes)
                title = f"These are the aveilable bots:\n"
                return title,table
            else:
                plate = uri[0]
                chatID = int(params["chatID"])
                car = self.cars.find_one({"_id":plate})

                if (car == None):
                    raise cherrypy.HTTPError(400,f"Car with {plate} as plate does not exists.")
                else:
                    find = False
                    for c in car["chatID_drivers"]:
                        if (c == chatID):
                            find = True
                            build_direction = "TOP_TO_BOTTOM"
                            table_attributes = {"style":"width:100%","class":"table table-striped","border":2}
                            table = json2table.convert(car,build_direction = build_direction,table_attributes = table_attributes)
                            title = "Driver's information:\n" 
                            return title,table
                    
                    if (find == False):
                        raise cherrypy.HTTPError(400,f"The given car and chatID do not correspond.") 
    
    @cherrypy.tools.json_in()
    def POST(self,*uri):
        body = cherrypy.request.json   
             
        if (uri[0] == 'driver'):    
            chatID = body["chatID"]
            user = self.users.find_one({"chatID":chatID})

            if (user == None):
                self.users.insert_one(body)
            else:
                for key in body.keys():
                    self.users.find_one_and_update({"chatID":chatID},{"$set":{key:body[key]}})

                t = time.time()
                t = time.strftime("%A, %d %B %Y %H:%M:%S",time.localtime(t))
                self.users.find_one_and_update({"chatID":chatID},{"$set":{"lastUpdate":t}})
        elif (uri[0] == "car"):
            plate = uri[1]
            chatID = body["chatID_drivers"]
            car = self.cars.find_one({"_id":plate})

            if (car == None):
                self.cars._insert_one(body)
            else:
                find = False

                for c in car["chatID_drivers"]:
                    if (c == chatID):
                        for key in body.keys():
                            self.cars.find_one_and_update({"_id":plate},{"$set":{key:body[key]}})


                        find = True

                if (find == False):
                    raise cherrypy.HTTPError(400,f"The given car and chatID do not correspond.")
    
    def DELETE(self,*uri,**params):
        chatID = params["chatID"]

        if (uri[0] == "driver"):
            if (self.users.find_one({"chatID":chatID}) == None):
                raise cherrypy.HTTPError(400,f"User with {chatID} as chatID does not exists.")
            else:
                self.users.find_one_and_delete({"chatID":chatID})
        elif (uri[0] == "car"):
            plate = uri[1]
            car = self.cars.find_one({"plate":plate})

            if (car == None):
                raise cherrypy.HTTPError(400,f"Car with {plate} as plate does not exists.")
            else:
                find = False
                for c in car["chatID_drivers"]:
                    if (c == chatID):
                        self.cars.find_one_and_delete({"plate":plate})
                        find = True
                
                if (find == False):
                    raise cherrypy.HTTPError(400,f"The given car and chatID do not correspond.")
   
if __name__ == '__main__':
    resourcesfilenameSC="SmartCarCatalog.json"
    try:
        username=str(input("Enter the username to obtain necessary resources: "))
        password=str(input("Enter the username to obtain necessary resources: "))
        if username=="Settings" and password=="pr0jecti0t":
            print("Loading...")
            client1 = MongoClient(f"mongodb+srv://{username}:{password}@icar.bpz7hb7.mongodb.net/?retryWrites=true&w=majority")
            dbService = client1.ServiceCatalog
            resources=dbService.Resources
            catalogSC=resources.find_one({"filename": resourcesfilenameSC})
            clienturlSC=catalogSC["client"]

            conf = { 
                '/': { 
                        'request.dispatch': cherrypy.dispatch.MethodDispatcher(), 
                        'tools.sessions.on': True, 
                } 
            } 
            cherrypy.tree.mount(DriverCatalogREST(clienturlSC), '/', conf)
            cherrypy.config.update({'server.socket_host': '0.0.0.0'})
            cherrypy.config.update({'server.socket_port': 8070})
            cherrypy.engine.start()
            cherrypy.engine.block()
        else:
            print("Wrong username or password!")
    except:
        raise Exception("It's not possible to access the database containing the resources needed!")
    