import json
import os
import requests

try:
    key = os.environ.get('PETFINDER_KEY')
    sec = os.environ.get('PETFINDER_SEC')
except Exception as e:
    print(e)
    try:
        with open('petfinder_config.json') as f:
            config = json.load(f)
            key, sec = config['petfinder_key'], config['petfinder_sec']
    except Exception as e:
        print(e)
        

class PetFinder:
    
    def __init__(self, api_key: str, api_sec: str):
        self.api_key = api_key
        self.api_sec = api_sec
        self.base_url = 'https://api.petfinder.com/v2'
    
        self.client = requests.session()
    
    
    def auth(self):
        data = {'grant_type': 'client_credentials',
                'client_id': self.api_key,
                'client_secret': self.api_sec}
        
        token = self.client.post(f'{self.base_url}/oauth2/token',
                                 data=data)
        
        self.client.headers = {'Authorization': f'Bearer {token}'}
        
        return token
    
    
    def get_organizations(self, **kwargs):
        organizations = self.client.get(f'{self.base_url}/organizations', params=kwargs)
        
        return organizations
