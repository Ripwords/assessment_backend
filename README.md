# Getting Started

## Installation

Clone the repository

Install the required packages using the following command:

```bash
pip install -r requirements.txt
```

## Create a .env file

The .env file should contain your geocoding API Key from Google, and an API Key for the python server.

To apply for the geocoding API Key from Google, visit the following link: [Google Geocoding Services](https://developers.google.com/maps/documentation/javascript/geocoding#GetStarted)

```bash
GEOCODE_API_KEY=your_geocoding_api_key
MY_SECRET=your_secret
```

## Run scapper.py

Running the scrapper will create a file called `data.json` which will contain the data from the Subway website.

```bash
python scrapper.py
```

## Run the ML_model.py

Running the ML_model will create 1 folder which contains the model and 2 pickle files which are the vectorizer and the label encoder.

This model will be used to run the query from the chatbot.

WARNING: THIS IS NOT RUNNING IN PRODUCTION.
This is because, the backend hosting is using pythonanywhere which only has 512MB of storage, which is not enough to install all the packages and store the files needed to run the model.

```bash
python ML_model.py
```

## Run the server

The server will take some time to load all the models and the data during boot up.

After the models are loaded, the server will be running and listening to requests.

```bash
python server.py
```
