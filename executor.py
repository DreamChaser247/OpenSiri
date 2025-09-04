import json
import subprocess 
from datetime import datetime

class CommandExecutor:
    def __init__(self):
        pass
    
    def getTheAppName(self, commandIngredients):
        appName = ""
        if len(commandIngredients) == 2:
            appName = commandIngredients[1]
        elif commandIngredients[1] == "the":
                appName = commandIngredients[2]
        with open("apps.json", "r") as f:
            appMapping = json.load(f)
            appName = appMapping.get(appName, appName)
        return appName
    
    def openApp(self, commandIngredients):
        appName = self.getTheAppName(commandIngredients)
        print(f"opening {appName}")

        try:
            subprocess.Popen([appName])
        except:
            print(f"Error: Could not find an application named '{appName}'.")
    
    def closeApp(self, commandIngredients):
        appName = self.getTheAppName(commandIngredients)
        if commandIngredients[1] == "yourself":
                print("Disabling myself...")
                raise KeyboardInterrupt
        return {
            "awaitingProcess": "closeConfirm",
            "objectOfQuestion": appName,
            "question": f"Are you sure you want to close {appName}?"
        }
    def closeAppConfirmed(self, commandIngredients, processToKill=""):
        with open("reactions.json", "r") as f:
            reactions = json.load(f)
            commandToRun = f"pkill {processToKill}"
            print(commandToRun)
            if commandIngredients[1] in reactions["confirmation"]:
                print(f"closing {processToKill}")
                subprocess.Popen([commandToRun], shell=True)
            else:
                print("failed to confirm")

    def tellTime(self):
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        print(f"The current time is {current_time}")

    def tellDate(self):
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        print(f"Today's date is {current_date}")

    def controlVolume(self, commandIngredients):
        if commandIngredients[1] == "up":
            subprocess.Popen(["pactl set-sink-volume @DEFAULT_SINK@ +10%"], shell=True)
        elif commandIngredients[1] == "down":
            subprocess.Popen(["pactl set-sink-volume @DEFAULT_SINK@ -10%"], shell=True)
        elif commandIngredients[1] == "mute":
            subprocess.Popen(["pactl set-sink-mute @DEFAULT_SINK@ toggle"], shell=True)
        