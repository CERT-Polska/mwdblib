import itertools
import json

import requests

from .api import MalwarecageAPI
from .object import MalwarecageObject
from .file import MalwarecageFile
from .config import MalwarecageConfig
from .blob import MalwarecageBlob


class Malwarecage(object):
    def __init__(self, api=None):
        self.api = api or MalwarecageAPI()

    def login(self, username, password):
        """
        Performs user authentication using provided username and password.
        If you want to authenticate using API key - initialize Malwarecage object with MalwarecageAPI instance

        :param username: User name
        :param password: Password
        :raises: requests.exceptions.HTTPError
        """
        result = self.api.post("auth/login", json={
            "login": username,
            "password": password
        }, noauth=True)
        self.api.set_api_key(result["token"])

    def _recent(self, endpoint, query=None):
        try:
            for page in itertools.count(start=1):
                params = {"page": page}
                if query is not None:
                    params["query"] = query
                result = self.api.get(endpoint, params={"page": page})
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
        If you already know type of object you are looking for - use specialized variants:
        - recent_files
        - recent_configs
        - recent_blobs

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

    def query(self, hash):
        """
        Queries for object using provided hash.
        If you already know type of object you are looking for - use specialized variants:
        - query_file
        - query_config
        - query_blob

        :param hash: Object hash (identifier, MD5, SHA-1, SHA-2)
        :rtype: :class:`MalwarecageObject`
        :raises: requests.exceptions.HTTPError
        """
        result = self.api.get("object/{}".format(hash))
        return MalwarecageObject.create(self.api, result)

    def query_file(self, hash):
        """
        Queries for file using provided hash

        :param hash: Object hash (identifier, MD5, SHA-1, SHA-2)
        :rtype: :class:`MalwarecageFile`
        :raises: requests.exceptions.HTTPError
        """
        result = self.api.get("file/{}".format(hash))
        return MalwarecageFile(self.api, result)

    def query_config(self, hash):
        """
        Queries for configuration object using provided hash

        :param hash: Object hash (identifier, MD5, SHA-1, SHA-2)
        :rtype: :class:`MalwarecageConfig`
        :raises: requests.exceptions.HTTPError
        """
        result = self.api.get("config/{}".format(hash))
        return MalwarecageConfig(self.api, result)

    def query_blob(self, hash):
        """
        Queries for blob object using provided hash

        :param hash: Object hash (identifier, MD5, SHA-1, SHA-2)
        :rtype: :class:`MalwarecageConfig`
        :raises: requests.exceptions.HTTPError
        """
        result = self.api.get("blob/{}".format(hash))
        return MalwarecageBlob(self.api, result)

    def search(self, query):
        """
        Advanced search for objects using Lucene syntax.
        If you already know type of object you are looking for - use specialized variants:
        - search_files
        - search_configs
        - search_blobs

        :param query: Search query
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
        :rtype: Iterator[:class:`MalwarecageFile`]
        :raises: requests.exceptions.HTTPError
        """
        return self._recent("file", query)

    def search_configs(self, query):
        """
        Advanced search for configuration objects using Lucene syntax.

        :param query: Search query
        :rtype: Iterator[:class:`MalwarecageConfig`]
        :raises: requests.exceptions.HTTPError
        """
        return self._recent("config", query)

    def search_blobs(self, query):
        """
        Advanced search for blob objects using Lucene syntax.

        :param query: Search query
        :rtype: Iterator[:class:`MalwarecageBlob`]
        :raises: requests.exceptions.HTTPError
        """
        return self._recent("blob", query)

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
                        for key, value_list in metakeys.iteritems()
                        for value in (value_list if isinstance(value_list, list) else [value_list])]

        if public:
            share_with = "public"
        if private:
            share_with = self.api.logged_user()

        result = self.api.post("{}/{}".format(type, parent), data={
            'metakeys': json.dumps({'metakeys': metakeys}),
            'upload_as': share_with or "*"
        }, files=req_files, json=req_json)
        return result

    def upload_file(self, name, content, **kwargs):
        """
        Upload file object

        :param name: Original file name
        :param content: File contents
        :param parent: (optional) Parent object or parent identifier
        :param metakeys: (optional) Dictionary with metakeys.
            If you want to set many values with the same key: use list
        :param share_with: (optional) Group name you want to share object with
        :param private: (optional) True if sample should be uploaded as private
        :param public: (optional) True if sample should be visible for everyone
        :rtype: :class:`MalwarecageFile`
        :raises: requests.exceptions.HTTPError
        """
        result = self._upload("file", req_files={'file': (name, content)}, **kwargs)
        return MalwarecageFile(self.api, result)

    def upload_config(self, family, cfg, **kwargs):
        """
        Upload configuration object

        :param family: Malware family name
        :param cfg: Dict object with configuration
        :param parent: (optional) Parent object or parent identifier
        :param metakeys: (optional) Dictionary with metakeys.
            If you want to set many values with the same key: use list
        :param share_with: (optional) Group name you want to share object with
        :param private: (optional) True if sample should be uploaded as private
        :param public: (optional) True if sample should be visible for everyone
        :rtype: :class:`MalwarecageConfig`
        :raises: requests.exceptions.HTTPError
        """
        result = self._upload("config", req_json={
            "family": family,
            "cfg": cfg
        }, **kwargs)
        return MalwarecageConfig(self.api, result)

    def upload_blob(self, name, type, content, **kwargs):
        """
        Upload blob object

        :param name: Blob name
        :param type: Blob type
        :param content: Blob content
        :param cfg: Dict object with configuration
        :param parent: (optional) Parent object or parent identifier
        :param metakeys: (optional) Dictionary with metakeys.
            If you want to set many values with the same key: use list
        :param share_with: (optional) Group name you want to share object with
        :param private: (optional) True if sample should be uploaded as private
        :param public: (optional) True if sample should be visible for everyone
        :rtype: :class:`MalwarecageBlob`
        :raises: requests.exceptions.HTTPError
        """
        result = self._upload("blob", req_json={
            "blob_name": name,
            "blob_type": type,
            "content": content
        }, **kwargs)
        return MalwarecageBlob(self.api, result)
