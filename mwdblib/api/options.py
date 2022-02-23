import configparser
import pathlib
import warnings
from typing import Any, Optional, Type

import keyring
import keyring.errors


class OptionsField:
    def __init__(
        self, default_value: Any = None, value_type: Optional[Type] = None
    ) -> None:
        self.default_value: Any = default_value
        self.nullable: bool = default_value is None
        self.value_type: Type = value_type or type(default_value)

    def load_from_config(
        self, instance: Any, config_parser: configparser.ConfigParser, section: str
    ) -> None:
        """
        Loads value from configuration and overrides field if value is set.
        """
        value: Optional[Any]
        if self.value_type is bool:
            value = config_parser.getboolean(section, self.name, fallback=None)
        elif self.value_type is int:
            value = config_parser.getint(section, self.name, fallback=None)
        else:
            value = config_parser.get(section, self.name, fallback=None)
        if value is not None:
            self.__set__(instance, value)

    def load_from_dict(self, instance: Any, dictionary: dict) -> None:
        """
        Loads value from dictionary if set. Accepts None.
        """
        if self.name in dictionary:
            self.__set__(instance, dictionary[self.name])

    def __set_name__(self, owner: Any, name: str) -> None:
        self.name = name
        self.instance_name = "_" + name

    def __get__(self, instance: Any, owner: Any) -> Any:
        if hasattr(instance, self.instance_name):
            return getattr(instance, self.instance_name)
        return self.default_value

    def __set__(self, instance: Any, value: Any) -> None:
        if not (self.nullable and value is None) and type(value) is not self.value_type:
            raise TypeError(
                f"Expected '{self.name}' to be {self.value_type} not {type(value)}"
            )
        setattr(instance, self.instance_name, value)


class APIClientOptions:
    """
    Options bag that contains configuration for APIClient.

    Field values are loaded using the following precedence:

    - built-in defaults accessible via class properties e.g.
      ``APIClientOptions.api_url``
    - values from ``~/.mwdb`` configuration file
    - values passed as an arguments to the ``APIClientOptions`` constructor

    Configuration may depend on ``api_url`` value, so remember to set it if you want to
    talk with specific MWDB Core instance.
    """

    # Register fields and defaults
    api_url = OptionsField("https://mwdb.cert.pl/api/")
    api_key = OptionsField(value_type=str)
    username = OptionsField(value_type=str)
    password = OptionsField(value_type=str)
    verify_ssl = OptionsField(True)
    obey_ratelimiter = OptionsField(True)
    retry_on_downtime = OptionsField(False)
    max_downtime_retries = OptionsField(5)
    downtime_timeout = OptionsField(10)
    retry_idempotent = OptionsField(True)
    use_keyring = OptionsField(True)
    emit_warnings = OptionsField(True)

    # General options that can be set both globally or for specific instance
    GENERAL_OPTIONS = [
        verify_ssl,
        obey_ratelimiter,
        retry_on_downtime,
        max_downtime_retries,
        downtime_timeout,
        retry_idempotent,
        use_keyring,
        emit_warnings,
    ]
    # Options that apply only to global mwdblib configuration
    GLOBAL_ONLY_OPTIONS = [api_url]
    # Options that apply only to specific MWDB instance
    INSTANCE_ONLY_OPTIONS = [api_key, username, password]

    # Configuration priority (from least important):
    # - global configuration section [mwdb]
    # - instance configuration section [mwdb:<api_url>]
    # - api_options keyword arguments

    def __init__(
        self,
        config_path: Optional[pathlib.Path] = (pathlib.Path.home() / ".mwdb"),
        **api_options: Any,
    ) -> None:
        self.config_parser: configparser.ConfigParser = configparser.ConfigParser()
        if config_path is not None:
            # Ensure that config_path is Path object
            self.config_path: Optional[pathlib.Path] = pathlib.Path(config_path)
            # Read configuration from provided path or do nothing if doesn't exist
            self.config_parser.read([self.config_path])
        else:
            # If config_path is None, assume that user doesn't want to
            # fetch credentials from keyring as well
            self.config_path = None
            self.use_keyring = False

        # For each settings item: override defaults by global configuration
        for option in self.GENERAL_OPTIONS + self.GLOBAL_ONLY_OPTIONS:
            option.load_from_config(self, self.config_parser, "mwdb")
            option.load_from_dict(self, api_options)

        # Normalize api_url
        if not self.api_url.endswith("/"):
            self.api_url += "/"
        if not self.api_url.endswith("/api/") and self.emit_warnings:
            warnings.warn(
                "APIClient.api_url doesn't end with '/api/'. Make sure you have passed "
                "URL to the REST API instead of MWDB UI"
            )

        # Load general settings from instance configuration
        for option in self.GENERAL_OPTIONS + self.INSTANCE_ONLY_OPTIONS:
            option.load_from_config(self, self.config_parser, f"mwdb:{self.api_url}")
            option.load_from_dict(self, api_options)

        # If keyring is used: fetch credentials from keyring
        # Otherwise: assume that they're stored plaintext in configuration
        if (
            self.username is not None
            and self.use_keyring
            and "api_key" not in api_options
            and "password" not in api_options
        ):
            self.api_key = keyring.get_password(
                f"mwdb-apikey:{self.api_url}", self.username
            )
            # If api_key not set: try to fetch password
            if self.api_key is None:
                self.password = keyring.get_password(
                    f"mwdb:{self.api_url}", self.username
                )

    def clear_stored_credentials(self, config_writeback: bool = True) -> None:
        """
        Clears stored credentials in configuration for current user.

        Used by ``mwdb logout`` CLI command.
        """
        if not self.username:
            return
        # Remove credentials from keyring
        if self.use_keyring:
            try:
                keyring.delete_password(f"mwdb-apikey:{self.api_url}", self.username)
            except keyring.errors.PasswordDeleteError:
                pass
            try:
                keyring.delete_password(f"mwdb:{self.api_url}", self.username)
            except keyring.errors.PasswordDeleteError:
                pass
        instance_section = f"mwdb:{self.api_url}"
        # Remove credentials from configuration
        if self.config_parser.has_section(instance_section):
            if self.config_parser.has_option(instance_section, "username"):
                self.config_parser.remove_option(instance_section, "username")
            if self.config_parser.has_option(instance_section, "password"):
                self.config_parser.remove_option(instance_section, "password")
            if self.config_parser.has_option(instance_section, "api_key"):
                self.config_parser.remove_option(instance_section, "api_key")
            if config_writeback and self.config_path:
                with self.config_path.open("w") as f:
                    self.config_parser.write(f)

    def store_credentials(self) -> None:
        """
        Stores current credentials in configuration for current user.

        Used by ``mwdb login`` CLI command.
        """
        if not self.username or (not self.api_key and not self.password):
            return
        # Clear currently stored credentials
        self.clear_stored_credentials(config_writeback=False)
        # Ensure that 'mwdb' section exists in configuration
        if not self.config_parser.has_section("mwdb"):
            self.config_parser.add_section("mwdb")
        # Set api_url information
        self.config_parser.set("mwdb", "api_url", self.api_url)
        # Set credentials for instance
        instance_section = f"mwdb:{self.api_url}"
        if not self.config_parser.has_section(instance_section):
            self.config_parser.add_section(instance_section)
        self.config_parser.set(instance_section, "username", self.username)
        # Set credentials
        if self.use_keyring:
            if self.api_key:
                keyring.set_password(
                    f"mwdb-apikey:{self.api_url}", self.username, self.api_key
                )
            else:
                keyring.set_password(
                    f"mwdb:{self.api_url}", self.username, self.password
                )
        else:
            if self.api_key:
                self.config_parser.set(instance_section, "api_key", self.api_key)
            else:
                self.config_parser.set(instance_section, "password", self.password)
        # Perform configuration writeback
        if self.config_path:
            with self.config_path.open("w") as f:
                self.config_parser.write(f)
