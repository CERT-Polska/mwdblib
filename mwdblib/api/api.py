import base64
import datetime
import functools
import json
import re
import time
import warnings
from typing import TYPE_CHECKING, Any, Callable, List, Optional, Tuple, Type, cast
from urllib.parse import urljoin

import requests
from requests.exceptions import ConnectionError, HTTPError

from ..exc import (
    BadResponseError,
    EndpointNotFoundError,
    GatewayError,
    InvalidCredentialsError,
    LimitExceededError,
    NotAuthenticatedError,
    VersionMismatchError,
    map_http_error,
)
from .options import APIClientOptions

if TYPE_CHECKING:
    from .. import MWDB


class JWTAuthToken:
    def __init__(self, value: str) -> None:
        self.value: str = value
        try:
            header, payload, signature = value.split(".")
            self.header = json.loads(base64.b64decode(header + "=="))
            self.payload = json.loads(base64.b64decode(payload + "=="))
        except ValueError:
            raise InvalidCredentialsError(
                "Invalid authentication token. Verify whether actual token is provided "
                "instead of its UUID."
            )

    @property
    def is_expired(self) -> bool:
        if "exp" not in self.header:
            # No expiration time set
            return False
        return bool(datetime.datetime.utcnow().timestamp() >= self.header["exp"])

    @property
    def username(self) -> str:
        return str(self.payload["login"])


class APIClient:
    """
    Client for MWDB REST API that performs authentication and
    low-level API request/response handling.

    If you want to send arbitrary request to MWDB API, use :py:meth:`get`,
    :py:meth:`post`, :py:meth:`put` and :py:meth:`delete` methods using
    ``MWDB.api`` property.

    .. code-block:: python

        mwdb = MWDB()
        ...
        # Deletes object with given sha256
        mwdb.api.delete(f'object/{sha256}')
    """

    def __init__(self, _auth_token: Optional[str] = None, **api_options: Any) -> None:
        self.options: APIClientOptions = APIClientOptions(**api_options)
        self.auth_token: Optional[JWTAuthToken] = None
        self._server_metadata: Optional[dict] = None

        self.session: requests.Session = requests.Session()

        from ..__version__ import __version__

        self.session.headers[
            "User-Agent"
        ] = f'mwdblib/{__version__} {self.session.headers["User-Agent"]}'

        if _auth_token:
            self.set_auth_token(_auth_token)
        if self.options.api_key:
            self.set_api_key(self.options.api_key)
        elif self.options.username and self.options.password:
            self.login(self.options.username, self.options.password)

    @property
    def server_metadata(self) -> dict:
        """
        Information about MWDB Core server from ``/api/server`` endpoint.
        """
        if self._server_metadata is None:
            self._server_metadata = self.get("server", noauth=True)
        return self._server_metadata

    @property
    def server_version(self) -> str:
        """
        MWDB Core server version
        """
        return str(self.server_metadata["server_version"])

    @property
    def logged_user(self) -> Optional[str]:
        """
        Username of logged-in user or the owner of used API key.
        Returns None if no credentials are provided
        """
        return self.auth_token.username if self.auth_token else None

    def supports_version(self, required_version: str) -> bool:
        """
        Checks if server version is higher or equal than provided.

        .. versionadded:: 4.1.0
        """
        return parse_version(self.server_version) >= parse_version(required_version)

    def set_auth_token(self, auth_key: str) -> None:
        self.auth_token = JWTAuthToken(auth_key)
        self.session.headers.update(
            {"Authorization": f"Bearer {self.auth_token.value}"}
        )

    def login(self, username: str, password: str) -> None:
        """
        Performs authentication using provided credentials

        .. note:
            It's not recommended to use this method directly.
            Use :py:meth:`MWDB.login` instead.

        :param username: Account username
        :param password: Account password
        """
        token = self.post(
            "auth/login", json={"login": username, "password": password}, noauth=True
        )["token"]
        self.set_auth_token(token)
        # Store credentials in API options
        self.options.username = username
        self.options.password = password

    def set_api_key(self, api_key: str) -> None:
        """
        Sets API key to be used for authorization

        .. note:
            It's not recommended to use this method directly.
            Pass ``api_key`` argument to ``MWDB`` constructor.

        :param api_key: API key to set
        """
        self.set_auth_token(api_key)
        # Store credentials in API options
        self.options.api_key = api_key

    def logout(self) -> None:
        """
        Removes authorization token from APIClient instance
        """
        self.auth_token = None
        self.session.headers.pop("Authorization")

    def perform_request(
        self, method: str, url: str, *args: Any, **kwargs: Any
    ) -> requests.models.Response:
        try:
            response = self.session.request(method, url, *args, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as http_error:
            mapped_error = map_http_error(http_error)
            if mapped_error is None:
                raise
            raise mapped_error

    def request(
        self,
        method: str,
        url: str,
        noauth: bool = False,
        raw: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Sends request to MWDB API. This method can be used for accessing features that
        are not directly supported by mwdblib library.

        Other keyword arguments are the same as in requests library.

        .. seealso::

            Use functions specific for HTTP methods instead of passing
            ``method`` argument on your own:

            - :py:meth:`APIClient.get`
            - :py:meth:`APIClient.post`
            - :py:meth:`APIClient.put`
            - :py:meth:`APIClient.delete`

        :param method: HTTP method
        :param url: Relative url of API endpoint
        :param noauth: |
            Don't check if user is authenticated before sending request (default: False)
        :param raw: Return raw response bytes instead of parsed JSON (default: False)
        """
        # Check if authenticated
        if not noauth and self.auth_token is None:
            raise NotAuthenticatedError(
                "API credentials for MWDB were not set, pass api_key parameter "
                "to MWDB or call MWDB.login first"
            )

        # Set method name and request URL
        url = urljoin(self.options.api_url, url)
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
                        "Probably APIClient.api_url points to the MWDB web app "
                        "instead of MWDB REST API."
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
                # Assume that http_error is not Optional for LimitExceededError
                http_error: HTTPError = cast(HTTPError, e.http_error)
                if "Retry-After" not in http_error.response.headers:
                    # This should be exponential backoff, but we don't expect
                    # to see mwdb instances without retry-after headers anyway
                    retry_after = 60
                else:
                    retry_after = int(http_error.response.headers["Retry-After"])
                if self.options.emit_warnings:
                    warnings.warn(
                        f"Rate limit exceeded. Sleeping for a {retry_after} seconds."
                    )
                time.sleep(retry_after)
                # Retry failed request...
            except (ConnectionError, GatewayError):
                if (
                    not retry_on_downtime
                    or downtime_retries == 0
                    or (not retry_idempotent and method == "post")
                ):
                    raise
                downtime_retries -= 1
                if self.options.emit_warnings:
                    warnings.warn(
                        "Retrying request due to connectivity issues. "
                        f"Sleeping for {downtime_timeout} seconds."
                    )
                time.sleep(downtime_timeout)
                # Retry failed request...

    def get(self, *args: Any, **kwargs: Any) -> Any:
        return self.request("get", *args, **kwargs)

    def post(self, *args: Any, **kwargs: Any) -> Any:
        return self.request("post", *args, **kwargs)

    def put(self, *args: Any, **kwargs: Any) -> Any:
        return self.request("put", *args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> Any:
        return self.request("delete", *args, **kwargs)

    @staticmethod
    def requires(required_version: str, always_check_version: bool = False) -> Callable:
        """
        Method decorator that provides server version requirement
        and fallback to older implementation if available.

        To optimize requests sent by CLI: first method is called
        always if server version is not already available. If it
        fails with EndpointNotFoundError, server version is fetched
        and used to determine if fallback is available.

        If your method fails on something different than missing endpoint,
        you can check version always by enabling ``always_check_version``
        flag.
        """

        class VersionDependentMethod:
            def __init__(self, main_method: Callable) -> None:
                self.required_version = parse_version(required_version)
                self.main_method = main_method
                self.fallback_methods: List[Tuple[Tuple[int, ...], Callable]] = []
                functools.update_wrapper(self, main_method)

            def fallback(self, fallback_version: str) -> Callable:
                """
                Registers fallback method
                """

                def fallback_decorator(fallback_method: Callable) -> Callable:
                    self.fallback_methods = sorted(
                        self.fallback_methods
                        + [(parse_version(fallback_version), fallback_method)],
                        key=lambda e: e[0],
                        reverse=True,
                    )
                    return self

                return fallback_decorator

            def __get__(self, mwdb: "MWDB", objtype: Type) -> Callable:
                return functools.partial(self.__call__, mwdb)

            def __call__(self, mwdb: "MWDB", *args: Any, **kwargs: Any) -> Any:
                # Check server version if available
                server_version: Optional[Tuple[int, ...]]
                if mwdb.api._server_metadata is not None or always_check_version:
                    server_version = parse_version(mwdb.api.server_version)
                else:
                    server_version = None

                # If version available and matches the requirement: call main method
                if server_version is None or server_version >= self.required_version:
                    try:
                        return self.main_method(mwdb, *args, **kwargs)
                    except EndpointNotFoundError:
                        # On EndpointNotFoundError, check version requirement
                        server_version = parse_version(mwdb.api.server_version)
                        if server_version >= self.required_version:
                            # If matches the requirement: something wrong happened
                            raise

                # If not: call fallback methods
                fallback_version = self.required_version
                for fallback_version, fallback_method in self.fallback_methods:
                    if server_version >= fallback_version:
                        return fallback_method(mwdb, *args, **kwargs)
                else:
                    # If no fallback matched: raise VersionMismatchError
                    raise VersionMismatchError(
                        f"Required server version is "
                        f"'>={'.'.join(map(str, fallback_version))}' "
                        f"but '{mwdb.api.server_version}' is installed"
                    )

        return VersionDependentMethod


def parse_version(version: str) -> Tuple[int, ...]:
    """
    Parses server version into numerical tuple. Pre-release suffixes
    e.g. -rc1 are accepted but ignored.
    """
    match = re.match(
        r"^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)(?:[-.]\w+)?",
        version,
    )
    if not match:
        raise ValueError(f"Version doesn't match to pattern: {version}")
    return tuple(int(value) for value in match.groups())
