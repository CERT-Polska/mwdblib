import getpass
import warnings

from .api import APIClient
from .methods import MWDBMethods
from .remote import RemoteAPIClient, MWDBRemote

try:
    import __builtin__
    user_input = getattr(__builtin__, "raw_input")
except ImportError:
    user_input = input


class MWDB(MWDBMethods):
    """
    Main object used for communication with MWDB REST API

    :param api: Custom :class:`APIClient` used to communicate with MWDB
    :type api: :class:`mwdblib.APIClient`, optional
    :param api_key: API key used for authentication (omit if password-based authentication is used)
    :type api_key: str, optional

    .. versionadded:: 2.6.0
       API request will sleep for a dozen of seconds when rate limit has been exceeded.

    .. versionadded:: 3.2.0
       You can enable :attr:`retry_on_downtime` to automatically retry
       requests in case of HTTP 502/504 or ConnectionError.

    .. versionadded:: 3.5.0
        Added support for remote instances (requires MWDB Core >=2.2.0)

    Usage example:

    .. code-block:: python

       from mwdblib import MWDB

       mwdb = MWDB()
       mwdb.login("example", "<password>")

       file = mwdb.query_file("3629344675705286607dd0f680c66c19f7e310a1")

    """

    def __init__(self, api=None, **api_options):
        super(MWDB, self).__init__(
            api=api or APIClient(**api_options)
        )

    def login(self, username=None, password=None, warn=True):
        """
        Performs user authentication using provided username and password.

        .. warning::

           Keep in mind that password-authenticated sessions are short lived, so password needs to be stored
           in :class:`APIClient` object. Consider generating a new API key in your MWDB profile.

        .. versionadded:: 2.4.0
           MWDB tries to reauthenticate on first Unauthorized exception

        .. versionadded:: 2.5.0
           username and password arguments are optional. If one of the credentials is not provided via arguments,
           user will be asked for it.

        .. versionadded:: 2.6.0
           :py:meth:`MWDB.login` will warn if login is called after setting up API key

        :param username: User name
        :type username: str
        :param password: Password
        :type password: str
        :param warn: Show warning about password-authenticated sessions
        :type warn: bool (default: True)
        :raises: requests.exceptions.HTTPError
        """
        if self.api.api_key is not None:
            warnings.warn("login() will reset the previously set API key. If you really want to reauthenticate, "
                          "call logout() before to suppress this warning.")
        if username is None:
            # Py2 compatibility
            username = user_input("Username: ")
        if password is None:
            password = getpass.getpass("Password: ")
        self.api.login(username, password, warn=warn)

    def logout(self):
        """
        Performs session logout and removes previously set API key.
        """
        self.api.logout()

    def list_remotes(self):
        """
        .. versionadded:: 3.5.0

        Shows a list of available remote instance names

        :return: List of available remote names
        """
        return self.api.get("remote")["remotes"]

    def remote(self, remote_name):
        """
        .. versionadded:: 3.5.0

        Returns an MWDBRemote object that allows to operate
        on the remote MWDB instance

        .. code-block:: python

            mwdb = MWDB(api_url="http://127.0.0.1/api")

            # Get mwdb.cert.pl remote object
            mwdb_cert = mwdb.remote("mwdb.cert.pl")

            # Get file object from mwdb.cert.pl
            remote_file = mwdb_cert.query_file("75dec9b5253ba55a6fecc2e96a704e654785e7d9")

            # Pull that file to the local instance
            local_file = mwdb_cert.pull_file(remote_file)

        :param remote_name: Remote instance name
        :type remote_name: str
        :return: MWDBRemote object
        """
        return MWDBRemote(
            RemoteAPIClient(self.api, remote_name)
        )


# Backwards compatibility
Malwarecage = MWDB
