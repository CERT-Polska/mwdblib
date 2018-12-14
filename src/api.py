try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin

import requests

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

API_URL = "https://mwdb.cert.pl/api/"


class MalwarecageAPI(object):
    def __init__(self, api_url=API_URL, api_key=None):
        self.api_url = api_url
        self.api_key = None
        self.session = requests.Session()
        self.set_api_key(api_key)

    def set_api_key(self, api_key):
        self.api_key = api_key
        self.session.headers.update({'Authorization': 'Bearer {}'.format(self.api_key)})

    def request(self, method, url, noauth=False, raw=False, *args, **kwargs):
        # Check if authenticated yet
        if not noauth and self.api_key is None:
            raise RuntimeError(
                'API credentials for MWDB2 were not set, call MalwarecageAPI.set_api_key or '
                'Malwarecage.login first'
            )

        # Set method name and request URL
        url = urljoin(self.api_url, url)
        # Set default kwargs
        kwargs["verify"] = False
        kwargs["json"] = kwargs.get("json", True)
        response = self.session.request(method, url, *args, **kwargs)
        response.raise_for_status()
        return response.json() if not raw else response.content

    def get(self, *args, **kwargs):
        return self.request("get", *args, **kwargs)

    def post(self, *args, **kwargs):
        return self.request("post", *args, **kwargs)

    def put(self, *args, **kwargs):
        return self.request("put", *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.request("delete", *args, **kwargs)
