#The system depends on the ollama app and the llama 3.1 model being installed
#Ollama can be installed at https://ollama.com/download/windows
#The model can be downloaded via command prompt with the command "ollama pull llama3.1:latest" (remove the quotes when actually run)

import ollama
from django.conf import settings
from django.db import models

class AILocation(models.Model):
    #Parameters are created as empty strings on startup so the data fields can still be referenced in views
    location = ""
    rawOutput = ""

    def giveSuggestion(self, destIn):
        #Define the parameters of the system's behavior
        system_msg = ("You are a trip advisor suggesting a vacation location to a group with varying preferences."
              "Given a list of locations, suggest exactly one potential vacation destination based on characteristics such as weather and nearby activities"
              "If a majority of suggested locations lies within the same country, only suggest destinations within that country"
              "If a majority of group suggestions describe the same destination, suggest that location"
              "The final destination suggested should be shown in the exact format **City, State/Province, Country**"
              "The overall output should be the suggested city followed by a one paragraph description of why this destination is a good choice"
        )

        #Construct a simulated user prompt from the input list
        user_msg = "Give a suggestion for a vacation destination based on the following list of user suggestions:"
        for i in destIn:
            user_msg += "\n"
            user_msg += i
        
        #Prompt the model and record the output
        resp = ollama.chat(
            model = "llama3.1:latest",
            messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
            ]
        )

        #Get the message from the response and parse the location as a string
        self.rawOutput = resp["message"]["content"]
        self.location = self.rawOutput.split("**")[1]

        #Return self.location for convenience in testing
        return {"Location":self.location, "Raw":self.rawOutput}

class AIActivities(models.Model):
    activities = []
    rawOutput = ""

    def giveSuggestion(self, destIn, actIn):
        #Define the parameters of the system's behavior
        system_msg = ("You are a trip advisor suggesting a set of activities to a group with varying preferences."
            "The group has chosen a location for travel and would like you to suggest specific activities within or near that location."
            "Be sure to suggest a specific place where each activity is to happen, such as a particular trail system if suggesting mountain biking."
            "Given a list of potential activities, suggest a list of no more than 3 activities that represents the best compromise between all suggestions."
            "If a majority of users suggest the same activity, ensure that this activity is on the final list"
            "The final activities suggested should be shown in the exact format **Activity, Location**"
            "The overall output should be in the format:\n1. Activity One\n2: Activity2\n3. Activity3\n\nEXPLAINER PARAGRAPH"
        )

        #Construct a simulated user prompt from the input list
        user_msg = f"Give a suggestion for a set of activites to do on vacation in {destIn}"
        for i in actIn:
            user_msg += "\n"
            user_msg += i

        #Prompt the model and record the output
        resp = ollama.chat(
            model = "llama3.1:latest",
            messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
            ]
        )

        #Get the message from the response and parse the location as an array of strings
        self.rawOutput = resp["message"]["content"]
        activities = []
        entries = self.rawOutput.split("**")
        for i, con in enumerate(entries):
            if i==1 or i==3 or i==5:
                activities.append(con)

        #Return object variables for convenience in testing
        return {"Activities":self.activities, "Raw":self.rawOutput}