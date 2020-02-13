import unittest

from tests.unit.fake_cache_api import FakeCacheApi
from mock import MagicMock
from werkzeug import exceptions

from bond_app.open_id_config import OpenIdConfig


class OpenIdConfigTestCase(unittest.TestCase):

    def setUp(self):
        self.url_prefix_regex = "^http(s)?:\/\/[a-z0-9_\-]+(\.[a-z0-9_\-]+)+"
        fake_config = {"token_endpoint": "https://fake.domain/user/oauth2/token",
                       "revocation_endpoint": "",
                       "scopes_supported": ["foo", "bar"]}
        self.provider = "fake_provider"
        self.open_id_config = OpenIdConfig(self.provider, "not-a-real-url", FakeCacheApi())
        self.open_id_config.load_dict = MagicMock(return_value=fake_config)

    def test_get_config(self):
        open_id_config = self.open_id_config.load_dict()
        self.assertIsNotNone(open_id_config)

    def test_get_value(self):
        key = "scopes_supported"
        self.assertIsNotNone(self.open_id_config.get_config_value(key))

    def test_get_open_id_config_value_missing(self):
        with self.assertRaises(exceptions.InternalServerError):
            self.open_id_config.get_config_value("something-that-does-not-exist")

    def test_get_open_id_config_value_missing_no_exception(self):
        self.assertIsNone(self.open_id_config.get_config_value("something-that-does-not-exist", False))

    def test_get_token_info_url(self):
        token_info_url = self.open_id_config.get_token_info_url()
        self.assertRegex(token_info_url, self.url_prefix_regex)

    def test_get_revoke_url(self):
        url_regex = "^http(s)?:\/\/.+?revoke"
        self.assertRegex(self.open_id_config.get_revoke_url(), url_regex)
