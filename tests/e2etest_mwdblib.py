import os
from src import Malwarecage
import unittest
from itertools import islice
from tests.request_counter import RequestsCounter


class TestE2E(unittest.TestCase):
    def get_mwdb(self):
        username = os.environ["MWDB_USER"]
        password = os.environ["MWDB_PASS"]

        mwdb = Malwarecage()
        mwdb.login(username, password)
        return mwdb

    def test_login(self):
        with RequestsCounter(1):
            self.get_mwdb()

    def read_common(self, obj):
        obj.id
        obj.sha256
        obj.tags
        # obj.metakeys - not allowed
        obj.comments
        obj.upload_time
        obj.parents
        obj.children

    def test_lazy_load(self):
        mwdb = self.get_mwdb()
        for obj in islice(mwdb.recent_objects(), 10):
            with RequestsCounter(0):
                obj.id
                obj.sha256
                obj.tags
                obj.upload_time
            with RequestsCounter(1):
                obj.parents
                obj.children
            with RequestsCounter(1):
                obj.comments

    def test_recent_objects(self):
        mwdb = self.get_mwdb()
        for obj in islice(mwdb.recent_objects(), 10):
            with RequestsCounter(2):
                self.read_common(obj)

    def test_recentfiles(self):
        mwdb = self.get_mwdb()
        for obj in islice(mwdb.recent_files(), 10):
            with RequestsCounter(2):
                self.read_common(obj)
            with RequestsCounter(0):
                obj.md5
                obj.sha1
                obj.sha256
                obj.sha512
                obj.crc32
                obj.ssdeep
                obj.file_name
                obj.file_size
                obj.file_type
                obj.name
                obj.size
                obj.type
            with RequestsCounter(2):
                obj.download()

    def test_recentconfigs(self):
        mwdb = self.get_mwdb()
        for obj in islice(mwdb.recent_configs(), 10):
            with RequestsCounter(2):
                self.read_common(obj)
            with RequestsCounter(0):
                obj.family
                obj.cfg

    def test_recentblobs(self):
        mwdb = self.get_mwdb()
        for obj in islice(mwdb.recent_blobs(), 10):
            with RequestsCounter(2):
                self.read_common(obj)
            with RequestsCounter(0):
                obj.blob_name
                obj.blob_size
                obj.blob_type
                obj.name
                obj.size
                obj.type
                obj.content
                obj.last_seen
