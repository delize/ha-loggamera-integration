import requests

class LoggameraAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.loggamera.com/v1"

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def get_power_data(self):
        endpoint = f"{self.base_url}/power"
        response = requests.get(endpoint, headers=self._headers())
        return self._handle_response(response)

    def get_water_data(self):
        endpoint = f"{self.base_url}/water"
        response = requests.get(endpoint, headers=self._headers())
        return self._handle_response(response)

    def get_other_data(self, data_type):
        endpoint = f"{self.base_url}/{data_type}"
        response = requests.get(endpoint, headers=self._headers())
        return self._handle_response(response)

    def _handle_response(self, response):
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()