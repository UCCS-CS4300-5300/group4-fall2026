#The system depends on the ollama app and the llama 3.1 model being installed
#Ollama can be installed at https://ollama.com/download/windows
#The model can be downloaded via command prompt with the command "ollama pull llama3.1:latest" (remove the quotes when actually run)

import ollama

destIn = "Seoul, South Korea"
#Define the parameters of the system's behavior
actIn = ["Mountain Biking", "Hiking", "Art Museum", "Art Gallery"]
#for i in range(0,10):
    #destIn.append("Seoul, South Korea")
print(f"Total suggestions: {len(actIn)}")

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

#Get the message from the response and parse the location as an array
text = resp["message"]["content"]
activities = []
entries = text.split("**")
for i, con in enumerate(entries):
    if i==1 or i==3 or i==5:
        activities.append(con)
#text.split("**")[1].split(",")
#for i, value in enumerate(activities):
    #activities[i] = activities[i].strip()

print(text)
print(activities)
