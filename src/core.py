import getpass
import json
import time
import warnings

from .api import APIClient
from .exc import ObjectNotFoundError, ValidationError
from .object import MWDBObject
from .file import MWDBFile
from .config import MWDBConfig
from .blob import MWDBBlob

try:
    import __builtin__
    user_input = getattr(__builtin__, "raw_input")
except ImportError:
    user_input = input


class MWDB(object):
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

    Usage example:

    .. code-block:: python

       from mwdblib import MWDB

       mwdb = MWDB()
       mwdb.login("example", "<password>")

       file = mwdb.query_file("3629344675705286607dd0f680c66c19f7e310a1")

    """

    def __init__(self, api=None, **api_options):
        self.api = api or APIClient(**api_options)

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

    def _recent(self, object_type, query=None):
        try:
            last_object = None
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
                    yield last_object
        except ObjectNotFoundError:
            return

    def recent_objects(self):
        """
        Retrieves recently uploaded objects
        If you already know type of object you are looking for, use specialized variants:

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

    def recent_files(self):
        """
        Retrieves recently uploaded files

        :rtype: Iterator[:class:`MWDBFile`]
        :raises: requests.exceptions.HTTPError
        """
        return self._recent(MWDBFile)

    def recent_configs(self):
        """
        Retrieves recently uploaded configuration objects

        :rtype: Iterator[:class:`MWDBConfig`]
        :raises: requests.exceptions.HTTPError
        """
        return self._recent(MWDBConfig)

    def recent_blobs(self):
        """
        Retrieves recently uploaded blob objects

        :rtype: Iterator[:class:`MWDBBlob`]
        :raises: requests.exceptions.HTTPError
        """
        return self._recent(MWDBBlob)

    def _listen(self, last_object, object_type, blocking=True, interval=15, query=None):
        if last_object is None:
            last_object = next(self._recent(object_type, query=query), None)
            # If there are no elements (even first element): just get new samples from now on
        elif isinstance(last_object, MWDBObject):
            # If we are requesting for typed objects, we should additionally check the object type
            if object_type is not MWDBObject and not isinstance(last_object, object_type):
                raise TypeError("latest_object type must be 'str' or '{}'".format(object_type.__name__))
            # If object instance provided: get ID from instance
        else:
            # If not: first check whether object exists in repository
            last_object = self._query(object_type, last_object, raise_not_found=True)

        while True:
            objects = []
            for obj in self._recent(object_type, query=query):
                if last_object:
                    if obj.id == last_object.id:
                        break

                    if obj.upload_time < last_object.upload_time:
                        raise RuntimeError(
                            "Newly fetched object [{}] is older than the pivot [{}]".format(
                                obj.id, last_object.id
                            )
                        )
                objects.append(obj)

            # Return fetched objects in reversed order (from oldest to latest)
            for obj in objects[::-1]:
                last_object = obj
                yield obj
            if blocking:
                time.sleep(interval)
            else:
                break

    def listen_for_objects(self, last_object=None, **kwargs):
        """
        Listens for recent objects and yields newly added.

        In blocking mode (default) if last_object is provided: the method fetches the latest objects until
        the provided object is reached and yields new objects from the oldest one. Otherwise, the method periodically
        asks for recent objects until a new object appears. The default request interval is 15 seconds.

        In a non-blocking mode: a generator stops if there are no more objects to fetch.

        last_object argument accepts both identifier and MWDBObject instance. If the object identifier is
        provided: method firstly checks whether the object exists in repository and has the correct type.

        If you already know type of object you are looking for, use specialized variants:

        - :py:meth:`listen_for_files`
        - :py:meth:`listen_for_configs`
        - :py:meth:`listen_for_blobs`

        .. warning::
            Make sure that last_object is valid in MWDB instance. If you provide MWDBObject that doesn't
            exist, mwdblib will iterate over all objects and you can quickly hit your rate limit. Library is trying to
            protect you from that as much as possible by checking type and object existence, but it's still possible to
            do something unusual.

            Additionally, if using the ``query`` parameter and passing the ``last_object`` pivot, make sure
            that the passed object actually matches the query criteria. Otherwise the mechanism that catches faulty
            pivots will signal that there's something wrong and raise an exception.

        .. versionadded:: 3.2.0
            Added listen_for_* methods

        .. versionadded:: 3.4.0
            Added query parameter

        .. versionadded:: 3.4.0
            The listen_for_* methods will now try to prevent you from iterating over the whole database by
            throwing an exception if they detect that there is something wrong with the pivot object

        :param last_object: MWDBObject instance or object hash
        :type last_object: MWDBObject or str
        :param blocking: Enable blocking mode (default)
        :type blocking: bool, optional
        :param interval: Interval for periodic queries in blocking mode (default is 15 seconds)
        :type interval: int, optional
        :param query: Lucene query to be used for listening for only specific objects
        :type query: str, optional
        :rtype: Iterator[:class:`MWDBObject`]
        """
        return self._listen(last_object,
                            object_type=MWDBObject,
                            **kwargs)

    def listen_for_files(self, last_object=None, **kwargs):
        """
        Listens for recent files and yields newly added.

        .. seealso::
            More details can be found here: :meth:`listen_for_objects`

        .. versionadded:: 3.2.0
            Added listen_for_* methods

        .. versionadded:: 3.4.0
            Added query parameter

        .. versionadded:: 3.4.0
            The listen_for_* methods will now try to prevent you from iterating over the whole database by
            throwing an exception if they detect that there is something wrong with the pivot object

        :param last_object: MWDBFile instance or object hash
        :type last_object: MWDBFile or str
        :param blocking: Enable blocking mode (default)
        :type blocking: bool, optional
        :param interval: Interval for periodic queries in blocking mode (default is 15 seconds)
        :type interval: int, optional
        :param query: Lucene query to be used for listening for only specific files
        :type query: str, optional
        :rtype: Iterator[:class:`MWDBFile`]
        """
        return self._listen(last_object,
                            object_type=MWDBFile,
                            **kwargs)

    def listen_for_configs(self, last_object=None, **kwargs):
        """
        Listens for recent configs and yields newly added.

        .. seealso::
            More details can be found here: :meth:`listen_for_objects`

        .. versionadded:: 3.2.0
            Added listen_for_* methods

        .. versionadded:: 3.4.0
            Added query parameter

        .. versionadded:: 3.4.0
            The listen_for_* methods will now try to prevent you from iterating over the whole database by
            throwing an exception if they detect that there is something wrong with the pivot object

        :param last_object: MWDBConfig instance or object hash
        :type last_object: MWDBConfig or str
        :param blocking: Enable blocking mode (default)
        :type blocking: bool, optional
        :param interval: Interval for periodic queries in blocking mode (default is 15 seconds)
        :type interval: int, optional
        :param query: Lucene query to be used for listening for only specific configs
        :type query: str, optional
        :rtype: Iterator[:class:`MWDBConfig`]
        """
        return self._listen(last_object,
                            object_type=MWDBConfig,
                            **kwargs)

    def listen_for_blobs(self, last_object=None, **kwargs):
        """
        Listens for recent blobs and yields newly added.

        .. seealso::
            More details can be found here: :meth:`listen_for_objects`

        .. versionadded:: 3.2.0
            Added listen_for_* methods

        .. versionadded:: 3.4.0
            Added query parameter

        .. versionadded:: 3.4.0
            The listen_for_* methods will now try to prevent you from iterating over the whole database by
            throwing an exception if they detect that there is something wrong with the pivot object

        :param last_object: MWDBBlob instance or object hash
        :type last_object: MWDBBlob or str
        :param blocking: Enable blocking mode (default)
        :type blocking: bool, optional
        :param interval: Interval for periodic queries in blocking mode (default is 15 seconds)
        :type interval: int, optional
        :param query: Lucene query to be used for listening for only specific blobs
        :type query: str, optional
        :rtype: Iterator[:class:`MWDBBlob`]
        """
        return self._listen(last_object,
                            object_type=MWDBBlob,
                            **kwargs)

    def _query(self, object_type, hash, raise_not_found):
        try:
            url_pattern = object_type.URL_TYPE + "/{id}"
            result = self.api.get(url_pattern.format(id=hash))
            return object_type.create(self.api, result)
        except ObjectNotFoundError:
            if not raise_not_found:
                return None
            else:
                raise

    def query(self, hash, raise_not_found=True):
        """
        Queries for object using provided hash.
        If you already know type of object you are looking for, use specialized variants:

        - :py:meth:`query_file`
        - :py:meth:`query_config`
        - :py:meth:`query_blob`

        .. versionadded:: 2.4.0
           Added raise_not_found optional argument

        .. versionchanged:: 3.0.0
           Fallback to :py:meth:`query_file` if other hash than SHA256 was provided

        :param hash: Object hash (identifier, MD5, SHA-1, SHA-2)
        :type hash: str
        :param raise_not_found: If True (default), method raises HTTPError when object is not found
        :type raise_not_found: bool, optional
        :rtype: :class:`MWDBObject` or None (if raise_not_found=False)
        :raises: requests.exceptions.HTTPError
        """
        if len(hash) != 64:
            # If different hash than SHA256 was provided
            return self.query_file(hash, raise_not_found=raise_not_found)
        return self._query(MWDBObject, hash, raise_not_found)

    def query_file(self, hash, raise_not_found=True):
        """
        Queries for file using provided hash

        :param hash: Object hash (identifier, MD5, SHA-1, SHA-2)
        :type hash: str
        :param raise_not_found: If True (default), method raises HTTPError when object is not found
        :type raise_not_found: bool
        :rtype: :class:`MWDBFile` or None (if raise_not_found=False)
        :raises: requests.exceptions.HTTPError
        """
        return self._query(MWDBFile, hash, raise_not_found)

    def query_config(self, hash, raise_not_found=True):
        """
        Queries for configuration object using provided hash

        :param hash: Object hash (SHA-256 identifier)
        :type hash: str
        :param raise_not_found: If True (default), method raises HTTPError when object is not found
        :type raise_not_found: bool
        :rtype: :class:`MWDBConfig` or None (if raise_not_found=False)
        :raises: requests.exceptions.HTTPError
        """
        return self._query(MWDBConfig, hash, raise_not_found)

    def query_blob(self, hash, raise_not_found=True):
        """
        Queries for blob object using provided hash

        :param hash: Object hash (SHA-256 identifier)
        :type hash: str
        :param raise_not_found: If True (default), method raises HTTPError when object is not found
        :type raise_not_found: bool
        :rtype: :class:`MWDBBlob` or None (if raise_not_found=False)
        :raises: requests.exceptions.HTTPError
        """
        return self._query(MWDBBlob, hash, raise_not_found)

    def search(self, query):
        """
        Advanced search for objects using Lucene syntax.
        If you already know type of objects you are looking for, use specialized variants:

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

    def search_files(self, query):
        """
        Advanced search for files using Lucene syntax.

        :param query: Search query
        :type query: str
        :rtype: Iterator[:class:`MWDBFile`]
        :raises: requests.exceptions.HTTPError
        """
        return self._recent(MWDBFile, query)

    def search_configs(self, query):
        """
        Advanced search for configuration objects using Lucene syntax.

        :param query: Search query
        :type query: str
        :rtype: Iterator[:class:`MWDBConfig`]
        :raises: requests.exceptions.HTTPError
        """
        return self._recent(MWDBConfig, query)

    def search_blobs(self, query):
        """
        Advanced search for blob objects using Lucene syntax.

        :param query: Search query
        :type query: str
        :rtype: Iterator[:class:`MWDBBlob`]
        :raises: requests.exceptions.HTTPError
        """
        return self._recent(MWDBBlob, query)

    def _count(self, object_type, query=None):
        params = {'query': query}
        result = self.api.get(object_type.URL_TYPE + '/count', params=params)
        return result["count"]

    def count(self, query=None):
        """
        Returns number of objects matching provided query in Lucene syntax.
        If you already know type of objects you want to count, use specialized variants:

        - :py:meth:`count_files`
        - :py:meth:`count_configs`
        - :py:meth:`count_blobs`

        Usage example:

        .. code-block:: python

            from mwdblib import Malwarecage

            # Count samples tagged as evil and with size less than 100kB
            result = mwdb.count_files("tag:evil AND file.size:[0 TO 100000]")

        :param query: Query in Lucene syntax
        :type query: str, optional
        :rtype: int
        :raises: requests.exceptions.HTTPError
        """
        return self._count(MWDBObject, query)

    def count_files(self, query=None):
        """
        Returns number of files matching provided query in Lucene syntax.

        :param query: Query in Lucene syntax
        :type query: str, optional
        :rtype: int
        :raises: requests.exceptions.HTTPError
        """
        return self._count(MWDBFile, query)

    def count_configs(self, query=None):
        """
        Returns number of configs matching provided query in Lucene syntax.

        :param query: Query in Lucene syntax
        :type query: str, optional
        :rtype: int
        :raises: requests.exceptions.HTTPError
        """
        return self._count(MWDBConfig, query)

    def count_blobs(self, query=None):
        """
        Returns number of blobs matching provided query in Lucene syntax.

        :param query: Query in Lucene syntax
        :type query: str, optional
        :rtype: int
        :raises: requests.exceptions.HTTPError
        """
        return self._count(MWDBBlob, query)

    @staticmethod
    def _convert_bytes(data):
        if isinstance(data, dict):
            return dict(map(MWDB._convert_bytes, data.items()))

        if isinstance(data, bytes):
            return data.decode('utf-8', 'replace')

        if isinstance(data, (tuple, list)):
            return list(map(MWDB._convert_bytes, data))

        return data

    def _upload_params(self, parent=None, metakeys=None,
                       share_with=None, private=False, public=False):
        if isinstance(parent, MWDBObject):
            parent = parent.id

        metakeys = metakeys or []

        if isinstance(metakeys, dict):
            metakeys = [{"key": key, "value": value}
                        for key, value_list in metakeys.items()
                        for value in (value_list if isinstance(value_list, list) else [value_list])]

        if len([arg for arg in (share_with, private, public) if arg]) > 1:
            raise ValidationError("'share_with', 'private' and 'public' arguments are exclusive")

        if public:
            share_with = "public"
        elif private:
            share_with = self.api.logged_user
        elif not share_with:
            share_with = "*"

        return {
            'parent': parent,
            'metakeys': metakeys,
            'upload_as': share_with
        }

    def upload_file(self, name, content, **kwargs):
        """
        Upload file object

        :param name: Original file name (see also :py:attr:`MWDBFile.file_name`)
        :type name: str
        :param content: File contents
        :type content: bytes
        :param parent: Parent object or parent identifier
        :type parent: :class:`MWDBObject` or str, optional
        :param metakeys: Dictionary with metakeys.
            If you want to set many values with the same key: use list as value
        :type metakeys: dict, optional
        :param share_with: Group name you want to share object with
        :type share_with: str, optional
        :param private: True if sample should be uploaded as private
        :type private: bool, optional
        :param public: True if sample should be visible for everyone
        :type public: bool, optional
        :rtype: :class:`MWDBFile`
        :raises: :class:`requests.exceptions.HTTPError`, :class:`ValueError`

        Usage example:

        .. code-block:: python

           mwdb.upload_file(
               "malware.exe",
               open("malware.exe", "rb").read(),
               parent="3629344675705286607dd0f680c66c19f7e310a1",
               public=True)
        """
        result = self.api.post("file", files={
            'file': (name, content),
            'options': (None, json.dumps(self._upload_params(**kwargs)))
        })
        return MWDBFile(self.api, result)

    def upload_config(self, family, cfg, config_type="static", **kwargs):
        """
        Upload configuration object

        :param family: Malware family name (see also :py:attr:`MWDBConfig.family`)
        :type family: str
        :param cfg: Dict object with configuration (see also :py:attr:`MWDBConfig.cfg`)
        :type cfg: dict
        :param config_type: Configuration type (default: static, see also :py:attr:`MWDBConfig.type`)
        :type config_type: str, optional
        :param parent: Parent object or parent identifier
        :type parent: :class:`MWDBObject` or str, optional
        :param metakeys: Dictionary with metakeys.
            If you want to set many values with the same key: use list as value
        :type metakeys: dict, optional
        :param share_with: Group name you want to share object with
        :type share_with: str, optional
        :param private: True if sample should be uploaded as private
        :type private: bool, optional
        :param public: True if sample should be visible for everyone
        :type public: bool, optional
        :rtype: :class:`MWDBConfig`
        :raises: :class:`requests.exceptions.HTTPError`, :class:`ValueError`

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
        params = {
            "family": family,
            "cfg": cfg,
            "config_type": config_type
        }
        params.update(self._upload_params(**kwargs))
        result = self.api.post("config", json=params)
        return MWDBConfig(self.api, result)

    def upload_blob(self, name, type, content, **kwargs):
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
        :param metakeys: Dictionary with metakeys.
            If you want to set many values with the same key: use list as value
        :type metakeys: dict, optional
        :param share_with: Group name you want to share object with
        :type share_with: str, optional
        :param private: True if sample should be uploaded as private
        :type private: bool, optional
        :param public: True if sample should be visible for everyone
        :type public: bool, optional
        :rtype: :class:`MWDBBlob`
        :raises: :class:`requests.exceptions.HTTPError`, :class:`ValueError`
        """
        params = {
            "blob_name": name,
            "blob_type": type,
            "content": content
        }
        params.update(self._upload_params(**kwargs))
        result = self.api.post("blob", json=params)
        return MWDBBlob(self.api, result)


# Backwards compatibility
Malwarecage = MWDB
