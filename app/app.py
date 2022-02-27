import os
from flask import Flask
import pymongo


def create_app():
    app = Flask(__name__)
    
    app.config.from_pyfile('./config/production.cfg')
    
    try:
        app.config.from_pyfile('./config/development.cfg')
    except FileNotFoundError:
        pass
    
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.mkdir(app.config['UPLOAD_FOLDER'])
    
    client = pymongo.MongoClient(app.config['MONGODB_URI'], 27017)
    database = client['AUTH']
    users = database['USERS']

    return app, users
