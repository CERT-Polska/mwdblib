import unittest


class TestPublicApi(unittest.TestCase):
    def test_public_api(self):
        """
        This imports are a part of the public API and should never be removed
        """
        from src import Malwarecage  # noqa
        from src import MalwarecageAPI  # noqa
        from src import MalwarecageFile  # noqa
        from src import MalwarecageObject  # noqa
        from src import MalwarecageConfig  # noqa
        from src import MalwarecageBlob  # noqa
