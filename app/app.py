"""
Puploader's app factory. Primarily called from run.py in order to execute the application.
"""
import os
from flask import Flask
import pymongo
from views.auth import auth
from views.photos import photos
from views.resources import resources


def create_app():
    """App factory - Returns base application configured based on ./cfg file.

    Returns:
        Base application, petfinder_api instance, and MongoDB connection.
    """
    app = Flask(__name__)

    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(photos, url_prefix='/')
    app.register_blueprint(resources, url_prefix='/')

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

    return app, users
