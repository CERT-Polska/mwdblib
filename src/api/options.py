import configparser
import keyring
import keyring.errors
import pathlib


class OptionsField:
    def __init__(self, value=None, value_type=None):
        self.value = value
        self.value_type = value_type or type(value)

    def load_from_config(self, config_parser):
        """
        Loads value from configuration and overrides field if value is set.
        """
        if self.value_type is bool:
            value = config_parser.getboolean("mwdb", self.name, fallback=None)
        elif self.value_type is int:
            value = config_parser.getint("mwdb", self.name, fallback=None)
        else:
            value = config_parser.get("mwdb", self.name, fallback=None)
        if value is not None:
            self.value = value

    def load_from_dict(self, dictionary):
        """
        Loads value from dictionary if set. Accepts None.
        """
        if self.name in dictionary:
            self.value = dictionary[self.name]

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        return self.value

    def __set__(self, instance, value):
        if type(value) is not self.value_type:
            raise TypeError(f"Expected '{self.name}' to be {str(self.value_type)}")
        self.value = value


class APIClientOptions:
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

    def __init__(self, config_path=(pathlib.Path.home() / ".mwdb"), **api_options):
        self.config_parser = configparser.ConfigParser()
        if config_path is not None:
            # Ensure that config_path is pathlib object
            self.config_path = pathlib.Path(config_path)
            # Read configuration from provided path or do nothing if doesn't exist
            self.config_parser.read([self.config_path])
        else:
            self.config_path = None
        # For each settings item
        for name, item in self.__dict__.items():
            if not isinstance(item, OptionsField):
                continue
            # Override defaults by configuration
            item.load_from_config(self.config_parser)
            # Override by api_options values
            item.load_from_dict(api_options)
        # Load credentials from keyring if keyring is active,
        # username is set in configuration
        # and credentials are not set in api_options or configuration
        if (
            self.use_keyring
            and self.username is not None
            and self.password is None
            and self.api_key is None
        ):
            self.api_key = keyring.get_password("mwdb-apikey", self.username)
            if self.api_key is None:
                self.password = keyring.get_password("mwdb", self.username)

    def clear_stored_credentials(self, config_writeback=True):
        """
        Clears stored credentials in configuration for current user
        Used by `mwdb logout` and `mwdb login` CLI command
        """
        if not self.username:
            return
        # Remove credentials from keyring
        if self.use_keyring:
            try:
                keyring.delete_password("mwdb-apikey", self.username)
            except keyring.errors.PasswordDeleteError:
                pass
            try:
                keyring.delete_password("mwdb", self.username)
            except keyring.errors.PasswordDeleteError:
                pass
        # Remove credentials from configuration
        if self.config_parser.has_section("mwdb"):
            if self.config_parser.has_option("mwdb", "username"):
                self.config_parser.remove_option("mwdb", "username")
            if self.config_parser.has_option("mwdb", "password"):
                self.config_parser.remove_option("mwdb", "password")
            if self.config_parser.has_option("mwdb", "api_key"):
                self.config_parser.remove_option("mwdb", "api_key")
            if self.config_path and config_writeback:
                with self.config_path.open("w") as f:
                    self.config_parser.write(f)

    def store_credentials(self, config_writeback=True):
        """
        Stores current credentials in configuration for current user
        Used by `mwdb login` CLI command
        """
        if not self.username or (not self.api_key and not self.password):
            return
        # Clear currently stored credentials
        self.clear_stored_credentials(config_writeback=False)
        # Ensure that 'mwdb' section exists in configuration
        if not self.config_parser.has_section("mwdb"):
            self.config_parser.add_section("mwdb")
        # Set basic information
        self.config_parser.set("mwdb", "api_url", self.api_url)
        self.config_parser.set("mwdb", "username", self.username)
        # Set credentials
        if self.use_keyring:
            if self.api_key:
                keyring.set_password("mwdb-apikey", self.username, self.api_key)
            else:
                keyring.set_password("mwdb", self.username, self.password)
        else:
            if self.api_key:
                self.config_parser.set("mwdb", "api_key", self.api_key)
            else:
                self.config_parser.set("mwdb", "password", self.password)
        # Perform configuration writeback
        if self.config_path and config_writeback:
            with self.config_path.open("w") as f:
                self.config_parser.write(f)
