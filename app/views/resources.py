"""
View responsible for resource generation (Charities, Orgs, etc.)
"""
import json
import os
from flask import (Blueprint, redirect, render_template, request, session, url_for)
from charitynav_api.charitynav_api import CharityNavAPI
from petfinder_api.petfinder_api import PetFinder

resources = Blueprint('resources', __name__, template_folder='templates')


def load_api_config():
    """Load API configuration from a JSON file or environment variables."""
    try:
        with open('./config/config.json') as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def get_petfinder_api():
    """Initialize and authenticate the PetFinder API client."""
    config = load_api_config()
    petfinder_key = config['PETFINDER_KEY'] if config else os.environ.get('PETFINDER_KEY')
    petfinder_sec = config['PETFINDER_SEC'] if config else os.environ.get('PETFINDER_SEC')

    petfinder_api = PetFinder(petfinder_key, petfinder_sec)
    petfinder_api.auth()
    return petfinder_api


def process_pets(pets):
    """Process pet data to include address and photo fallback."""
    for pet in pets:
        pet['contact']['address'] = ', '.join(filter(None, pet['contact']['address'].values()))
        pet['photo'] = pet['photos'][0]['medium'] if pet.get('photos') else url_for('static', filename='assets/no_photo_avail.jpg')
    return pets


def process_organizations(orgs):
    """Process organization data to include address, hours, and photo fallback."""
    for org in orgs:
        org['address'] = ', '.join(filter(None, org['address'].values()))
        org['hours'] = ', '.join(filter(None, org['hours'].values()))
        org['photo'] = org['photos'][0]['medium'] if org.get('photos') else ''
    return orgs


def get_charitynav_api():
    """Initialize the Charity Navigator API client."""
    config = load_api_config()
    charitynav_id = config['CHARITY_APP_ID'] if config else os.environ.get('CHARITY_APP_ID')
    charitynav_key = config['CHARITY_APP_KEY'] if config else os.environ.get('CHARITY_APP_KEY')
    return CharityNavAPI(charitynav_id, charitynav_key)


def process_charities(charities):
    """Process charity data to include address formatting."""
    for charity in charities:
        charity['address'] = ', '.join(filter(None, charity['mailingAddress'].values()))
    return charities


@resources.route('/resources/<resource>', methods=['GET', 'POST'])
def render_resources(resource):
    """
    Route responsible for rendering pages related to animal-friendly resources.
    """
    location = request.form.get('inputZip')
    petfinder_api = get_petfinder_api()

    if resource == 'local_pups':
        pets = petfinder_api.get_animals(type='dog', location=location)
        processed_pets = process_pets(pets)
        return render_template('/resources/pups.html', pups=processed_pets, auth=('username' in session))

    elif resource == 'local_orgs':
        organizations = petfinder_api.get_organizations(location=location)
        processed_orgs = process_organizations(organizations)
        return render_template('/resources/organizations.html', organizations=processed_orgs, auth=('username' in session))

    elif resource == 'charities':
        charitynav_api = get_charitynav_api()
        charities = charitynav_api.get_organizations(category_id=1, sort='RATING:DESC')[:10]
        processed_charities = process_charities(charities)
        return render_template('/resources/charities.html', charities=processed_charities)

    return redirect('/')
