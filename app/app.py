import os
from flask import Flask
import pymongo
from petfinder_api.petfinder_api import PetFinder


def create_app():
    app = Flask(__name__)
    
    try:
        app.config.from_pyfile('./config/development.cfg')
    except FileNotFoundError:
        app.config.from_pyfile('./config/production.cfg')
        
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') if os.os.environ.get('SECRET_KEY') else app.config['SECRET_KEY']

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.mkdir(app.config['UPLOAD_FOLDER'])
    
    mongo_uri = app.config['MONGODB_URI'] if app.config['MONGODB_URI'] else os.environ.get('MONGODB_URI')
    client = pymongo.MongoClient(mongo_uri, 27017)
    database = client['AUTH']
    users = database['USERS']
    
    if os.environ.get('PETFINDER_KEY') and os.environ.get('PETFINDER_SEC'):
        petfinder_api = PetFinder(os.environ.get('PETFINDER_KEY'),
                                  os.environ.get('PETFINDER_SEC'))
    else:
        petfinder_api = PetFinder(app.config['PETFINDER_KEY'],
                                  app.config['PETFINDER_SEC'])

    return app, users, petfinder_api
