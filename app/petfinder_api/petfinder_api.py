import json
import os
import requests
        

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
