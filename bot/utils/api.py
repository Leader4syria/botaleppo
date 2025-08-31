import requests
from bot.config import API_TOKEN
import uuid

class APIClient:
    def __init__(self, base_url=None):
        self.base_url = base_url
        self.headers = {"api-token": API_TOKEN}

    def _get(self, endpoint, params=None):
        try:
            response = requests.get(f"{self.base_url}{endpoint}", headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            return None

    def get_api_content(self):
        return self._get("/client/api/content/0")

    def new_order(self, service_id, params):
        # Add a unique UUID to the order params
        params['order_uuid'] = uuid.uuid4()
        endpoint = f"/client/api/newOrder/{service_id}/params"
        return self._get(endpoint, params=params)

    def check_orders(self, user_id):
        # NOTE: The user has not provided a specific endpoint for checking orders.
        # Using a placeholder endpoint. This might need to be updated.
        return self._get("/client/api/orders", params={"user_id": user_id})
