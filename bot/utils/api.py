import requests
from bot.config import API_TOKEN

class APIClient:
    def __init__(self, base_url="https://api.example.com"):
        self.base_url = base_url
        self.headers = {"api-token": API_TOKEN}

    def _get(self, endpoint, params=None):
        try:
            response = requests.get(f"{self.base_url}/{endpoint}", headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            return None

    def get_categories_and_products(self):
        return self._get("categories")

    def new_order(self, order_data):
        return self._get("new_order", params=order_data)

    def check_orders(self, user_id):
        return self._get("orders", params={"user_id": user_id})
