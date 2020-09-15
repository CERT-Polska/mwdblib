import unittest


class TestPublicApi(unittest.TestCase):
    def test_public_api(self):
        """
        This imports are a part of the public API and should never be removed
        """
        from src import MWDB  # noqa
        from src import APIClient # noqa
        from src import MWDBFile  # noqa
        from src import MWDBObject  # noqa
        from src import MWDBConfig  # noqa
        from src import MWDBBlob  # noqa
