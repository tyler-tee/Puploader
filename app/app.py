from flask import Flask
import os
import pymongo
from config import config


app = Flask(__name__)

# Configure and create the upload folder if necessary
app.config['UPLOAD_FOLDER'] = config['upload_folder']
if not os.path.exists(app.config['UPLOAD_FOLDER']):
   os.mkdir(app.config['UPLOAD_FOLDER'])

app.secret_key = "secret key"
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

client = pymongo.MongoClient("localhost", 27017)
if not 'AUTH' in client.list_database_names():
   database = client['AUTH']

users = database['USERS']
