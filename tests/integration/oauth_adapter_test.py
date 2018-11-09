import ConfigParser
import unittest
import endpoints

from google.appengine.ext import testbed
from oauth_adapter import OauthAdapter


class OauthAdapterTestCase(unittest.TestCase):

    def setUp(self):
        super(OauthAdapterTestCase, self).setUp()
        self.tb = testbed.Testbed()
        self.tb.activate()
        self.tb.init_memcache_stub()
        self.tb.init_urlfetch_stub()
        config = ConfigParser.ConfigParser()
        config.read("config.ini")
        self.provider = "fence"
        self.client_id = config.get(self.provider, 'CLIENT_ID')
        self.client_secret = config.get(self.provider, 'CLIENT_SECRET')
        self.open_id_config_url = config.get(self.provider, 'OPEN_ID_CONFIG_URL')
        self.oauth_adapter = OauthAdapter(self.client_id, self.client_secret, self.open_id_config_url, self.provider)

    def tearDown(self):
        self.tb.deactivate()
        super(OauthAdapterTestCase, self).tearDown()

    def test_get_open_id_config(self):
        open_id_config = self.oauth_adapter._get_open_id_config()
        self.assertIsNotNone(open_id_config)

    def test_get_open_id_config_value(self):
        key = "scopes_supported"
        self.assertTrue(len(self.oauth_adapter._get_open_id_config_value(key)),
                        "Expected key \"" + key + "\" to be a non-empty array")

    def test_get_open_id_config_value_missing(self):
        with self.assertRaises(endpoints.InternalServerErrorException):
            self.oauth_adapter._get_open_id_config_value("something-that-does-not-exist")

    def test_get_open_id_config_value_missing_no_exception(self):
        self.assertIsNone(self.oauth_adapter._get_open_id_config_value("something-that-does-not-exist", False))

    def test_get_token_info_url(self):
        self.assertRegexpMatches(self.oauth_adapter._get_token_info_url(), "^http(s)?:\/\/[a-z0-9]+(\.[a-z0-9]+)+")

    def test_get_revoke_url(self):
        self.assertRegexpMatches(self.oauth_adapter._get_revoke_url(), "^http(s)?:\/\/.+?revoke")
