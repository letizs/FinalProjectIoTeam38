import json
import requests

class ManageCommunication():
    def __init__(self):
        self.url = "http://127.0.0.1:8070"

    def PrintUser(self,name,surname,chatID):
        information = requests.get(f"{self.url}/{name}/{surname}?chatID={chatID}")
        return information.url

    def PrintCar(self,plate,chatID):
        information = requests.get(f"{self.url}/{plate}?chatID={chatID}")
        return information.url

    def PrintBots(self,choose):
        information = requests.get(f"{self.url}/{choose}")
        return information.url

    def CreateOrUpdateDriver(self,choose,data):
        operation = requests.post(f"{self.url}/{choose}",json = data)
        return operation.status_code
    
    def CreateOrUpdateCar(self,choose,plate,data):
        operation = requests.post(f"{self.url}/{choose}/{plate}",json = data)
        return operation.status_code

    def DeleteUser(self,chatID,choose):
        operation = requests.delete(f"{self.url}/{choose}?chatID={chatID}")
        return operation.status_code

    def DeleteCar(self,plate,chatID,choose):
        operation = requests.delete(f"{self.url}/{choose}/{plate}?chatID={chatID}")
        return operation.status_code
    
if __name__ == '__main__':
    print("Welcome!")
    manager = ManageCommunication()

    while True:
        command = str(input("Insert an operation to perform one of the following actions: \n\
            - 'print' to print information about you or your cars; \n\
            - 'add' to add/update a driver or a car; \n\
            - 'del' to delate a driver or a car; \n\
            - 'quit' to end the execution. \n"))
        if (command == "print"):
            choose = str(input("Digit: \n\
                - 'driver' to print information about you; \n\
                - 'car' to print information about your cars; \n\
                - 'bots' to print information about the aveilable bot; \n\
                - 'back' to return to the principal menu. \n"))
            
            if (choose == "driver"):
                name = str(input("Insert your name: "))
                surname = str(input("Insert your surname: "))
                chatID = str(input("Insert your chatID: "))
                
                url = manager.PrintUser(name,surname,chatID)
                print(f"Go to the link '{url}' to view the data")
            elif (choose == "car"):
                plate = str(input("Insert the plate: "))
                chatID = str(input("Insert your chatID: "))
                
                url = manager.PrintCar(plate,chatID)
                print(f"Go to the link '{url}' to view the data")
            elif (choose == "bots"):
                url = manager.PrintBots(choose)
                print(f"Go to the link '{url}' to view the data")
            elif (choose != "back"):
                print("The command is not valid")
        elif (command =='add'):
            choose = str(input("Digit: \n\
                - 'driver' to insert a new user or updating an existing one; \n\
                - 'car' to insert a new car or updating an existing one; \n\
                - 'back' to return to the principal menu. \n"))

            try:
                file = open("DriverInfo.json","r")
                data = json.load(file)
            except:
                print("Problem with the file 'DriverInfo.json'")
            finally:
                file.close()

            if (choose == "driver"):
                code = manager.CreateOrUpdateDriver(choose,data)
                print (f"Status code: {code}")
            elif (choose=="car"):
                plate = str(input("Insert the plate: "))
                code = manager.CreateOrUpdateCar(choose,plate,data)
                print (f"Status code: {code}")
            elif (choose != "back"):
                print("The command is not valid")
        elif (command == 'del'):
            choose = str(input("Digit: \n\
                - 'driver' to delete an user; \n\
                - 'car' to delete a car; \n\
                - 'back' to return to the principal menu. \n"))

            if (choose == 'car'):
                plate = str(input(f'Insert the plate of the car to remove: '))
                chatID = str(input("Insert its chatID: "))
                action = manager.DeleteCar(plate,chatID,choose)
                print(f"Status code: {action}")
            elif (choose == 'driver'):
                user = str(input(f'Insert the chatID of the driver to remove: '))
                action = manager.DeleteUser(user,choose)
                print(f"Status code: {action}")
            elif (choose != "back"):
                print("The command is not valid")
        elif (command == 'quit'):
            print("Bye!")
            break
        else:
            print(f"ERROR: the given command does not exist)")