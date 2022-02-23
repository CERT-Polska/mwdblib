import getpass
import json
import time
from typing import (
    TYPE_CHECKING,
    Any,
    BinaryIO,
    Dict,
    Iterator,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
    cast,
)

from .api import APIClient
from .blob import MWDBBlob
from .config import MWDBConfig
from .exc import ObjectNotFoundError, ValidationError
from .file import MWDBFile
from .object import MWDBObject

if TYPE_CHECKING:
    from .api.options import APIClientOptions

MWDBObjectVar = TypeVar("MWDBObjectVar", bound=MWDBObject)


class MWDB:
    """
    Main object used for communication with MWDB REST API

    :param api_url: MWDB API URL (that ends with '/api/').
    :param api_key: MWDB API key
    :param username: MWDB account username
    :param password: MWDB account password
    :param verify_ssl: Verify SSL certificate correctness (default: True)
    :param obey_ratelimiter: If ``False``, HTTP 429 errors will cause an exception
        like all other error codes.
        If ``True``, library will transparently handle them by sleeping
        for a specified duration. Default is ``True``.
    :param retry_on_downtime: If ``True``, requests will be automatically retried
        after ``downtime_timeout`` seconds on HTTP 502/504 and ConnectionError.
        Default is ``False``.
    :param max_downtime_retries: Number of retries caused by temporary downtime
    :param downtime_timeout: How long we need to wait between retries (in seconds).
        Default is 10.
    :param retry_idempotent: Retry idempotent POST requests (default).
        The only thing that is really non-idempotent in current API is
        :meth:`MWDBObject.add_comment`, so it's not a big deal. You can turn it off
        if possible doubled comments are problematic in your MWDB instance.
        Default is ``True``.
    :param use_keyring: If ``True``, APIClient uses keyring to fetch
        stored credentials. If not, they're fetched from plaintext configuration.
        Default is ``True``.
    :param emit_warnings: If ``True``, warnings are emitted by APIClient.
        Default is ``True``.
    :param config_path: Path to the configuration file (default is `~/.mwdb`).
        If None, configuration file will not be used by APIClient
    :param api: Custom :class:`APIClient` to be used for communication with MWDB
    :type api: :class:`mwdblib.APIClient`, optional

    .. versionadded:: 2.6.0
       API request will sleep for a dozen of seconds when rate limit has been exceeded.

    .. versionadded:: 3.2.0
       You can enable :attr:`retry_on_downtime` to automatically retry
       requests in case of HTTP 502/504 or ConnectionError.

    .. versionchanged:: 4.0.0
       :class:`MWDB` by default uses credentials and api_url set by `mwdb login`.
       If you don't want to automatically fetch them from configuration,
       pass `config_path=None` to the constructor

    .. versionadded:: 4.0.0
       Added ``use_keyring``, ``emit_warnings`` and ``config_path`` options.
       ``username`` and ``password`` can be passed directly to the constructor.

    Usage example:

    .. code-block:: python

       from mwdblib import MWDB

       mwdb = MWDB()
       mwdb.login("example", "<password>")

       file = mwdb.query_file("3629344675705286607dd0f680c66c19f7e310a1")
    """

    def __init__(self, api: Optional[APIClient] = None, **api_options: Any):
        self.api = api or APIClient(**api_options)

    @property
    def options(self) -> "APIClientOptions":
        """
        Returns object with current configuration of MWDB client

        .. versionadded:: 4.0.0
           Added MWDB.options property.
        """
        return self.api.options

    def login(
        self, username: Optional[str] = None, password: Optional[str] = None
    ) -> None:
        """
        Performs user authentication using provided username and password.

        If credentials are not set, asks interactively for credentials.

        .. warning::

           Keep in mind that password-authenticated sessions are short-lived,
           so password needs to be stored in :class:`APIClient` object.
           Consider generating a new API key in your MWDB profile.

        .. versionadded:: 2.4.0
           MWDB tries to reauthenticate on first Unauthorized exception

        .. versionadded:: 2.5.0
           username and password arguments are optional. If one of the credentials
           is not provided via arguments, user will be asked for it.

        .. versionadded:: 2.6.0
           :py:meth:`MWDB.login` will warn if login is called after setting up API key

        .. versionchanged:: 4.0.0
            :py:meth:`MWDB.login` no longer warns about password-authenticated sessions
            or credentials that are already set up.

        :param username: Username
        :type username: str
        :param password: Password
        :type password: str
        :raises: requests.exceptions.HTTPError
        """
        if username is None:
            username = input("Username: ")
        if password is None:
            password = getpass.getpass("Password: ")
        self.api.login(username, password)

    def logout(self) -> None:
        """
        Performs session logout and removes previously set API key.
        """
        self.api.logout()

    def _recent(
        self, object_type: Type[MWDBObjectVar], query: Optional[str] = None
    ) -> Iterator[MWDBObjectVar]:
        """
        Generic implementation of recent_* methods
        """
        try:
            last_object: Optional[MWDBObject] = None
            while True:
                params = {"older_than": last_object.id} if last_object else {}
                if query is not None:
                    params["query"] = query
                # 'object', 'file', 'config' or 'blob'?
                result = self.api.get(object_type.URL_TYPE, params=params)
                key = object_type.URL_TYPE + "s"
                if key not in result or len(result[key]) == 0:
                    return
                for obj in result[key]:
                    last_object = object_type.create(self.api, obj)
                    yield cast(MWDBObjectVar, last_object)
        except ObjectNotFoundError:
            return

    def recent_objects(self) -> Iterator[MWDBObject]:
        """
        Retrieves recently uploaded objects
        If you already know type of object you are looking for,
        use specialized variants:

        - :py:meth:`recent_files`
        - :py:meth:`recent_configs`
        - :py:meth:`recent_blobs`

        Usage example:

        .. code-block:: python

            from mwdblib import MWDB
            from itertools import islice

            mwdb = MWDB()
            mwdb.login("admin", "password123")

            # recent_files is generator, do not execute list(recent_files)!
            files = islice(mwdb.recent_files(), 25)
            print([(f.name, f.tags) for f in files])

        :rtype: Iterator[:class:`MWDBObject`]
        :raises: requests.exceptions.HTTPError
        """
        return self._recent(MWDBObject)

    def recent_files(self) -> Iterator[MWDBFile]:
        """
        Retrieves recently uploaded files

        :rtype: Iterator[:class:`MWDBFile`]
        :raises: requests.exceptions.HTTPError
        """
        return self._recent(MWDBFile)

    def recent_configs(self) -> Iterator[MWDBConfig]:
        """
        Retrieves recently uploaded configuration objects

        :rtype: Iterator[:class:`MWDBConfig`]
        :raises: requests.exceptions.HTTPError
        """
        return self._recent(MWDBConfig)

    def recent_blobs(self) -> Iterator[MWDBBlob]:
        """
        Retrieves recently uploaded blob objects

        :rtype: Iterator[:class:`MWDBBlob`]
        :raises: requests.exceptions.HTTPError
        """
        return self._recent(MWDBBlob)

    def _listen(
        self,
        last_object: Optional[Union[MWDBObjectVar, str]],
        object_type: Type[MWDBObjectVar],
        blocking: bool,
        interval: int,
        query: Optional[str],
    ) -> Iterator[MWDBObjectVar]:
        """
        Generic implementation of listen_* methods
        """
        last: Optional[MWDBObjectVar]
        if last_object is None:
            last = next(self._recent(object_type, query=query), None)
            # If there are no elements (even first element):
            # just get new samples from now on
        elif isinstance(last_object, MWDBObject):
            # If we are requesting for typed objects,
            # we should additionally check the object type
            if object_type is not MWDBObject and not isinstance(
                last_object, object_type
            ):
                raise TypeError(
                    "latest_object type must be 'str' or '{}'".format(
                        object_type.__name__
                    )
                )
            # If object instance provided: get ID from instance
            last = cast(MWDBObjectVar, last_object)
        elif isinstance(last_object, str):
            # If not: first check whether object exists in repository
            last = self._query(object_type, last_object, raise_not_found=True)
        else:
            raise TypeError("'last_object' must be MWDBObject instance, str or None")

        while True:
            objects: List[MWDBObjectVar] = []
            for recent_object in self._recent(object_type, query=query):
                if last:
                    if recent_object.id == last.id:
                        break

                    if recent_object.upload_time < last.upload_time:
                        raise RuntimeError(
                            f"Newly fetched object [{recent_object.id}] is older than "
                            f"the pivot [{last.id}]"
                        )
                objects.append(recent_object)

            # Return fetched objects in reversed order (from oldest to latest)
            for obj in objects[::-1]:
                last = obj
                yield obj
            if blocking:
                time.sleep(interval)
            else:
                break

    def listen_for_objects(
        self,
        last_object: Optional[Union[MWDBObject, str]] = None,
        blocking: bool = True,
        interval: int = 15,
        query: Optional[str] = None,
    ) -> Iterator[MWDBObject]:
        """
        Listens for recent objects and yields newly added.

        In blocking mode (default) if last_object is provided: the method fetches
        the latest objects until the provided object is reached and yields new objects
        from the oldest one. Otherwise, the method periodically asks for recent objects
        until a new object appears. The default request interval is 15 seconds.

        In a non-blocking mode: a generator stops if there are no more objects to fetch.

        last_object argument accepts both identifier and MWDBObject instance. If
        the object identifier is provided: method firstly checks whether the object
        exists in repository and has the correct type.

        If you already know type of object you are looking for,
        use specialized variants:

        - :py:meth:`listen_for_files`
        - :py:meth:`listen_for_configs`
        - :py:meth:`listen_for_blobs`

        .. warning::
            Make sure that last_object is valid in MWDB instance. If you provide
            MWDBObject that doesn't exist, mwdblib will iterate over all objects
            and you can quickly hit your rate limit. Library is trying to protect you
            from that as much as possible by checking type and object existence, but
            it's still possible to do something unusual.

            Additionally, if using the ``query`` parameter and passing
            the ``last_object`` pivot, make sure that the passed object actually
            matches the query criteria. Otherwise the mechanism that catches faulty
            pivots will signal that there's something wrong and raise an exception.

        .. versionadded:: 3.2.0
            Added listen_for_* methods

        .. versionadded:: 3.4.0
            Added query parameter

        .. versionadded:: 3.4.0
            The listen_for_* methods will now try to prevent you from iterating
            over the whole database by throwing an exception if they detect that
            there is something wrong with the pivot object

        :param last_object: MWDBObject instance or object hash
        :type last_object: MWDBObject or str
        :param blocking: Enable blocking mode (default)
        :type blocking: bool, optional
        :param interval: Interval for periodic queries in blocking mode
            (default is 15 seconds)
        :type interval: int, optional
        :param query: Lucene query to be used for listening for only specific objects
        :type query: str, optional
        :rtype: Iterator[:class:`MWDBObject`]
        """
        return self._listen(
            last_object,
            object_type=MWDBObject,
            blocking=blocking,
            interval=interval,
            query=query,
        )

    def listen_for_files(
        self,
        last_object: Optional[Union[MWDBFile, str]] = None,
        blocking: bool = True,
        interval: int = 15,
        query: Optional[str] = None,
    ) -> Iterator[MWDBFile]:
        """
        Listens for recent files and yields newly added.

        .. seealso::
            More details can be found here: :meth:`listen_for_objects`

        .. versionadded:: 3.2.0
            Added listen_for_* methods

        .. versionadded:: 3.4.0
            Added query parameter

        .. versionadded:: 3.4.0
            The listen_for_* methods will now try to prevent you from iterating
            over the whole database by throwing an exception if they detect that
            there is something wrong with the pivot object

        :param last_object: MWDBFile instance or object hash
        :type last_object: MWDBFile or str
        :param blocking: Enable blocking mode (default)
        :type blocking: bool, optional
        :param interval: Interval for periodic queries in blocking mode
            (default is 15 seconds)
        :type interval: int, optional
        :param query: Lucene query to be used for listening for only specific files
        :type query: str, optional
        :rtype: Iterator[:class:`MWDBFile`]
        """
        return self._listen(
            last_object,
            object_type=MWDBFile,
            blocking=blocking,
            interval=interval,
            query=query,
        )

    def listen_for_configs(
        self,
        last_object: Optional[Union[MWDBConfig, str]] = None,
        blocking: bool = True,
        interval: int = 15,
        query: Optional[str] = None,
    ) -> Iterator[MWDBConfig]:
        """
        Listens for recent configs and yields newly added.

        .. seealso::
            More details can be found here: :meth:`listen_for_objects`

        .. versionadded:: 3.2.0
            Added listen_for_* methods

        .. versionadded:: 3.4.0
            Added query parameter

        .. versionadded:: 3.4.0
            The listen_for_* methods will now try to prevent you from iterating
            over the whole database by throwing an exception if they detect that
            there is something wrong with the pivot object

        :param last_object: MWDBConfig instance or object hash
        :type last_object: MWDBConfig or str
        :param blocking: Enable blocking mode (default)
        :type blocking: bool, optional
        :param interval: Interval for periodic queries in blocking mode
            (default is 15 seconds)
        :type interval: int, optional
        :param query: Lucene query to be used for listening for only specific configs
        :type query: str, optional
        :rtype: Iterator[:class:`MWDBConfig`]
        """
        return self._listen(
            last_object,
            object_type=MWDBConfig,
            blocking=blocking,
            interval=interval,
            query=query,
        )

    def listen_for_blobs(
        self,
        last_object: Optional[Union[MWDBBlob, str]] = None,
        blocking: bool = True,
        interval: int = 15,
        query: Optional[str] = None,
    ) -> Iterator[MWDBBlob]:
        """
        Listens for recent blobs and yields newly added.

        .. seealso::
            More details can be found here: :meth:`listen_for_objects`

        .. versionadded:: 3.2.0
            Added listen_for_* methods

        .. versionadded:: 3.4.0
            Added query parameter

        .. versionadded:: 3.4.0
            The listen_for_* methods will now try to prevent you from iterating
            over the whole database by throwing an exception if they detect that
            there is something wrong with the pivot object

        :param last_object: MWDBBlob instance or object hash
        :type last_object: MWDBBlob or str
        :param blocking: Enable blocking mode (default)
        :type blocking: bool, optional
        :param interval: Interval for periodic queries in blocking mode
            (default is 15 seconds)
        :type interval: int, optional
        :param query: Lucene query to be used for listening for only specific blobs
        :type query: str, optional
        :rtype: Iterator[:class:`MWDBBlob`]
        """
        return self._listen(
            last_object,
            object_type=MWDBBlob,
            blocking=blocking,
            interval=interval,
            query=query,
        )

    def _query(
        self, object_type: Type[MWDBObjectVar], hash: str, raise_not_found: bool
    ) -> Optional[MWDBObjectVar]:
        """
        Generic implementation of query_* methods
        """
        try:
            url_pattern = object_type.URL_TYPE + "/{id}"
            result = self.api.get(url_pattern.format(id=hash))
            return cast(MWDBObjectVar, object_type.create(self.api, result))
        except ObjectNotFoundError:
            if not raise_not_found:
                return None
            else:
                raise

    def query(self, hash: str, raise_not_found: bool = True) -> Optional[MWDBObject]:
        """
        Queries for object using provided hash.
        If you already know type of object you are looking for,
        use specialized variants:

        - :py:meth:`query_file`
        - :py:meth:`query_config`
        - :py:meth:`query_blob`

        .. versionadded:: 2.4.0
           Added raise_not_found optional argument

        .. versionchanged:: 3.0.0
           Fallback to :py:meth:`query_file` if other hash than SHA256 was provided

        :param hash: Object hash (identifier, MD5, SHA-1, SHA-2)
        :type hash: str
        :param raise_not_found: If True (default), method raises HTTPError
            when object is not found
        :type raise_not_found: bool, optional
        :rtype: :class:`MWDBObject` or None (if raise_not_found=False)
        :raises: requests.exceptions.HTTPError
        """
        if len(hash) != 64:
            # If different hash than SHA256 was provided
            return self.query_file(hash, raise_not_found=raise_not_found)
        return self._query(MWDBObject, hash, raise_not_found)

    def query_file(self, hash: str, raise_not_found: bool = True) -> Optional[MWDBFile]:
        """
        Queries for file using provided hash

        :param hash: Object hash (identifier, MD5, SHA-1, SHA-2)
        :type hash: str
        :param raise_not_found: If True (default), method raises HTTPError
            when object is not found
        :type raise_not_found: bool
        :rtype: :class:`MWDBFile` or None (if raise_not_found=False)
        :raises: requests.exceptions.HTTPError
        """
        return self._query(MWDBFile, hash, raise_not_found)

    def query_config(
        self, hash: str, raise_not_found: bool = True
    ) -> Optional[MWDBConfig]:
        """
        Queries for configuration object using provided hash

        :param hash: Object hash (SHA-256 identifier)
        :type hash: str
        :param raise_not_found: If True (default), method raises HTTPError
            when object is not found
        :type raise_not_found: bool
        :rtype: :class:`MWDBConfig` or None (if raise_not_found=False)
        :raises: requests.exceptions.HTTPError
        """
        return self._query(MWDBConfig, hash, raise_not_found)

    def query_blob(self, hash: str, raise_not_found: bool = True) -> Optional[MWDBBlob]:
        """
        Queries for blob object using provided hash

        :param hash: Object hash (SHA-256 identifier)
        :type hash: str
        :param raise_not_found: If True (default), method raises HTTPError
            when object is not found
        :type raise_not_found: bool
        :rtype: :class:`MWDBBlob` or None (if raise_not_found=False)
        :raises: requests.exceptions.HTTPError
        """
        return self._query(MWDBBlob, hash, raise_not_found)

    def search(self, query: str) -> Iterator[MWDBObject]:
        """
        Advanced search for objects using Lucene syntax.
        If you already know type of objects you are looking for,
        use specialized variants:

        - :py:meth:`search_files`
        - :py:meth:`search_configs`
        - :py:meth:`search_blobs`

        Usage example:

        .. code-block:: python

            from mwdblib import MWDB

            # Search for samples tagged as evil and with size less than 100kB
            results = mwdb.search_files("tag:evil AND file.size:[0 TO 100000]")

        :param query: Search query
        :type query: str
        :rtype: Iterator[:class:`MWDBObject`]
        :raises: requests.exceptions.HTTPError
        """
        return self._recent(MWDBObject, query)

    def search_files(self, query: str) -> Iterator[MWDBFile]:
        """
        Advanced search for files using Lucene syntax.

        :param query: Search query
        :type query: str
        :rtype: Iterator[:class:`MWDBFile`]
        :raises: requests.exceptions.HTTPError
        """
        return self._recent(MWDBFile, query)

    def search_configs(self, query: str) -> Iterator[MWDBConfig]:
        """
        Advanced search for configuration objects using Lucene syntax.

        :param query: Search query
        :type query: str
        :rtype: Iterator[:class:`MWDBConfig`]
        :raises: requests.exceptions.HTTPError
        """
        return self._recent(MWDBConfig, query)

    def search_blobs(self, query: str) -> Iterator[MWDBBlob]:
        """
        Advanced search for blob objects using Lucene syntax.

        :param query: Search query
        :type query: str
        :rtype: Iterator[:class:`MWDBBlob`]
        :raises: requests.exceptions.HTTPError
        """
        return self._recent(MWDBBlob, query)

    def _count(
        self, object_type: Type[MWDBObjectVar], query: Optional[str] = None
    ) -> int:
        """
        Generic implementation for count_* methods
        """
        params = {"query": query}
        result = self.api.get(object_type.URL_TYPE + "/count", params=params)
        return cast(int, result["count"])

    def count(self, query: Optional[str] = None) -> int:
        """
        Returns number of objects matching provided query in Lucene syntax.
        If you already know type of objects you want to count, use specialized variants:

        - :py:meth:`count_files`
        - :py:meth:`count_configs`
        - :py:meth:`count_blobs`

        Usage example:

        .. code-block:: python

            from mwdblib import MWDB

            mwdb = MWDB()

            # Count samples tagged as evil and with size less than 100kB
            result = mwdb.count_files("tag:evil AND file.size:[0 TO 100000]")

        :param query: Query in Lucene syntax
        :type query: str, optional
        :rtype: int
        :raises: requests.exceptions.HTTPError
        """
        return self._count(MWDBObject, query)

    def count_files(self, query: Optional[str] = None) -> int:
        """
        Returns number of files matching provided query in Lucene syntax.

        :param query: Query in Lucene syntax
        :type query: str, optional
        :rtype: int
        :raises: requests.exceptions.HTTPError
        """
        return self._count(MWDBFile, query)

    def count_configs(self, query: Optional[str] = None) -> int:
        """
        Returns number of configs matching provided query in Lucene syntax.

        :param query: Query in Lucene syntax
        :type query: str, optional
        :rtype: int
        :raises: requests.exceptions.HTTPError
        """
        return self._count(MWDBConfig, query)

    def count_blobs(self, query: Optional[str] = None) -> int:
        """
        Returns number of blobs matching provided query in Lucene syntax.

        :param query: Query in Lucene syntax
        :type query: str, optional
        :rtype: int
        :raises: requests.exceptions.HTTPError
        """
        return self._count(MWDBBlob, query)

    def _upload_params(
        self,
        parent: Optional[Union[MWDBObject, str]],
        metakeys: Optional[Dict[str, Union[str, List[str]]]],
        attributes: Optional[Dict[str, Union[Any, List[Any]]]],
        tags: Optional[List[str]],
        karton_id: Optional[str],
        karton_arguments: Optional[Dict[str, str]],
        share_with: Optional[str],
        private: bool,
        public: bool,
    ) -> Dict[str, Any]:
        """
        Internal method that prepares and validates additional upload options
        """
        if isinstance(parent, MWDBObject):
            parent = parent.id
        if metakeys and attributes:
            raise ValueError("'attributes' and 'metakeys' must be used exclusively")

        # Use attributes if set or metakeys otherwise
        _attributes = attributes or metakeys or {}
        attributes_list = [
            {"key": key, "value": value}
            for key, value_list in _attributes.items()
            for value in (value_list if isinstance(value_list, list) else [value_list])
        ]

        _metakeys_param = {"metakeys": attributes_list} if metakeys else {}

        _attributes_param = {"attributes": attributes_list} if attributes else {}

        _tags_param = {"tags": [{"tag": tag} for tag in tags]} if tags else {}

        _karton_id_param = {"karton_id": karton_id} if karton_id else {}

        _karton_arguments_param = (
            {"karton_arguments": karton_arguments} if karton_arguments else {}
        )

        if len([arg for arg in (share_with, private, public) if arg]) > 1:
            raise ValidationError(
                "'share_with', 'private' and 'public' arguments are exclusive"
            )

        if public:
            share_with = "public"
        elif private:
            share_with = self.api.logged_user
        elif not share_with:
            share_with = "*"

        return {
            "parent": parent,
            "upload_as": share_with,
            **_tags_param,
            **_metakeys_param,
            **_attributes_param,
            **_karton_id_param,
            **_karton_arguments_param,
        }

    def upload_file(
        self,
        name: str,
        content: Union[bytes, BinaryIO],
        parent: Optional[Union[MWDBObject, str]] = None,
        metakeys: Optional[Dict[str, Union[str, List[str]]]] = None,
        attributes: Optional[Dict[str, Union[Any, List[Any]]]] = None,
        karton_id: Optional[str] = None,
        karton_arguments: Optional[Dict[str, str]] = None,
        tags: Optional[List[str]] = None,
        share_with: Optional[str] = None,
        private: bool = False,
        public: bool = False,
    ) -> MWDBFile:
        """
        Upload file object

        :param name: Original file name (see also :py:attr:`MWDBFile.file_name`)
        :type name: str
        :param content: File contents
        :type content: bytes or BinaryIO
        :param parent: Parent object or parent identifier
        :type parent: :class:`MWDBObject` or str, optional
        :param metakeys: Dictionary with string attributes
            (to be used for MWDB Core older than 2.6.0)
        :type metakeys: dict, optional
        :param attributes: Dictionary with attributes to be set after upload.
            If you want to set many values with the same key: use list as value.
            Attributes support object values that are JSON-serializable.
        :type attributes: dict, optional
        :param karton_id: Karton analysis identifier to be attached
            to the uploaded file
        :type karton_id: str, optional
        :param karton_arguments: Karton analysis arguments. Reserved for future.
        :type karton_arguments: dict, optional
        :param tags: Dictionary with tags to be set after upload.
        :type tags: list, optional
        :param share_with: Group name you want to share object with
        :type share_with: str, optional
        :param private: True if sample should be uploaded as private
        :type private: bool, optional
        :param public: True if sample should be visible for everyone
        :type public: bool, optional
        :rtype: :class:`MWDBFile`

        .. versionadded:: 4.0.0
            Added ``attributes`` and ``tags`` arguments.
            They are supported by MWDB Core >= 2.6.0, use ``metakeys``
            if your MWDB Core version is older.

        .. versionadded:: 4.1.0
            Added ``karton_id`` and ``karton_arguments`` parameters.
            Use ``karton_id`` instead of ``metakeys={"karton": "<id>"}`` if
            you use MWDB Core >= 2.3.0

        Usage example:

        .. code-block:: python

           mwdb.upload_file(
               "malware.exe",
               open("malware.exe", "rb").read(),
               parent="3629344675705286607dd0f680c66c19f7e310a1",
               public=True)
        """
        result = self.api.post(
            "file",
            files={
                "file": (name, content),
                "options": (
                    None,
                    json.dumps(
                        self._upload_params(
                            parent=parent,
                            metakeys=metakeys,
                            attributes=attributes,
                            karton_id=karton_id,
                            karton_arguments=karton_arguments,
                            tags=tags,
                            share_with=share_with,
                            private=private,
                            public=public,
                        )
                    ),
                ),
            },
        )
        return MWDBFile(self.api, result)

    def upload_config(
        self,
        family: str,
        cfg: Dict[str, Any],
        config_type: str = "static",
        parent: Optional[Union[MWDBObject, str]] = None,
        metakeys: Optional[Dict[str, Union[str, List[str]]]] = None,
        attributes: Optional[Dict[str, Union[Any, List[Any]]]] = None,
        karton_id: Optional[str] = None,
        karton_arguments: Optional[Dict[str, str]] = None,
        tags: Optional[List[str]] = None,
        share_with: Optional[str] = None,
        private: bool = False,
        public: bool = False,
    ) -> MWDBConfig:
        """
        Upload configuration object

        :param family: Malware family name (see also :py:attr:`MWDBConfig.family`)
        :type family: str
        :param cfg: Dict object with configuration (see also :py:attr:`MWDBConfig.cfg`)
        :type cfg: dict
        :param config_type: Configuration type
            (default: static, see also :py:attr:`MWDBConfig.type`)
        :type config_type: str, optional
        :param parent: Parent object or parent identifier
        :type parent: :class:`MWDBObject` or str, optional
        :param metakeys: Dictionary with string attributes
            (to be used for MWDB Core older than 2.6.0)
        :type metakeys: dict, optional
        :param attributes: Dictionary with attributes to be set after upload.
            If you want to set many values with the same key: use list as value.
            Attributes support object values that are JSON-serializable.
        :type attributes: dict, optional
        :param karton_id: Karton analysis identifier to be attached
            to the uploaded file
        :type karton_id: str, optional
        :param karton_arguments: Karton analysis arguments. Reserved for future.
        :type karton_arguments: dict, optional
        :param tags: Dictionary with tags to be set after upload.
        :type tags: list, optional
        :param share_with: Group name you want to share object with
        :type share_with: str, optional
        :param private: True if sample should be uploaded as private
        :type private: bool, optional
        :param public: True if sample should be visible for everyone
        :type public: bool, optional
        :rtype: :class:`MWDBConfig`

        .. versionadded:: 4.0.0
            Added ``attributes`` and ``tags`` arguments.
            They are supported by MWDB Core >= 2.6.0, use ``metakeys``
            if your MWDB Core version is older.

        .. versionadded:: 4.1.0
            Added ``karton_id`` and ``karton_arguments`` parameters.
            Use ``karton_id`` instead of ``metakeys={"karton": "<id>"}`` if
            you use MWDB Core >= 2.3.0

        .. code-block:: python

           mwdb.upload_config(
               "evil",
               {
                   "botnet": "mal0123",
                   "version": 2019,
                   "urls": [
                       "http://example.com",
                       "http://example.com/2"
                   ]
               }
               parent="3629344675705286607dd0f680c66c19f7e310a1",
               public=True)
        """
        params = {"family": family, "cfg": cfg, "config_type": config_type}
        params.update(
            self._upload_params(
                parent=parent,
                metakeys=metakeys,
                attributes=attributes,
                karton_id=karton_id,
                karton_arguments=karton_arguments,
                tags=tags,
                share_with=share_with,
                private=private,
                public=public,
            )
        )
        result = self.api.post("config", json=params)
        return MWDBConfig(self.api, result)

    def upload_blob(
        self,
        name: str,
        type: str,
        content: str,
        parent: Optional[Union[MWDBObject, str]] = None,
        metakeys: Optional[Dict[str, Union[str, List[str]]]] = None,
        attributes: Optional[Dict[str, Union[Any, List[Any]]]] = None,
        karton_id: Optional[str] = None,
        karton_arguments: Optional[Dict[str, str]] = None,
        tags: Optional[List[str]] = None,
        share_with: Optional[str] = None,
        private: bool = False,
        public: bool = False,
    ) -> MWDBBlob:
        """
        Upload blob object

        :param name: Blob name (see also :py:attr:`MWDBBlob.blob_name`)
        :type name: str
        :param type: Blob type (see also :py:attr:`MWDBBlob.blob_type`)
        :type type: str
        :param content: Blob content (see also :py:attr:`MWDBBlob.content`)
        :type content: str
        :param parent: Parent object or parent identifier
        :type parent: :class:`MWDBObject` or str, optional
        :param metakeys: Dictionary with string attributes
            (to be used for MWDB Core older than 2.6.0)
        :type metakeys: dict, optional
        :param attributes: Dictionary with attributes to be set after upload.
            If you want to set many values with the same key: use list as value.
            Attributes support object values that are JSON-serializable.
        :type attributes: dict, optional
        :param karton_id: Karton analysis identifier to be attached
            to the uploaded file
        :type karton_id: str, optional
        :param karton_arguments: Karton analysis arguments. Reserved for future.
        :type karton_arguments: dict, optional
        :param tags: Dictionary with tags to be set after upload.
        :type tags: list, optional
        :param share_with: Group name you want to share object with
        :type share_with: str, optional
        :param private: True if sample should be uploaded as private
        :type private: bool, optional
        :param public: True if sample should be visible for everyone
        :type public: bool, optional
        :rtype: :class:`MWDBBlob`

        .. versionadded:: 4.0.0
            Added ``attributes`` and ``tags`` arguments.
            They are supported by MWDB Core >= 2.6.0, use ``metakeys``
            if your MWDB Core version is older.

        .. versionadded:: 4.1.0
            Added ``karton_id`` and ``karton_arguments`` parameters.
            Use ``karton_id`` instead of ``metakeys={"karton": "<id>"}`` if
            you use MWDB Core >= 2.3.0
        """
        params = {"blob_name": name, "blob_type": type, "content": content}
        params.update(
            self._upload_params(
                parent=parent,
                metakeys=metakeys,
                attributes=attributes,
                karton_id=karton_id,
                karton_arguments=karton_arguments,
                tags=tags,
                share_with=share_with,
                private=private,
                public=public,
            )
        )
        result = self.api.post("blob", json=params)
        return MWDBBlob(self.api, result)
