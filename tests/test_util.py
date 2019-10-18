import unittest
from src import config_dhash


class TestPublicApi(unittest.TestCase):
    def test_dhash(self):
        config = {
            "type": "emotet_spam",
            "urls": [
                {"cnc": "23.253.207.142", "port": 8080},
                {"cnc": "185.187.198.4", "port": 8080},
                {"cnc": "46.228.205.245", "port": 4143},
            ],
            "hdr_const": 355370982,
        }

        self.assertEquals(
            config_dhash(config),
            "f16fbc9c2a977daed84a5cc5e36c5bbf4bf0da044d3bf1cb367bdb05ff915c70",
        )
