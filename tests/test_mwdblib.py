import unittest


class TestPublicApi(unittest.TestCase):
    def test_public_api(self):
        """
        This imports are a part of the public API and should never be removed
        """
        from mwdblib import MWDB  # noqa
        from mwdblib import APIClient # noqa
        from mwdblib import MWDBFile  # noqa
        from mwdblib import MWDBObject  # noqa
        from mwdblib import MWDBConfig  # noqa
        from mwdblib import MWDBBlob  # noqa
