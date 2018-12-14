import itertools
import json

import requests

from .api import MalwarecageAPI
from .obj import MalwarecageObject
from .file import MalwarecageFile
from .config import MalwarecageConfig
from .blob import MalwarecageBlob


class Malwarecage(object):
    def __init__(self, api=None):
        self.api = api or MalwarecageAPI()

    def login(self, username, password):
        result = self.api.post("auth/login", json={
            "login": username,
            "password": password
        }, noauth=True)
        self.api.set_api_key(result["token"])

    def recent_files(self):
        try:
            for page in itertools.count(start=1):
                result = self.api.get("file", params={"page": page})
                if "files" not in result or len(result["files"]) == 0:
                    return
                for file in result["files"]:
                    yield MalwarecageFile(self.api, file)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code >= 500:
                raise e

    def recent_configs(self):
        try:
            for page in itertools.count(start=1):
                result = self.api.get("config", params={"page": page})
                if "configs" not in result or len(result["configs"]) == 0:
                    return
                for file in result["configs"]:
                    yield MalwarecageConfig(self.api, file)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code >= 500:
                raise e

    def query_file(self, hash):
        result = self.api.get("file/{}".format(hash))
        return MalwarecageFile(self.api, result)

    def query_config(self, hash):
        result = self.api.get("config/{}".format(hash))
        return MalwarecageConfig(self.api, result)

    def search(self, query):
        result = self.api.post("search", json={"query": query})
        for file in result:
            yield MalwarecageObject.create(self.api, file)

    def upload_file(self, name, content, parent=None, metakeys=None):
        parent = parent or "root"
        result = self.api.post("file/{}".format(parent), data={
            'metakeys': json.dumps({'metakeys': metakeys or []})
        }, files={'file': (name, content)})
        return MalwarecageFile(self.api, result)

    def upload_config(self, family, cfg, parent=None):
        parent = parent or "root"
        result = self.api.put("config/{}".format(parent), json={
            "family": family,
            "cfg": cfg
        })
        return MalwarecageConfig(self.api, result)

    def upload_blob(self, name, type, content, parent=None):
        parent = parent or "root"
        result = self.api.put("blob/{}".format(parent), json={
            "blob_name": name,
            "blob_type": type,
            "content": content
        })
        return MalwarecageBlob(self.api, result)
