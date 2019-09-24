import os
import configparser
import functools

from click.globals import get_current_context
import click
import keyring

from ..api import MalwarecageAPI, API_URL
from ..core import Malwarecage
from ..exc import MalwarecageError


class MwdbAuthenticator(object):
    CONFIG_PATH = os.path.expanduser("~/.mwdb")
    CONFIG_FIELDS = [
        "username",
        "api_url",
        "verify_ssl",
        "obey_ratelimiter"
    ]

    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read(['mwdb.cfg', self.CONFIG_PATH])

    def get_authenticated_mwdb(self, api_url=None):
        """
        Gets pre-authenticated Malwarecage object based on local configuration
        :param api_url: Alternative API url provided explicitly by user
        :rtype: Malwarecage
        """
        api_url = api_url or self.config.get("mwdb", "api_url", fallback=API_URL)
        api = MalwarecageAPI(api_url=api_url,
                             verify_ssl=self.config.getboolean("mwdb", "verify_ssl", fallback=True),
                             obey_ratelimiter=self.config.getboolean("mwdb", "obey_ratelimiter", fallback=True))

        username = self.config.get("mwdb", "username", fallback=None)
        if username is not None:
            api_key = keyring.get_password("mwdb-apikey", username)
            if api_key is not None:
                api.set_api_key(api_key)
            else:
                password = keyring.get_password("mwdb", username)
                api.login(username, password, warn=False)
        mwdb = Malwarecage(api=api)
        # If not authenticated: ask for credentials
        if mwdb.api.api_key is None:
            mwdb.login(warn=False)
        return mwdb

    def store_login(self, username, password, api_key):
        """
        Sets credentials into user configuration file and keyring
        :param username: Username to store
        :param password: Password to store
        :param api_key: API key to store
        """
        if api_key is not None:
            api = MalwarecageAPI(api_key=api_key)
            username = api.logged_user
            self.set_config("username", username)
            keyring.set_password("mwdb-apikey", username, api_key)
        else:
            self.set_config("username", username)
            keyring.set_password("mwdb", username, password)

    def reset_login(self):
        """
        Removes credentials from user configuration file and keyring
        """
        username = self.config.get("mwdb", "username", fallback=None)
        if username is None:
            return
        self.set_config("username", None)
        if keyring.get_password("mwdb-apikey", username):
            keyring.delete_password("mwdb-apikey", username)
        if keyring.get_password("mwdb", username):
            keyring.delete_password("mwdb", username)

    def set_config(self, field, value):
        """
        Sets provided field in user configuration file
        :param field: Field name
        :param value: New value or None if field should be erased from configuration
        """
        if field not in self.CONFIG_FIELDS:
            raise ValueError("Incorrect field '{}'".format(field))
        if not self.config.has_section("mwdb"):
            self.config.add_section("mwdb")
        if value is not None:
            self.config.set("mwdb", field, value)
        elif self.config.has_option("mwdb", field):
            self.config.remove_option("mwdb", field)
        with open(self.CONFIG_PATH, "w") as f:
            self.config.write(f)


def pass_mwdb(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        ctx = get_current_context()
        authenticator = MwdbAuthenticator()
        mwdb = authenticator.get_authenticated_mwdb(ctx.obj.get("api_url", None))
        try:
            return fn(mwdb=mwdb, *args, **kwargs)
        except MalwarecageError as error:
            click.echo("{}: {}".format(error.__class__.__name__, error.args[0]), err=True)
            ctx.abort()
    return wrapper
