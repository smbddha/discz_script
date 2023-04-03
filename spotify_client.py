import requests

BASE_URL="https://api.spotify.com/v1"
ACCOUNTS_URL="https://accounts.spotify.com/api"

class SpotifyClient:
    def __init__(self, client_id, client_secret) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None
        self._connect()

    def _connect(self) -> None:
        """
        curl -X POST "https://accounts.spotify.com/api/token" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "grant_type=client_credentials&client_id=your-client-id&client_secret=your-client-secret"

        returns (valid for 1 hour):
        {
        "access_token": "BQDBKJ5eo5jxbtpWjVOj7ryS84khybFpP_lTqzV7uV-T_m0cTfwvdn5BnBSKPxKgEb11",
        "token_type": "Bearer",
        "expires_in": 3600
        }

        """
        # pass
        headers = {
            'Content-Type': "application/x-www-form-urlencoded"
        }
        data = {
            'grant_type': "client_credentials",
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        res = requests.post(f'{ACCOUNTS_URL}/token',
                            headers=headers,
                            data=data)

        print(res)
        print(res.json())

        self.token = res.json()['access_token'];
        # self.token = res

    def _call_api(self, route, params=None):
        url  = f'{BASE_URL}{route}'
        headers = {
            'Authorization': f'Bearer {self.token}'
        }

        print(url, headers)
        res = requests.get(url, headers=headers, params=params)

        # handle the bad status codes
        return res

    def search(self):
        res = self._call_api('/search')

        return res


    def artist(self, artist_id: str):
        res = self._call_api(f'/artists/{artist_id}')

        return res


    def artist_related_artist(self, artist_id: str):
        res = self._call_api(f'/artists/{artist_id}/related-artists')

        return res
