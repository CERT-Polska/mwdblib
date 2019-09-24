import base64
import json
import warnings
import time

from .exc import InvalidCredentialsError, NotAuthenticatedError, LimitExceededError, map_http_error

try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin

import requests

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

API_URL = "https://mwdb.cert.pl/api/"


class MalwarecageAPI(object):
    def __init__(
        self,
        api_url=API_URL,
        api_key=None,
        verify_ssl=True,
        obey_ratelimiter=True
    ):
        """ API object used to talk with a malwarecage instance directly.

        :param api_url: Malwarecage instance URL. Should end with a slash.
        :param api_key: Optional API key.
        :param verify_ssl: Should the api verify SSL certificate correctness?
        :param obey_ratelimiter: If false, HTTP 429 errors will cause an
        exception like all other error codes. If true (default), library will
        transparently handle them by sleeping for a specified duration.
        """
        self.api_url = api_url
        if not self.api_url.endswith("/"):
            self.api_url += "/"
            warnings.warn("MalwarecageAPI.api_url should end with a trailing slash. "
                          "Fix your configuration. Missing character was added to the URL.")
        self.api_key = None
        self.logged_user = None
        self.session = requests.Session()

        from . import __version__
        self.session.headers['User-Agent'] = "mwdblib/{} ".format(__version__) + self.session.headers['User-Agent']

        self.set_api_key(api_key)

        self.username = None
        self.password = None
        self.verify_ssl = verify_ssl
        self.obey_ratelimiter = obey_ratelimiter

    def set_api_key(self, api_key):
        self.api_key = api_key
        if self.api_key is not None:
            try:
                self.logged_user = json.loads(base64.b64decode(self.api_key.split(".")[1] + "=="))["login"]
            except Exception:
                raise InvalidCredentialsError("Invalid API key format. Verify whether actual token is provided "
                                              "instead of its UUID.")
            self.session.headers.update({'Authorization': 'Bearer {}'.format(self.api_key)})

    def login(self, username, password, warn=True):
        if warn:
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

    def logout(self):
        self.api_key = None

    def perform_request(self, method, url, *args, **kwargs):
        try:
            response = self.session.request(method, url, *args, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as http_error:
            mapped_error = map_http_error(http_error)
            if mapped_error is None:
                raise
            raise mapped_error

    def request(self, method, url, noauth=False, raw=False, *args, **kwargs):
        # Check if authenticated yet
        if not noauth and self.api_key is None:
            raise NotAuthenticatedError(
                'API credentials for MWDB2 were not set, call MalwarecageAPI.set_api_key or '
                'Malwarecage.login first'
            )

        # Set method name and request URL
        url = urljoin(self.api_url, url)
        # Set default kwargs
        kwargs["verify"] = self.verify_ssl

        # If there are both 'form data' and 'json' passed - we need to pack them into multipart/form-data
        if "data" in kwargs and "json" in kwargs:
            kwargs["files"] = kwargs.get("files", {})
            kwargs["files"]["json"] = (None, json.dumps(kwargs["json"]), "application/json")
            del kwargs["json"]

        while True:
            try:
                response = self.perform_request(method, url, *args, **kwargs)
                break
            except NotAuthenticatedError:
                # Forget api_key
                self.logout()
                # If authenticated using API key: re-raise
                if self.username is None:
                    raise
                # Try to log in
                self.login(self.username, self.password)
                # Retry failed request...
            except LimitExceededError as e:
                if not self.obey_ratelimiter:
                    raise
                if 'Retry-After' not in e.http_error.response.headers:
                    # This should be exponential backoff, but we don't expect
                    # to see mwdb instances without retry-after headers anyway
                    retry_after = 60
                else:
                    retry_after = int(e.http_error.response.headers["Retry-After"])
                warnings.warn("Rate limit exceeded. Sleeping for a {} seconds.".format(retry_after))
                time.sleep(retry_after)
                # Retry failed request...
        return response.json() if not raw else response.content

    def get(self, *args, **kwargs):
        return self.request("get", *args, **kwargs)

    def post(self, *args, **kwargs):
        return self.request("post", *args, **kwargs)

    def put(self, *args, **kwargs):
        return self.request("put", *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.request("delete", *args, **kwargs)
