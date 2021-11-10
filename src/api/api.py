import base64
import datetime
import json
import warnings
import time

from urllib.parse import urljoin

import requests
from requests.exceptions import ConnectionError

from ..exc import (
    InvalidCredentialsError, NotAuthenticatedError, LimitExceededError,
    BadResponseError, GatewayError, map_http_error
)
from .options import APIClientOptions


class JWTAuthKey:
    def __init__(self, value: str) -> None:
        self.value = value
        try:
            header, payload, signature = value.split(".")
            self.header = json.loads(base64.b64decode(header))
            self.payload = json.loads(base64.b64decode(payload))
        except ValueError:
            raise InvalidCredentialsError("Invalid authentication token. Verify whether actual token is provided "
                                          "instead of its UUID.")

    @property
    def is_expired(self) -> bool:
        if "exp" not in self.header:
            # No expiration time set
            return False
        return datetime.datetime.utcnow().timestamp() >= self.header["exp"]

    @property
    def username(self) -> str:
        return self.payload["login"]


class APIClient:
    """
    Client for MWDB REST API that performs authentication and low-level API request/response handling
    """
    def __init__(self, _auth_key=None, **api_options):
        self.options = APIClientOptions(**api_options)
        self._server_metadata = {}

        self.api_url = self.options.api_url
        if not self.api_url.endswith("/"):
            self.api_url += "/"
        if not self.api_url.endswith("/api/") and self.options.emit_warnings:
            warnings.warn("APIClient.api_url doesn't end with '/api/'. Make sure you have passed"
                          "URL to the REST API instead of MWDB UI")

        self.session = requests.Session()

        from .. import __version__
        self.session.headers['User-Agent'] = "mwdblib/{} ".format(__version__) + self.session.headers['User-Agent']

        if _auth_key:
            self.set_auth_key(_auth_key)
        if self.options.api_key:
            self.set_api_key(self.options.api_key)
        elif self.options.username and self.options.password:
            self.login(self.options.username, self.options.password)

    @property
    def server_metadata(self):
        if self._server_metadata is None:
            self._server_metadata = self.get("server")
        return self._server_metadata

    @property
    def server_version(self):
        return self.server_metadata["server_version"]

    @property
    def logged_user(self):
        return self.auth_key and self.auth_key.username

    def set_auth_key(self, auth_key):
        self.auth_key = JWTAuthKey(auth_key)
        self.session.headers.update({'Authorization': f'Bearer {self.auth_key}'})

    def login(self, username, password):
        auth_key = self.post("auth/login", json={
            "login": username,
            "password": password
        }, noauth=True)["token"]
        self.set_auth_key(auth_key)
        # Store credentials in API options
        self.options.username = username
        self.options.password = password

    def set_api_key(self, api_key):
        self.set_auth_key(api_key)
        # Store credentials in API options
        self.options.api_key = api_key

    def logout(self):
        self.auth_key = None
        self.session.headers.pop("Authorization")

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
        # Check if authenticated
        if not noauth and self.auth_key is None:
            raise NotAuthenticatedError(
                'API credentials for MWDB were not set, pass api_key parameter '
                'to MWDB or call MWDB.login first'
            )

        # Set method name and request URL
        url = urljoin(self.api_url, url)
        # Pass verify_ssl setting to requests kwargs
        kwargs["verify"] = self.options.verify_ssl

        downtime_retries = self.options.max_downtime_retries
        downtime_timeout = self.options.downtime_timeout
        retry_on_downtime = self.options.retry_on_downtime
        retry_idempotent = self.options.retry_idempotent

        while True:
            try:
                response = self.perform_request(method, url, *args, **kwargs)
                try:
                    return response.json() if not raw else response.content
                except ValueError:
                    raise BadResponseError(
                        "Can't decode JSON response from server. "
                        "Probably APIClient.api_url points to the MWDB web app instead of MWDB REST API."
                    )
            except NotAuthenticatedError:
                # Forget current auth_key
                self.logout()
                # If no password set: re-raise
                if self.options.password is None:
                    raise
                # Try to log in
                self.login(self.options.username, self.options.password)
                # Retry failed request...
            except LimitExceededError as e:
                if not self.options.obey_ratelimiter:
                    raise
                if 'Retry-After' not in e.http_error.response.headers:
                    # This should be exponential backoff, but we don't expect
                    # to see mwdb instances without retry-after headers anyway
                    retry_after = 60
                else:
                    retry_after = int(e.http_error.response.headers["Retry-After"])
                if self.options.emit_warnings:
                    warnings.warn(f"Rate limit exceeded. Sleeping for a {retry_after} seconds.")
                time.sleep(retry_after)
                # Retry failed request...
            except (ConnectionError, GatewayError):
                if not retry_on_downtime or downtime_retries == 0 or \
                        (not retry_idempotent and method == "post"):
                    raise
                downtime_retries -= 1
                if self.options.emit_warnings:
                    warnings.warn('Retrying request due to connectivity issues. '
                                  'Sleeping for {} seconds.'.format(downtime_timeout))
                time.sleep(downtime_timeout)
                # Retry failed request...

    def get(self, *args, **kwargs):
        return self.request("get", *args, **kwargs)

    def post(self, *args, **kwargs):
        return self.request("post", *args, **kwargs)

    def put(self, *args, **kwargs):
        return self.request("put", *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.request("delete", *args, **kwargs)
