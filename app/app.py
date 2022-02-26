from flask import Flask
import json
import os
import pymongo
from config import config


if os.environ.get('PETFINDER_KEY') and os.environ.get('PETFINDER_SEC'):
   petfinder_key, petfinder_sec = os.environ.get('PETFINDER_KEY'), os.environ.get('PETFINDER_SEC')
else:
   try:
      with open('petfinder_config.json') as f:
         config = json.load(f)
         key, sec = config['petfinder_key'], config['petfinder_sec']
   except Exception as e:
      print(e)


app = Flask(__name__)

# Configure and create the upload folder if necessary
app.config['UPLOAD_FOLDER'] = config['upload_folder']
if not os.path.exists(app.config['UPLOAD_FOLDER']):
   os.mkdir(app.config['UPLOAD_FOLDER'])

app.secret_key = "secret key"
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

mongodb_uri = os.getenv('MONGODB_URI') if os.get_env('MONGODB_URI') else 'localhost'
client = pymongo.MongoClient(mongodb_uri, 27017)
database = client['AUTH']
users = database['USERS']
