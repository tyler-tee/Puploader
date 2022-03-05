from flask_login import UserMixin
import pymongo

client = pymongo.MongoClient('127.0.0.1', 27017)
db = client['AUTH']
users = db['USERS']


class User(UserMixin):
    def __init__(self, user_id, name, email, profile_pic):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.profile_pic = profile_pic
    
    
    def get_id(self):
        return self.user_id
    

    @staticmethod
    def get(user_id):
        user = users.find_one({'user_id': user_id})
        
        if not user:
            return None
        
        user = User(user_id=user['user_id'],
                    name=user['name'],
                    email=user['email'],
                    profile_pic=user['profile_pic'])
        
        return user
    
    
    @staticmethod
    def create(user_id, name, email, profile_pic):
        users.insert_one({'user_id': user_id,
                          'name': name,
                          'email': email,
                          'profile_pic': profile_pic})
