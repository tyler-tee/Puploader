import os
from flask_login import UserMixin
import pymongo

# mongo_uri = os.environ.get('MONGODB_URI')
mongo_uri = 'mongodb+srv://puploader:LEXYNl4wudDCT3ID@puploaderprod.dv1xfp9.mongodb.net/?retryWrites=true&w=majority&ssl=true'
client = pymongo.MongoClient(mongo_uri, 27017)
db = client['AUTH']
users = db['USERS']


class User(UserMixin):
    """_Using Flask-Login's UserMixin to create a subclass suitable for our purposes.

    Args:
        UserMixin (_type_): _Flask-Login's base UserMixin.
    """

    def __init__(self, user_id, name, email, profile_pic):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.profile_pic = profile_pic


    def get_id(self):
        return self.user_id


    @staticmethod
    def get(user_id):
        """ Retrieve the user based on their ID.

        Args:
            user_id (str): "user_id" - Unique string created upon user creation.

        Returns:
            _user (_type_): Returns None if user not found, else returns the info for that user.
        """
        user = users.find_one({'user_id': user_id})

        if not user:
            return None

        user = User(user_id=user['user_id'],
                    name=user['name'],
                    email=user['email'],
                    profile_pic=user['profile_pic'])

        return user


    @staticmethod
    def create(user_id: str, name: str, email: str, profile_pic: str) -> bool:
        """ Create a new collection in our DB based on provided arguments.

        Args:
            user_id (str): User ID obtained from Google auth.
            name (str): User's name obtaind from Google auth.
            email (str): User's email obtaind from Google auth.
            profile_pic (str): User's profile pic obtained from Google auth.

        Returns:
            bool: True/False based on success of collection insertion.
        """

        return users.insert_one({'user_id': user_id,
                                 'name': name,
                                 'email': email,
                                 'profile_pic': profile_pic})
