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

  return tag


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
    
    answerType = answer_type(question)[0]
    print(question)
    analysis = model.analyze(question)

    return {"answerType": answerType, "analyzed": json.dumps(analysis)}

if __name__ == '__main__':
    app.run()