import base64
import json
import warnings

try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin

import requests

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

API_URL = "https://mwdb.cert.pl/api/"


class MalwarecageAPI(object):
    def __init__(self, api_url=API_URL, api_key=None, verify_ssl=False):
        self.api_url = api_url
        self.api_key = None
        self.session = requests.Session()
        self.set_api_key(api_key)
        self.username = None
        self.password = None
        self.verify_ssl = verify_ssl

    def set_api_key(self, api_key):
        self.api_key = api_key
        self.session.headers.update({'Authorization': 'Bearer {}'.format(self.api_key)})

    def login(self, username, password):
        warnings.warn("Password-authenticated sessions are short lived, so password needs to be stored "
                      "in MalwarecageAPI object. Ask Malwarecage instance administrator for an API key "
                      "(send e-mail to info@cert.pl if you use mwdb.cert.pl)")
        result = self.post("auth/login", json={
            "login": username,
            "password": password
        }, noauth=True)
        self.username = username
        self.password = password
        self.set_api_key(result["token"])

    def logged_user(self):
        if self.api_key is None:
            return None
        return json.loads(base64.b64decode(self.api_key.split(".")[1]+"=="))["login"]

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
        kwargs["verify"] = self.verify_ssl

        # If there are both 'form data' and 'json' passed - we need to pack them into multipart/form-data
        if "data" in kwargs and "json" in kwargs:
            files = kwargs.get("files", {})
            files["json"] = (None, json.dumps(kwargs["json"]), "application/json")
            del kwargs["json"]

        def try_request():
            response = self.session.request(method, url, *args, **kwargs)
            response.raise_for_status()
            return response

        try:
            response = try_request()
        except requests.HTTPError as e:
            # If not unauthorized: re-raise
            if e.response.status_code != requests.codes.unauthorized:
                raise
            # Forget api_key
            self.api_key = None
            # If authenticated using api_key: re-raise
            if self.username is None:
                raise
            # Try to log in
            self.login(self.username, self.password)
            # Repeat failed request
            response = try_request()

        return response.json() if not raw else response.content

    def get(self, *args, **kwargs):
        return self.request("get", *args, **kwargs)

    def post(self, *args, **kwargs):
        return self.request("post", *args, **kwargs)

    def put(self, *args, **kwargs):
        return self.request("put", *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.request("delete", *args, **kwargs)
