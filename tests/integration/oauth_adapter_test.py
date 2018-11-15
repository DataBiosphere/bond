import ConfigParser
import unittest
import endpoints
import re
import urllib
import sys
import time

from google.appengine.ext import testbed

from bond import FenceKeys
from jwt_token import JwtToken
from oauth_adapter import OauthAdapter


class OauthAdapterTestCase(unittest.TestCase):

    def setUp(self):
        super(OauthAdapterTestCase, self).setUp()

        self.tb = testbed.Testbed()
        self.tb.activate()
        self.tb.init_memcache_stub()
        self.tb.init_urlfetch_stub()

        self.url_prefix_regex = "^http(s)?:\/\/[a-z0-9_\-]+(\.[a-z0-9_\-]+)+"
        self.config = ConfigParser.ConfigParser()
        self.config.read("config.ini")
        self.oauth_adapters = {}
        for section in self.config.sections():
            if section != "sam":
                client_id = self.config.get(section, 'CLIENT_ID')
                client_secret = self.config.get(section, 'CLIENT_SECRET')
                open_id_config_url = self.config.get(section, 'OPEN_ID_CONFIG_URL')
                self.oauth_adapters[section] = OauthAdapter(client_id, client_secret, open_id_config_url, section)

    def tearDown(self):
        self.tb.deactivate()
        super(OauthAdapterTestCase, self).tearDown()

    @staticmethod
    def param_regex(key, value):
        return "[\?&]" + re.escape(key) + "=" + re.escape(value) + "[&]?"

    def test_get_open_id_config(self):
        for provider, oauth_adapter in self.oauth_adapters.iteritems():
            open_id_config = oauth_adapter._get_open_id_config()
            self.assertIsNotNone(open_id_config, "Expected open_id_config for " + provider + " to not be None")

    def test_get_open_id_config_value(self):
        for provider, oauth_adapter in self.oauth_adapters.iteritems():
            key = "scopes_supported"
            self.assertTrue(len(oauth_adapter._get_open_id_config_value(key)),
                            "Expected key \"" + key + "\" to be a non-empty array for provider " + provider)

    def test_get_open_id_config_value_missing(self):
        for provider, oauth_adapter in self.oauth_adapters.iteritems():
            with self.assertRaises(endpoints.InternalServerErrorException):
                oauth_adapter._get_open_id_config_value("something-that-does-not-exist")

    def test_get_open_id_config_value_missing_no_exception(self):
        for provider, oauth_adapter in self.oauth_adapters.iteritems():
            self.assertIsNone(oauth_adapter._get_open_id_config_value("something-that-does-not-exist", False))

    def test_get_token_info_url(self):
        for provider, oauth_adapter in self.oauth_adapters.iteritems():
            token_info_url = oauth_adapter._get_token_info_url()
            self.assertRegexpMatches(token_info_url, self.url_prefix_regex, "Token Info URL for provider " + provider)

    def test_get_revoke_url(self):
        url_regex = "^http(s)?:\/\/.+?revoke"
        for provider, oauth_adapter in self.oauth_adapters.iteritems():
            self.assertRegexpMatches(oauth_adapter._get_revoke_url(), url_regex, "Revoke URL for provider " + provider)

    def test_build_authz_url(self):
        scopes = ["foo", "bar"]
        redirect_uri = "http://something.something/"
        state = "abc123"
        for provider, oauth_adapter in self.oauth_adapters.iteritems():
            authz_url = oauth_adapter.build_authz_url(scopes, redirect_uri, state)
            msg = "For provider: " + provider
            self.assertRegexpMatches(authz_url, self.url_prefix_regex, msg)
            self.assertRegexpMatches(authz_url, self.param_regex("response_type", "code"), msg)
            self.assertRegexpMatches(authz_url, self.param_regex("scope", "+".join(scopes)), msg)
            self.assertRegexpMatches(authz_url, self.param_regex("redirect_uri", urllib.quote_plus(redirect_uri)), msg)
            self.assertRegexpMatches(authz_url, self.param_regex("state", state), msg)

    def test_exchange_authz_code(self):
        scopes = ['openid', 'google_credentials']
        redirect_uri = "http://local.broadinstitute.org/#fence-callback"
        state = "abc123"
        for provider, oauth_adapter in self.oauth_adapters.iteritems():
            authz_url = oauth_adapter.build_authz_url(scopes, redirect_uri, state)
            print('Please go to %s and authorize access for %s.' % (authz_url, provider))
            print("Please copy/paste the \"code\" parameter from the resulting URL: ")
            sys.stdout.flush()
            auth_code = sys.stdin.readline().strip()
            authz = oauth_adapter.exchange_authz_code(auth_code, redirect_uri)

            self.assertEqual("Bearer", authz[FenceKeys.TOKEN_TYPE], "Token type should be \"Bearer\" for provider: " + provider)
            self.assertTrue(authz[FenceKeys.REFRESH_TOKEN], "Missing refresh_token for provider: " + provider)
            self.assertTrue(authz[FenceKeys.ACCESS_TOKEN], "Missing access_token for provider: " + provider)
            self.assertTrue(authz[FenceKeys.ID_TOKEN], "Missing id_token for provider: " + provider)
            jwt_token = JwtToken(authz[FenceKeys.ID_TOKEN], self.config.get(provider, "USER_NAME_PATH_EXPR"))
            self.assertIsNotNone(jwt_token.username)
            self.assertIsNotNone(jwt_token.issued_at)
            self.assertIs(type(authz[FenceKeys.EXPIRES_IN]), int, "Value of expires_in for provider: " + provider + " should be of type: int")
            self.assertGreater(authz[FenceKeys.EXPIRES_IN], 0, "Value of expires_in for provider: " + provider + " should be greater than 0")
            self.assertIs(type(authz[FenceKeys.EXPIRES_AT]), float, "Value of expires_at for provider: " + provider + " should be of type: float")
            self.assertGreater(authz[FenceKeys.EXPIRES_AT], 0, "Value of expires_at for provider: " + provider + " should be greater than 0")
            calculated_expiry = time.time() + authz[FenceKeys.EXPIRES_IN]
            self.assertAlmostEqual(authz[FenceKeys.EXPIRES_AT], calculated_expiry, delta=60, msg="Value of expires_at for provider: " + provider + " should be an epoch time in seconds that is within 60 seconds of the current time plus the value of the expires_in field")
