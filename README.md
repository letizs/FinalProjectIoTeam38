# FinalProjectIoTeam38

BRIEF EXPLANATION OF THE PROJECT:

Here is the organization of the scripts divided for every microservice, while in the repository they are organized as they were running in the actual physical PCs
(ex. in the folder Car there are the scripts potentially running in the Car but two different microservices are agreeing among them)

°MICROSERVICE 1 -CAR MONITORING-

-CarStatistics_pub.py : it acts as a publisher for daily consumes and kilometers and for every airbag activations. 
			The topic contains the ID (plate) of the specific car in which the simulated sensors are generating those data, plus a keyword to identify from 			where the measures come.
			To try the script we didn't publish everyday but at a shortened time.
-IndustriesCatalogClient.py : it acts as a subscriber for daily consumes, kilometers and airbag activations data, receiving the data from all the cars registered in 				   the Industries Catalog.
			      After a check on the plate mean consumes and mean kilometers are calculated every 30 days, while airbag activations are calculated as the 			      sum in a year.
			      All this statistics are then registered in the Industries Catalog for every car, as soon as the client has enough data.
			      The daily data about consumes and kilometers are sent to the Thingspeak database as they arrive, while only the monthly means are sent to 			      NodeRed to be grafically inspectable. So this Client also publishes.
-ICarStatisticsBot.py : it manages the ICarStatistics Telegram Bot acting as a subscriber for data generated by the airbag sensors in the car with the objective of 			    sending an alarm message to the user.
			From Telegram the Airbag Alarm can be deactivated, otherwise an ambulance is theoretically called after 3 minutes.
			From this Bot is also possible to report Electrical or Mechanical damages that will be registered in the Industries Catalog.
-IndustriesCatalogManager.py : through REST web services it is possible to add, view, update or delete owners/cars in the Industries Catalog.
-DamagesList.py : through REST web services the user can have a complete list of the damages he reported to the Industry.





°°MICROSERVICE 2 -REMOTE CAR CONTROL-

-CarOptionals.py : This script manages all the optionals of a car, in particular it exploits MQTT in order to receive commands that the correspondent user sends by 		       Telegram. 
		   These updates are also uploaded in the database. At the same time, it publishes temperature and humidity data every two minutes as publisher.
-ICarManagerBot.py : This script controls a Telegram bot, useful for user in order to change the status of different optionals, like doors, windows, lights and air 			 conditioning system. 
                     What's more, it receives temperature and humidity data, which are published by CarOptionals.py, that are send to the database and to the car 		       specific ThingSpeak channel.





°°°MICROSERVICE 3 -DRIVER MONITORING-

-Smartwatch_pub.py : it publishes the heart rate of a user generated by a simulated sensor in his personal smartwatch having the smartwatch ID in its topic.
		     It publishes bpm directly so a value every 60 seconds.
-Smartwatch_bot.py : it act as a subscriber for the Smartwatch_pub and if data are below or over a threshold a warning message is sent to this specific Telegram Bot 			  chat reaching the user registerd with that smartwatch ID.
		     It also sends the data to the user specific Thingspeak channel and to NodeRed.
-SmartCarCatalogManager.py : it provides a REST interface to show all drivers and all cars present in the SmartCarCatalog, 
			     with the possibilty to modify it with a POST method and delete a car or a driver by specifing 
			     the plate(car) and the ID (driver). 
-UserManager.py : Client that performs http requests, useful for our company to interact with the SmartCarCataloManager and manipulate the catalog through: a file.json 
		  to modify it, and the ID or plate to delete a driver or a car.








SETTINGS FILES:
In every folder there are also all the settings files (.json) needed for configuration, for example the info about clientID, message broker, port, topics, telegram bots, thingspeak channels...


CATALOGS: (!!!All updated to clearly visualize the structure BUT we don't use them locally, they are in Mongo database!!!)
-All the configuration info are also registered in the SmartCarCatalog.json file that also contains data about drivers and cars for which services are active. For every car there is the section with data about sensors and actuators of the Remote Car control microservice.
-The IndustriesCatalog.json contains all the cars that are registered to the service that manages car statistics (Car Manager) and for every car there is the section with statistic and damages data.
-The ServiceCatalog.json is needed to manage the other two previously mentioned, the service can reach this one inserting username and password and then from this database it takes the url of the specific database needed between the two others.


MONGO DATABASE:
All the catalogs mentioned above are in three Mongo databases and so they are reachable from every host as they are online. 
One database contains only the ServiceCatalog.json that is reachable inserting username and password. 
Once this one is reached, as it contains the end-points (url) to reach the other two stored in other databases, the necessary resources catalogs can be read and manipulated.


THINGSPEAK:
-Channel 1: It's used to store data about the user heart-rate by microservice 3.
-Channel 2: It's used to store data coming from microservice 1 (consumes and kilometers) and 2 (temperature and humidity).
There is a specific channel for every user and for every car. The API is stored in the SmartCarCatalog. (We reported one in the DEMO as an example)


NODERED:
-flow1 : subscribes to obtain data coming from microservice 3. In the related dashboard there is has a gauge about heart-rate and also thingspeak charts from Channel1.
-flow2 : subscribes to obtain data coming from micriservice 1. In the related dashboard there are charts about consumes and kilometers.
There is a specific NodeRed flow for every car and for every user. It subscribes to the topics containing the specific smartwatch ID or plate (We reported one in the DEMO as an example)
