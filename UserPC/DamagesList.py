# HTTP GET method to retrive a table with all the damages listed in the Industries Catalog for a specific car plate 
import cherrypy
import json2table
import json
from pymongo import MongoClient

class DamagesList:
    exposed = True
    
    def __init__(self,clienturlI):
        self.clienturlI=clienturlI

        client2 = MongoClient(self.clienturlI)
        db = client2.IndustriesCatalog
        self.cars = db.Cars
        
    def GET(self,*uri,**params):                                                            # localhost:port/CarManager/myDamagesList?plate=...
        if (len(uri) >= 1):
            if (uri[0] == "CarManager"):
                if (len(uri) == 1):
                    raise cherrypy.HTTPError(404,"More informations needed.")
                else:
                    if (uri[1] == "myDamagesList"):
                        if (len(params) == 0):
                            raise cherrypy.HTTPError(400,"Please add the plate as a parameter.")
                        else:
                            plate = str(params["plate"])     
                            flag = 0

                            for car in self.cars.find():
                                if (car["plate"] == plate):
                                    damages = {"DAMAGES":car["statistics"]["damages"]}

                                    build_direction = "TOP_TO_BOTTOM"
                                    table_attributes = {"style":"width:100%","class":"table table-striped","border":2}
                                    table = json2table.convert(damages,build_direction = build_direction,table_attributes = table_attributes)
                                    title = f"List of damages of your car with plate {plate}:\n"
                                    flag = 1
                                    return title,table

                            if (flag == 0):
                                raise cherrypy.HTTPError(404,"Car plate not found! Try anotherone.") 
                    else:
                        raise cherrypy.HTTPError(404,"URI not available.") 
            else:
                raise cherrypy.HTTPError(404,"Warning! Keyword necessary to access the data!")
        else:
            raise cherrypy.HTTPError(400,"You have to specify a URI.")

if __name__ == '__main__':
    resourcesfilenameI="IndustriesCatalog.json"
    try:
        username=str(input("Enter the username to obtain the damages table: "))
        password=str(input("Enter the password to obtain the damages table: "))
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
    cherrypy.tree.mount(DamagesList(clienturlI),"/",conf)
    cherrypy.config.update({'server.socket_port': 8089})
    cherrypy.engine.start()
    cherrypy.engine.block()