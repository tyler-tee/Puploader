import requests
from typing import List


class CharityNav_API:
    """
    Wrapper for CharityNavigator's REST API.
    """

    def __init__(self, app_id: str, app_key: str):
        """
        Constructor for CharityNav's wrapper.
        """
        self.app_id = app_id
        self.app_key = app_key
        self.base_url = "https://api.data.charitynavigator.org/v2"

        self.client = requests.session()

    def get_organizations(self, category_id: int, **kwargs) -> List:
        """
        Retrieve organizations based on category and any other supplied args.
        """
        params = {
                "app_id": self.app_id,
                "app_key": self.app_key,
                "categoryID": category_id
                }
        params.update(**kwargs)

        orgs = self.client.get(f"{self.base_url}/organizations", params=params)

        if orgs.status_code == 200:
            return orgs.json()

        print(orgs.status_code, orgs.headers, orgs.text)
