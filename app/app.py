import os
from flask import Flask
import pymongo
from petfinder_api.petfinder_api import PetFinder


def create_app():
    """_App factory - Returns base application configured based on ./cfg file.

    Returns:
        Base application, petfinder_api instance, and MongoDB connection.
    """
    app = Flask(__name__)

    try:
        app.config.from_pyfile('./config/development.cfg')
    except FileNotFoundError:
        app.config.from_pyfile('./config/production.cfg')

    if os.environ.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.mkdir(app.config['UPLOAD_FOLDER'])

    if app.config['MONGODB_URI']:
        mongo_uri = app.config['MONGODB_URI']
    else:
        mongo_uri = os.environ.get('MONGODB_URI')

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
