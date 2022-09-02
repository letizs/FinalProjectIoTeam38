import certifi
import cherrypy
import json
import json2table
from pymongo import MongoClient

class ICManagement:
    exposed = True
    
    def __init__(self,clienturlI):
        self.clienturlI=clienturlI

        client2 = MongoClient(self.clienturlI)
        db = client2.IndustriesCatalog
        self.cars = db.Cars

    def GET(self,*uri,**params):
        if (len(uri) > 0):
            if (uri[0] == "PrintCars"):
                build_direction = "TOP_TO_BOTTOM"
                table_attributes = {"style": "width:100%","class" : "table table-striped", "border":2}

                dict = {"CARS":[]}
                for car in self.cars.find():
                    dict["CARS"].append(car)

                table = json2table.convert(dict,build_direction = build_direction,table_attributes = table_attributes)
                title = f"Here is your Catalog:\n"
                return title,table
            elif (uri[0] == "SearchCar"):
                if (len(params) == 0):
                    raise cherrypy.HTTPError(400,"Please add the plate as a parameter.")
                else:
                    plate = str(params["plate"])                                                        # host:port/SearchCar?plate=XXNNNXX
                    flag = 0

                    for car in self.cars.find():
                        if (car["plate"] == plate):
                            build_direction = "TOP_TO_BOTTOM"
                            table_attributes = {"style": "width:100%","class" : "table table-striped", "border":2}
                            table = json2table.convert(car,build_direction = build_direction,table_attributes = table_attributes)
                            title = f"Data about the car with {plate} as plate:\n"
                            flag = 1
                            return title,table
                    
                    if (flag == 0):
                        raise cherrypy.HTTPError(404,"Car plate not found! Try anotherone.") 
            else:
                raise cherrypy.HTTPError(404,"URI not available or more informations needed.") 
        else:
            raise cherrypy.HTTPError(400,"You have to specify a URI.")

    def POST(self,*uri,**params):
        if (len(uri) > 0):
            if (uri[0] == "InsertNewCar"):
                body = cherrypy.request.body.read() 
                new_car = json.loads(body) 

                if (self.cars.find_one({"plate":new_car["plate"]})!= None):
                    raise cherrypy.HTTPError(400,"The plate you typed already exists in the Catalog. Please check before inserting this car!\nIf you want to modify an existing car use the URI: '/UpdateCarData'.")
                else:
                    new_car["statistics"] = {"damage_number":0,"damages":[],"last_month_consumes(L/100km)":"","last_month_daily_km":"","annual_airbag_activations":""} 
                    self.cars.insert_one(new_car)

                    build_direction = "TOP_TO_BOTTOM"
                    table_attributes = {"style": "width:100%","class" : "table table-striped", "border":2}

                    dict = {"CARS":[]}
                    for car in self.cars.find():
                        dict["CARS"].append(car)

                    table = json2table.convert(dict,build_direction = build_direction,table_attributes = table_attributes)
                    title = f"Here is your updated Catalog:\n"
                    return title,table
            else:
                raise cherrypy.HTTPError(404,"URI not available.")
        else:
            raise cherrypy.HTTPError(400,"You have to specify a URI.")

    def PUT(self,*uri,**params):
        if (len(uri) > 0):
            if (uri[0] == "UpdateCarData"):
                if (len(params) == 0):
                    raise cherrypy.HTTPError(400,"Please add the plate as a parameter.")
                else:
                    plate = str(params["plate"])                                                          # host:port/UpdateCarData?plate=XXNNNXX
                    
                    car=self.cars.find_one({"plate":plate})
                    if car!=None:
                        body = cherrypy.request.body.read() 
                        values_modified = json.loads(body)                                            # only the arguments (key:value) I want to modify
                        for key in values_modified.keys():
                            if (key == "owner_data"):
                                for k in values_modified["owner_data"].keys():
                                    car["owner_data"][k] = values_modified["owner_data"][k]   
                                self.cars.find_one_and_update({"plate":plate},{"$set":{"owner_data":car["owner_data"]}})
                            else:
                                self.cars.find_one_and_update({"plate":plate},{"$set":{key:values_modified[key]}})

                        build_direction = "TOP_TO_BOTTOM"
                        table_attributes = {"style": "width:100%","class" : "table table-striped", "border":2}

                        dict = {"CARS":[]}
                        for car in self.cars.find():
                            dict["CARS"].append(car)

                        table = json2table.convert(dict,build_direction = build_direction,table_attributes = table_attributes)
                        title = f"Here is your updated car:\n"
                        return title,table 
                    else:
                        raise cherrypy.HTTPError(404,"Car plate not found! Try anotherone. If you want to add a new car use the URI: '/InsertNewCar'.")
            else:
                raise cherrypy.HTTPError(404,"URI not available.")
        else:
            raise cherrypy.HTTPError(400,"You have to specify a URI.")

    def DELETE(self,*uri,**params):
        if (len(uri) > 0):
            if (uri[0] == "DeleteCar"):
                if (len(params) == 0):
                    raise cherrypy.HTTPError(404,"Car plate not found! Try anotherone.")
                else:
                    plate = str(params["plate"]) 
                    car=self.cars.find_one({"plate":plate})                                                      # host:port/DeleteCar?plate=XXNNNXX
                    
                    if (car == None):   
                        raise 
                    else:
                        self.cars.delete_one({"plate":plate})
                
                        build_direction = "TOP_TO_BOTTOM"
                        table_attributes = {"style": "width:100%","class" : "table table-striped", "border":2}


                        table= json2table.convert(car,build_direction = build_direction,table_attributes = table_attributes)
                        title=f"Here is your deleted car:\n"
                        return title,table
            else:
                cherrypy.HTTPError(404,"URI not available.")
        else:
            raise cherrypy.HTTPError(400,"You have to specify a URI.")

if __name__ == '__main__':
    resourcesfilenameI="IndustriesCatalog.json"
    try:
        username=str(input("Enter the username to obtain necessary resources: "))
        password=str(input("Enter the username to obtain necessary resources: "))
        if username=="Settings" and password=="pr0jecti0t":
            print("Loading...")
            client1 = MongoClient(f"mongodb+srv://{username}:{password}@icar.bpz7hb7.mongodb.net/?retryWrites=true&w=majority")
            dbService = client1.ServiceCatalog
            resources=dbService.Resources
            catalogI=resources.find_one({"filename": resourcesfilenameI})
            clienturlI=catalogI["client"]
        else:
            print("Wrong username or password!")
    except:
        raise FileNotFoundError("It's not possible to access the database containing the resources needed!")
    conf = {
        '/': {
                'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
                'tool.session.on': True
        }
    }
    cherrypy.tree.mount(ICManagement(clienturlI),'/',conf)
    cherrypy.config.update(conf)
    cherrypy.engine.start()
    cherrypy.engine.block()