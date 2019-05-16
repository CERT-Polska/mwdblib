import getpass
import itertools
import json

import requests

from .api import MalwarecageAPI
from .object import MalwarecageObject
from .file import MalwarecageFile
from .config import MalwarecageConfig
from .blob import MalwarecageBlob

try:
    import __builtin__
    user_input = getattr(__builtin__, "raw_input")
except ImportError:
    user_input = input


class Malwarecage(object):
    """
    Main object used for communication with Malwarecage

    :param api: Custom :class:`MalwarecageAPI` used to communicate with Malwarecage
    :type api: :class:`MalwarecageAPI`, optional
    :param api_key: API key used for authentication (omit if password-based authentication is used)
    :type api_key: str, optional

    Usage example:

    .. code-block:: python

       from mwdblib import Malwarecage

       mwdb = Malwarecage()
       mwdb.login("example", "<password>")

       file = mwdb.query_file("3629344675705286607dd0f680c66c19f7e310a1")

    """

    def __init__(self, api=None, api_key=None):
        self.api = api or MalwarecageAPI(api_key=api_key)

    def login(self, username=None, password=None):
        """
        Performs user authentication using provided username and password.

        .. warning::

           Keep in mind that password-authenticated sessions are short lived, so password needs to be stored
           in :class:`MalwarecageAPI` object. Ask Malwarecage instance administrator for an API key (or send e-mail to
           info@cert.pl if you use mwdb.cert.pl)

        .. versionadded:: 2.4.0
           Malwarecage tries to reauthenticate on first Unauthorized exception

        .. versionadded:: 2.5.0
           username and password arguments are optional. If one of the credentials is not provided via arguments,
           user will be asked for it.

        :param username: User name
        :type username: str
        :param password: Password
        :type password: str
        :raises: requests.exceptions.HTTPError
        """
        if username is None:
            # Py2 compatibility
            username = user_input("Username: ")
        if password is None:
            password = getpass.getpass("Password: ")
        self.api.login(username, password)

    def _recent(self, endpoint, query=None):
        try:
            for page in itertools.count(start=1):
                params = {"page": page}
                if query is not None:
                    params["query"] = query
                result = self.api.get(endpoint, params=params)
                key = endpoint+"s"
                if key not in result or len(result[key]) == 0:
                    return
                for obj in result[key]:
                    yield MalwarecageObject.create(self.api, obj)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code >= 500:
                raise e

    def recent_objects(self):
        """
        Retrieves recently uploaded objects
        If you already know type of object you are looking for, use specialized variants:

        - :py:meth:`recent_files`
        - :py:meth:`recent_configs`
        - :py:meth:`recent_blobs`

        Usage example:

        .. code-block:: python

            from mwdblib import Malwarecage
            from itertools import islice

            mwdb = Malwarecage()
            mwdb.login("admin", "password123")

            # recent_files is generator, do not execute list(recent_files)!
            files = islice(mwdb.recent_files(), 25)
            print([(f.name, f.tags) for f in files])

        :rtype: Iterator[:class:`MalwarecageObject`]
        :raises: requests.exceptions.HTTPError
        """
        return self._recent("object")

    def recent_files(self):
        """
        Retrieves recently uploaded files

        :rtype: Iterator[:class:`MalwarecageFile`]
        :raises: requests.exceptions.HTTPError
        """
        return self._recent("file")

    def recent_configs(self):
        """
        Retrieves recently uploaded configuration objects

        :rtype: Iterator[:class:`MalwarecageConfig`]
        :raises: requests.exceptions.HTTPError
        """
        return self._recent("config")

    def recent_blobs(self):
        """
        Retrieves recently uploaded blob objects

        :rtype: Iterator[:class:`MalwarecageBlob`]
        :raises: requests.exceptions.HTTPError
        """
        return self._recent("blob")

    def _query(self, object_type, hash, raise_not_found):
        try:
            result = self.api.get(object_type.URL_PATTERN.format(id=hash))
            return object_type.create(self.api, result)
        except requests.exceptions.HTTPError as e:
            if not raise_not_found and e.response.status_code == requests.codes.not_found:
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

        :param hash: Object hash (identifier, MD5, SHA-1, SHA-2)
        :type hash: str
        :param raise_not_found: If True (default), method raises HTTPError when object is not found
        :type raise_not_found: bool, optional
        :rtype: :class:`MalwarecageObject` or None (if raise_not_found=False)
        :raises: requests.exceptions.HTTPError
        """
        return self._query(MalwarecageObject, hash, raise_not_found)

    def query_file(self, hash, raise_not_found=True):
        """
        Queries for file using provided hash

        :param hash: Object hash (identifier, MD5, SHA-1, SHA-2)
        :type hash: str
        :param raise_not_found: If True (default), method raises HTTPError when object is not found
        :type raise_not_found: bool
        :rtype: :class:`MalwarecageFile` or None (if raise_not_found=False)
        :raises: requests.exceptions.HTTPError
        """
        return self._query(MalwarecageFile, hash, raise_not_found)

    def query_config(self, hash, raise_not_found=True):
        """
        Queries for configuration object using provided hash

        :param hash: Object hash (SHA-256 identifier)
        :type hash: str
        :param raise_not_found: If True (default), method raises HTTPError when object is not found
        :type raise_not_found: bool
        :rtype: :class:`MalwarecageConfig` or None (if raise_not_found=False)
        :raises: requests.exceptions.HTTPError
        """
        return self._query(MalwarecageConfig, hash, raise_not_found)

    def query_blob(self, hash, raise_not_found=True):
        """
        Queries for blob object using provided hash

        :param hash: Object hash (SHA-256 identifier)
        :type hash: str
        :param raise_not_found: If True (default), method raises HTTPError when object is not found
        :type raise_not_found: bool
        :rtype: :class:`MalwarecageBlob` or None (if raise_not_found=False)
        :raises: requests.exceptions.HTTPError
        """
        return self._query(MalwarecageBlob, hash, raise_not_found)

    def search(self, query):
        """
        Advanced search for objects using Lucene syntax.
        If you already know type of object you are looking for, use specialized variants:

        - :py:meth:`search_files`
        - :py:meth:`search_configs`
        - :py:meth:`search_blobs`

        Usage example:

        .. code-block:: python

            from mwdblib import Malwarecage

            # Search for samples tagged as evil and with size less than 100kB
            results = mwdb.search_files("tag:evil AND file.size:[0 TO 100000]")

        :param query: Search query
        :type query: str
        :rtype: Iterator[:class:`MalwarecageObject`]
        :raises: requests.exceptions.HTTPError
        """
        result = self.api.post("search", json={"query": query})
        for file in result:
            yield MalwarecageObject.create(self.api, file)

    def search_files(self, query):
        """
        Advanced search for files using Lucene syntax.

        :param query: Search query
        :type query: str
        :rtype: Iterator[:class:`MalwarecageFile`]
        :raises: requests.exceptions.HTTPError
        """
        return self._recent("file", query)

    def search_configs(self, query):
        """
        Advanced search for configuration objects using Lucene syntax.

        :param query: Search query
        :type query: str
        :rtype: Iterator[:class:`MalwarecageConfig`]
        :raises: requests.exceptions.HTTPError
        """
        return self._recent("config", query)

    def search_blobs(self, query):
        """
        Advanced search for blob objects using Lucene syntax.

        :param query: Search query
        :type query: str
        :rtype: Iterator[:class:`MalwarecageBlob`]
        :raises: requests.exceptions.HTTPError
        """
        return self._recent("blob", query)

    @staticmethod
    def _convert_bytes(data):
        if isinstance(data, dict):
            return dict(map(Malwarecage._convert_bytes, data.items()))

        if isinstance(data, bytes):
            return data.decode('utf-8', 'replace')

        if isinstance(data, (tuple, list)):
            return list(map(Malwarecage._convert_bytes, data))

        return data

    def _upload(self, type, parent=None, metakeys=None,
                share_with=None, private=False, public=False,
                req_files=None, req_json=None):
        parent = parent or "root"

        if isinstance(parent, MalwarecageObject):
            parent = parent.id

        metakeys = metakeys or []
        req_files = req_files or {}
        req_json = req_json or {}

        if isinstance(metakeys, dict):
            metakeys = [{"key": key, "value": value}
                        for key, value_list in metakeys.items()
                        for value in (value_list if isinstance(value_list, list) else [value_list])]

        if private and public:
            raise ValueError("Sample can't be both private and public")
        if public:
            share_with = "public"
        if private:
            share_with = self.api.logged_user()

        result = self.api.post("{}/{}".format(type, parent), data={
            'metakeys': json.dumps({'metakeys': metakeys}),
            'upload_as': share_with or "*"
        }, files=req_files, json=self._convert_bytes(req_json))
        return result

    def upload_file(self, name, content, **kwargs):
        """
        Upload file object

        :param name: Original file name (see also :py:attr:`MalwarecageFile.file_name`)
        :type name: str
        :param content: File contents
        :type content: bytes
        :param parent: Parent object or parent identifier
        :type parent: :class:`MalwarecageObject` or str, optional
        :param metakeys: Dictionary with metakeys.
            If you want to set many values with the same key: use list as value
        :type metakeys: dict, optional
        :param share_with: Group name you want to share object with
        :type share_with: str, optional
        :param private: True if sample should be uploaded as private
        :type private: bool, optional
        :param public: True if sample should be visible for everyone
        :type public: bool, optional
        :rtype: :class:`MalwarecageFile`
        :raises: :class:`requests.exceptions.HTTPError`, :class:`ValueError`

        Usage example:

        .. code-block:: python

           mwdb.upload_file(
               "malware.exe",
               open("malware.exe", "rb").read(),
               parent="3629344675705286607dd0f680c66c19f7e310a1",
               public=True)
        """
        result = self._upload("file", req_files={'file': (name, content)}, **kwargs)
        return MalwarecageFile(self.api, result)

    def upload_config(self, family, cfg, config_type="static", **kwargs):
        """
        Upload configuration object

        :param family: Malware family name (see also :py:attr:`MalwarecageConfig.family`)
        :type family: str
        :param cfg: Dict object with configuration (see also :py:attr:`MalwarecageConfig.cfg`)
        :type cfg: dict
        :param config_type: Configuration type (default: static, see also :py:attr:`MalwarecageConfig.type`)
        :type config_type: str, optional
        :param parent: Parent object or parent identifier
        :type parent: :class:`MalwarecageObject` or str, optional
        :param metakeys: Dictionary with metakeys.
            If you want to set many values with the same key: use list as value
        :type metakeys: dict, optional
        :param share_with: Group name you want to share object with
        :type share_with: str, optional
        :param private: True if sample should be uploaded as private
        :type private: bool, optional
        :param public: True if sample should be visible for everyone
        :type public: bool, optional
        :rtype: :class:`MalwarecageConfig`
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
        result = self._upload("config", req_json={
            "family": family,
            "cfg": cfg,
            "config_type": config_type
        }, **kwargs)
        return MalwarecageConfig(self.api, result)

    def upload_blob(self, name, type, content, **kwargs):
        """
        Upload blob object

        :param name: Blob name (see also :py:attr:`MalwarecageBlob.blob_name`)
        :type name: str
        :param type: Blob type (see also :py:attr:`MalwarecageBlob.blob_type`)
        :type type: str
        :param content: Blob content (see also :py:attr:`MalwarecageBlob.content`)
        :type content: str
        :param parent: Parent object or parent identifier
        :type parent: :class:`MalwarecageObject` or str, optional
        :param metakeys: Dictionary with metakeys.
            If you want to set many values with the same key: use list as value
        :type metakeys: dict, optional
        :param share_with: Group name you want to share object with
        :type share_with: str, optional
        :param private: True if sample should be uploaded as private
        :type private: bool, optional
        :param public: True if sample should be visible for everyone
        :type public: bool, optional
        :rtype: :class:`MalwarecageBlob`
        :raises: :class:`requests.exceptions.HTTPError`, :class:`ValueError`
        """
        result = self._upload("blob", req_json={
            "blob_name": name,
            "blob_type": type,
            "content": content
        }, **kwargs)
        return MalwarecageBlob(self.api, result)
