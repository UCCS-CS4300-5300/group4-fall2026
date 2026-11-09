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
targetBudget = 1500

system_msg = ("You are a trip advisor justifying the budget for a proposed trip"
            "You have chosen a location for travel and a list of activities nearby"
            "You should calculate the total cost of travel to the location, a hotel stay at that location, and the activities happening at that location"
            "All costs presented to the user should be shown in USD"
            "Your job is to explain why the total cost of the trip is justified and explain how it falls into the given budget"
            "The final trip cost should be shown in the exact format **$COST**"
            "You should respond to user requests in the format **TOTAL TRIP COST** followed by one explainer paragraph"
        )

user_msg = f"Explain how our trip to {destIn} where we will be "
for i, con in enumerate(actIn):
    user_msg += con
    if i <= (len(actIn)-2):
        user_msg += ", "
    if i == (len(actIn)-2):
        user_msg += "and "
user_msg += f"falls into our proposed budget of {targetBudget}."

#Prompt the model and record the output
resp = ollama.chat(
    model = "llama3.1:latest",
    messages=[
    {"role": "system", "content": system_msg},
    {"role": "user", "content": user_msg},
    ]
)

rawBudget = resp["message"]["content"]
budget = rawBudget.split("**")[1].replace(",","").replace("$", "").replace(":", "").strip("TOTAL TRIP COST").strip()

print(rawBudget)
print(budget)
