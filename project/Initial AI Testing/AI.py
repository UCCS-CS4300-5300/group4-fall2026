#The system depends on the ollama app and the llama 3.1 model being installed
#Ollama can be installed at https://ollama.com/download/windows
#The model can be downloaded via command prompt with the command "ollama pull llama3.1:latest" (remove the quotes when actually run)

import ollama

#Define the parameters of the system's behavior
destIn = ["Tampa, Florida, USA", "Colorado Springs, Colorado, USA", "San Diego, California, USA", "Cambridge, Massachusetts, USA", "Toronto, Ontario, Canada", "Seoul, South Korea"]
#for i in range(0,10):
    #destIn.append("Seoul, South Korea")
print(f"Total suggestions: {len(destIn)}")

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

#Get the message from the response and parse the location as an array
text = resp["message"]["content"]
location = text.split("**")[1].split(",")
for i, value in enumerate(location):
    location[i] = location[i].strip()

print(text)
print(location)
