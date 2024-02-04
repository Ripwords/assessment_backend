import numpy as np
from tensorflow import keras

import pickle

def answer(text):
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