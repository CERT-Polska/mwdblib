from typing import Optional

import requests
import requests.exceptions


class MWDBError(RuntimeError):
    """
    Generic class for MWDB exceptions

    :param message: Error message
    :type message: str
    :param http_error: Original HTTP error
    :type http_error: :class:`requests.exceptions.HTTPError`
    """

    def __init__(
        self,
        message: Optional[str] = None,
        http_error: Optional[requests.exceptions.HTTPError] = None,
    ):
        self.http_error = http_error
        if message is None and http_error is not None:
            message = get_http_error_message(http_error)
        super().__init__(message)


class AuthError(MWDBError):
    """
    Authentication error, raised on HTTP 401: Unauthorized.
    """

    pass


class ValidationError(MWDBError):
    """
    Validation error, raised on HTTP 400: Bad Request.
    Check the message to find more information about this error.

    Most possible causes are:

    - Search query syntax is incorrect
    - Metakey has wrong format
    - User/group name has wrong format
    - Unexpected None's are provided as an argument
    """

    pass


class ObjectError(MWDBError):
    """
    Object error, raised when specified object cannot be accessed or uploaded.
    """

    pass


class PermissionError(MWDBError):
    """
    Permission error, raised when permissions are unsufficient (HTTP 403: Forbidden).
    """

    pass


class LimitExceededError(MWDBError):
    """
    Rate limit exceeded error.
    MWDB will try to throttle requests unless `obey_ratelimiter` flag is set.
    """


class BadResponseError(MWDBError):
    """
    Can't decode JSON response from server.
    Probably APIClient.api_url points to the MWDB web app instead of MWDB REST API.
    """

    pass


class InternalError(MWDBError):
    """
    Internal error. Something really bad occurred on the server side.
    """

    pass


class GatewayError(MWDBError):
    """
    Bad Gateway or Gateway Timeout. It is serious but usually temporary,
    can be caused by new version deploy or lack of resources.
    """


class NotAuthenticatedError(AuthError):
    """
    Authentication is required for specified request but credentials are not set.
    Use :py:meth:`MWDB.login` or set API key.
    """

    pass


class InvalidCredentialsError(AuthError):
    """
    Provided wrong password, API key has wrong format or was revoked.
    """

    pass


class UserPendingError(AuthError):
    """
    User has just been registered and is waiting for acceptance.
    """

    pass


class UserDisabledError(AuthError):
    """
    User is banned. Contact your administrator for more information.
    """

    pass


class MaintenanceUnderwayError(AuthError):
    """
    MWDB has been turned into maintenance mode. Try again later.
    """

    pass


class ObjectNotFoundError(ObjectError):
    """
    Object is not found, because it doesn't exist or you are not permitted to access it.
    """

    pass


class TypeConflictError(ObjectError):
    """
    Object you want to upload exists yet and has different type.
    Use :py:meth:`MWDB.query` to find it.

    If you don't have access (:class:`ObjectNotFoundError` is raised),
    try to upload it as config or blob.

    Double check whether the data you want to upload are meaningful
    (not an empty file or single string).
    """

    pass


class EndpointNotFoundError(MWDBError):
    """
    API endpoint was not found on the server. Possibly installed version
    of MWDB Core doesn't support required functionality and you need to
    upgrade.

    This exception is sometimes handled internally to fallback to
    backwards-compatible implementation.

    .. versionadded:: 4.0.0
    """

    pass


class VersionMismatchError(MWDBError):
    """
    Client detected that server version of MWDB Core is too old to support
    this functionality. You need to upgrade your server version to use it.

    .. versionadded:: 4.0.0
    """

    pass


def get_http_error_message(http_error: requests.exceptions.HTTPError) -> str:
    import json

    try:
        data = http_error.response.json()
        if "message" in data:
            return str(data["message"])
        if "errors" in data:
            return json.dumps(data["errors"])
    except ValueError:
        pass
    return str(http_error.args[0])


def map_http_error(http_error: requests.exceptions.HTTPError) -> MWDBError:
    if http_error.response.status_code == requests.codes.bad_request:
        return ValidationError(http_error=http_error)
    elif http_error.response.status_code == requests.codes.unauthorized:
        return NotAuthenticatedError(http_error=http_error)
    elif http_error.response.status_code == requests.codes.forbidden:
        error_message = get_http_error_message(http_error)
        if "Invalid login or password" in error_message:
            return InvalidCredentialsError(http_error=http_error)
        elif "Maintenance underway" in error_message:
            return MaintenanceUnderwayError(http_error=http_error)
        elif "User registration is pending" in error_message:
            return UserPendingError(http_error=http_error)
        elif "User account is disabled" in error_message:
            return UserDisabledError(http_error=http_error)
        return PermissionError(http_error=http_error)
    elif http_error.response.status_code == requests.codes.not_found:
        error_message = get_http_error_message(http_error)
        if "The requested URL was not found on the server" in error_message:
            return EndpointNotFoundError(http_error=http_error)
        return ObjectNotFoundError(http_error=http_error)
    elif http_error.response.status_code == requests.codes.conflict:
        return TypeConflictError(http_error=http_error)
    elif http_error.response.status_code == requests.codes.too_many_requests:
        return LimitExceededError(http_error=http_error)
    elif http_error.response.status_code in [
        requests.codes.bad_gateway,
        requests.codes.gateway_timeout,
    ]:
        return GatewayError(http_error=http_error)
    else:
        # Other codes are classified as internal error
        return InternalError(http_error=http_error)
