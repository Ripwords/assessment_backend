import math
import malaya
import json
import numpy as np
import pickle
from tensorflow import keras
from flask import Flask, request

# Load the secret from .env file
from os import getenv, path
from dotenv import load_dotenv
load_dotenv(path.join(path.dirname(__file__), '.env'))

SECRET = getenv("MY_SECRET")

# Load the database
json_file_path = path.join(path.dirname(__file__), 'data.json')
with open(json_file_path, 'r') as json_file:
    database = json.load(json_file)

# AI model
model = malaya.entity.transformer_ontonotes5(model="albert")
    
def answer_type(text):
  model = keras.models.load_model('chat_model')

  # load tokenizer object
  with open('tokenizer.pickle', 'rb') as handle:
      tokenizer = pickle.load(handle)

  # load label encoder object
  with open('label_encoder.pickle', 'rb') as enc:
      lbl_encoder = pickle.load(enc)

  result = model.predict(keras.preprocessing.sequence.pad_sequences(tokenizer.texts_to_sequences([text]), truncating='post', maxlen=20))
  tag = lbl_encoder.inverse_transform([np.argmax(result)])

  return tag[0]


app = Flask(__name__)

@app.route('/get-subway-locations')
def getSubwayLocations():
    # Check if header: {Authentication: MY_SECRET} is provided
    if request.headers.get('Authorization') != SECRET:
        return {"error": "Unauthorized"}, 401
    return database

@app.route('/get-catchment-area')
def getCatrchmentArea():
    # Check if header: {Authentication: MY_SECRET} is provided
    if request.headers.get('Authorization') != SECRET:
        return {"error": "Unauthorized"}, 401
    # Get the distance from query
    distance = request.args.get('distance')
    # Return error if distance is not provided or if it is not an integer
    if not distance:
        return {"error": "Please provide a distance"}, 400
    if not distance.isdigit():
        return {"error": "Distance must be an integer"}, 400
    
    # Get store name from query
    store_name = request.args.get('store_name')
    # Return error if store name is not provided
    if not store_name:
        return {"error": "Please provide a store name"}, 400
    # Return error if store name is not in the database
    if not any(location["name"] == store_name for location in database):
        return {"error": "Store name not found"}, 400
    
    # For each location in the database, generate the catchment area of 5km
    # If any other location is within the catchment area, add it to the list
    # Return a list of dictionaries containing the location and the list of locations within the catchment area
    def coord_to_km(lat1: float, lon1: float, lat2: float, lon2: float):
      R = 6378

      dLat = math.radians(lat2 - lat1)
      dLon = math.radians(lon2 - lon1)
      lat1 = math.radians(lat1)
      lat2 = math.radians(lat2)

      a = math.sin(dLat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dLon/2)**2
      c = 2*math.asin(math.sqrt(a))

      return R * c
    
    location = next((location for location in database if location["name"] == store_name), None)
    if not location:
        return {"error": "Store name not found"}, 400
    
    if (not location["info"]["coordinates"]):
        return {"error": "No coordinates found for the store"}, 400
    
    lat1 = location["info"]["coordinates"]["lat"]
    lng1 = location["info"]["coordinates"]["lng"]
    locations_within_catchment_area = []
    for other_location in database:
        if other_location["name"] == store_name:
            continue
        if (not other_location["info"]["coordinates"]):
            continue
        lat2 = other_location["info"]["coordinates"]["lat"]
        lng2 = other_location["info"]["coordinates"]["lng"]
        if coord_to_km(lat1, lng1, lat2, lng2) <= int(distance):
            locations_within_catchment_area.append(other_location["name"])
    catchment_area = {store_name: locations_within_catchment_area}
    return {"catchment_area": catchment_area}

@app.route('/ask')
def ask():
    print(request)
    # Check if header: {Authentication: MY_SECRET} is provided
    if request.headers.get('Authorization') != SECRET:
        return {"error": "Unauthorized"}, 401
    # Get the question from query
    question = str(request.args.get('question'))
    # Return error if question is not provided
    if not question:
        return {"error": "Please provide a question"}, 400
    
    location = str(request.args.get('location'))
    # Get data from this location in the database
    location_data = next((location for location in database if location["name"] == location), None)
    
    answerType = answer_type(question)
    analysis = model.analyze(question)

    if (answerType == 'count_stores'):
        for i in analysis:
            if (i['type'] == 'GPE'):
                # Go through the database and count the number of stores with the location in the address
                count = 0
                for location in database:
                    if i['text'][0] in location["info"]["address"]:
                        count += 1
                    elif i['text'][0] == 'KL':
                        if 'Kuala Lumpur' in location["info"]["address"]:
                            count += 1
                print(count)
                return {'response': f"There are {count} store{'s' if count > 1 else ''} in {' '.join(i['text'])}."}

    elif (answerType == 'operating_earliest'):
        # Go through the database and find the operating hours of the store
        earliest = 0
        earliest_location = ''
        for location in database:
        #    Find the earliest opening time by finding the smallest number of the first encountered number, some are 24hr format 0800, ignore the first number if it is 0
            if location["info"]["operating_hours"]:
                operating_hours = location["info"]["operating_hours"]
                for time in operating_hours:
                    timeSplit = time.split(":")
                    # extract the numbers from the first element of the split
                    processTimeSplit = "".join([s for s in timeSplit[0] if s.isdigit()])
                    timeSplitNum = int(processTimeSplit) if processTimeSplit != "" else 0
                    if (timeSplitNum < earliest or earliest == 0) and timeSplitNum != 0:
                        earliest = timeSplitNum
                        earliest_location = location["name"]
        return {'response': f"The earliest operating hour for {earliest_location} is {earliest}."}
    
    elif (answerType == 'operating_latest'):
        latest = 0
        latest_location = ''
        for location in database:
            if location["info"]["operating_hours"]:
                operating_hours = location["info"]["operating_hours"]
                # time maybe be in 2230 or 11:30PM format, find the latest time
                # convert to 24hr format by checking if it is PM
                if "PM" in operating_hours[-1]:
                    processTimeSplit = "".join([s for s in operating_hours[-1] if s.isdigit()])
                    timeSplitNum = int(processTimeSplit) + 1200 if processTimeSplit != "" else 0
                elif "AM" not in operating_hours[-1] and "PM" not in operating_hours[-1]:
                    # if it is in 24hr format
                    processTimeSplit = "".join([s for s in operating_hours[-1] if s.isdigit()])
                    timeSplitNum = int(processTimeSplit) if processTimeSplit != "" else 0
                else:
                    continue
                    
                if timeSplitNum > latest:
                    latest = timeSplitNum
                    latest_location = location["name"]

        return {'response': f"The latest operating hour for {latest_location} is {latest}."}
            
    elif (answerType == 'others'):
        return {'response': 'I am sorry, I do not understand the question.'}

if __name__ == '__main__':
    app.run()