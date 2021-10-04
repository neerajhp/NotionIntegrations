import requests
import json
import os
from dotenv import load_dotenv
from re import match


DEBUG = True


# Load environment variables
load_dotenv()

#ANKI server properties
ankiServerURL = "http://127.0.0.1:8765/"
DECK = "CS"

#Connect to Notion
# API Endpoints and variables
secret = os.getenv("NOTION_SECRET")
baseNotionURL = "https://api.notion.com/v1/blocks/"
data = {}
header = {"Authorization":secret, "Notion-Version":"2021-05-13", "Content-Type": "application/json"}

#Get Pages
javaFundamentalsPage = os.getenv("JAVA_FUNDAMENTALS_ID")


#************** HELPERS **************# 

def stringFormatter(contentArray):
    """Transform Notion rich text into html for ANKI"""
    string = ""
    for content in contentArray:
        if content["annotations"]["bold"]:
            string += "<b>" + content["plain_text"] + "</b>"
        elif content["annotations"]["italic"]:
            string += "<i>" + content["plain_text"] + "</i>"
        elif content["annotations"]["code"]:
            string += "<code>" + content["plain_text"] + "</code>"
        else: 
            string += content["plain_text"]
        
    return string


def createPayload(question, answer):
    """ Convert Notion data to  ANKI JSON payload. Only body is formatted. String formatting is handled by the stringFormatter function. """
    payload = {
    "action": "addNote",
    "version": 6,
    "params": {
        "note": {
            "deckName": "Default",
            "modelName": "Basic",
            "fields": {
                "Front": "",
                "Back": ""
            },
            "options": {
                "allowDuplicate": False,
                "duplicateScope": "deck",
                "duplicateScopeOptions": {
                    "deckName": "Default",
                    "checkChildren": False,
                    "checkAllModels": False
                }
            },
            "tags": [
                "JavaFundamentals"
            ],}
    }
    }
    body = ""
    cardFront = payload["params"]["note"]["fields"]["Front"]
    cardBack = payload["params"]["note"]["fields"]["Back"]

    #Update Question
    payload["params"]["note"]["fields"]["Front"] = stringFormatter(question)
   

    for content in answer:
        if content["type"] == "paragraph":
            body += stringFormatter(content["paragraph"]["text"])
        elif content["type"] == "bulleted_list_item":
            #Format bulleted List
            body += "<ul><li>" + stringFormatter(content["bulleted_list_item"]["text"]) + "</li></ul>"
       
        elif content["type"] == "image":
            # Image URL 
            payload["picture"] = [{"url": content["image"]["file"]["url"], "filename": content["image"]["caption"][0]["text"]["content"] + '.png' ,"fields":  ["Back"]}]
            
        # Add break in body
        body += '\n'

    # Add to payload
    payload["params"]["note"]["fields"]["Back"] += body  + '\n'

    return payload

def createCard(payload):
    """ ANKI api request to add card to deck """
    response = requests.post(ankiServerURL, json=payload).json()
    if len(response) != 2:
        print('response has an unexpected number of fields')
    if 'error' not in response:
        print('response is missing required error field')
    if 'result' not in response:
        print('response is missing required result field')
    if response['error'] is not None:
        print(response['error'])
    return response['result']

#************** Main **************#

if DEBUG:
    f = open("AnkiBots/output.txt", "w")


# Open Anki
os.system("open /Applications/Anki.app")

# Get notion Page
try:
    response = requests.get(baseNotionURL + javaFundamentalsPage + "/children", headers=header, data=data)
    response.raise_for_status()
except requests.exceptions.HTTPError as errh:
    print("There was an error with Notion")
    pass
except requests.exceptions.ConnectionError as errc:
    print(errc)
    pass
except requests.exceptions.Timeout as errt:
    print(errt)
    pass
except requests.exceptions.RequestException as err:
    print(err)
    pass

# Recursively get all page content
pageContent = response.json()["results"]
for block in pageContent:
    if block['has_children'] == True:
        try:
            response = requests.get(baseNotionURL + block['id'] + "/children", headers=header, data=data)
            response.raise_for_status()
            pageContent += response.json()["results"]
        except requests.exceptions.HTTPError as errh:
            print(errh)
            pass
        except requests.exceptions.ConnectionError as errc:
            print(errc)
            pass
        except requests.exceptions.Timeout as errt:
            print(errt)
            pass
        except requests.exceptions.RequestException as err:
            print(err)
            pass

# Filter toggle content 
toggleContent = [block for block in pageContent if block['type'] == 'toggle']
print("Successfully got toggles from Notion.")

#Convert toggle lists to JSON payload
for toggle in toggleContent:
    #Get toggle header (the question)
    toggleQuestion = toggle["toggle"]["text"]
    try:
        #Get toggle body (the answer)
        response = requests.get(baseNotionURL + toggle['id'] + "/children", headers=header, data=data).json()
        #Format body content into valid ANKI payload
        toggleAnswer = response["results"]
        #Create ANKI Payload
        newCard = createPayload(toggleQuestion, toggleAnswer)
        #Post to ANKI server
        createCard(newCard)
        if DEBUG:
            f.write(newCard["params"]["note"]["fields"]["Front"] + "\n" + newCard["params"]["note"]["fields"]["Back"])
            json.dump(newCard, f)
            f.write("\n\n")
           
    except requests.exceptions.HTTPError as errh:
            print(errh)
            pass
    except requests.exceptions.ConnectionError as errc:
            print(errc)
            pass
    except requests.exceptions.Timeout as errt:
            print(errt)
            pass
    except requests.exceptions.RequestException as err:
            print(err)
            pass

print("\nAll Done!\n")

if DEBUG:
    f.close()
# # Close Anki
# os.system("pkill Anki")
