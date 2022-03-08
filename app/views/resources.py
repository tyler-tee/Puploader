"""
View responsible for resource generation (Charities, Orgs, etc.)
"""
import json
import os
from flask import (Blueprint, redirect,
                   render_template, request, session,
                   url_for)
from charitynav_api.charitynav_api import CharityNav_API
from petfinder_api.petfinder_api import PetFinder

resources = Blueprint('resources', __name__, template_folder='templates')


@resources.route('/resources/<resource>', methods=['GET', 'POST'])
def render_resources(resource):
    """
    Route responsible for rendering pages related to animal-friendly resources.
    """
    try:
        with open('./config/config.json') as f:
            api_config = json.load(f)
    except FileNotFoundError:
        api_config = None

    if api_config:
        petfinder_key = api_config['PETFINDER_KEY']
        petfinder_sec = api_config['PETFINDER_SEC']
    else:
        petfinder_key = os.environ.get('PETFINDER_KEY')
        petfinder_sec = os.environ.get('PETFINDER_SEC')

    petfinder_api = PetFinder(petfinder_key,
                              petfinder_sec)
    petfinder_api.auth()

    location = request.form.get('inputZip')

    if resource == 'local_pups':
        pups = petfinder_api.get_animals(type='dog', location=location)

        for pup in pups:
            pup['contact']['address'] = ', '.join(i for i in pup['contact']['address'].values()
                                                  if i)
            try:
                pup['photo'] = pup['photos'][0]['medium']
            except IndexError:
                pup['photo'] = url_for('static', filename='/assets/no_photo_avail.jpg')

        return render_template('/resources/pups.html', pups=pups, auth=('username' in session))

    elif resource == 'local_orgs':
        organizations = petfinder_api.get_organizations(location=location)

        for org in organizations:
            org['address'] = ', '.join(i for i in org['address'].values() if i)
            org['hours'] = ', '.join(i for i in org['hours'].values() if i)
            try:
                org['photo'] = org['photos'][0]['medium']
            except IndexError:
                org['photo'] = ''

        return render_template('/resources/organizations.html',
                               organizations=organizations,
                               auth=('username' in session))

    elif resource == 'charities':
        if api_config:
            charitynav_id = api_config['CHARITY_APP_ID']
            charitynav_key = api_config['CHARITY_APP_KEY']
        else:
            charitynav_id = os.environ.get('CHARITY_APP_ID')
            charitynav_key = os.environ.get('CHARITY_APP_KEY')

        charitynav_api = CharityNav_API(charitynav_id, charitynav_key)

        charities = charitynav_api.get_organizations(category_id=1, sort='RATING:DESC')
        charities = charities[:10] if charities else None

        for charity in charities:
            charity['address'] = ', '.join(i for i in charity['mailingAddress'].values() if i)

        return render_template('/resources/charities.html', charities=charities)

    return redirect('/')
