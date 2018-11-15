import ConfigParser
import unittest
import endpoints
import re
import urllib
import sys
import time

from google.appengine.ext import testbed
from oauth_adapter import OauthAdapter


class OauthAdapterTestCase(unittest.TestCase):

    def setUp(self):
        super(OauthAdapterTestCase, self).setUp()

        self.tb = testbed.Testbed()
        self.tb.activate()
        self.tb.init_memcache_stub()
        self.tb.init_urlfetch_stub()

        self.url_prefix_regex = "^http(s)?:\/\/[a-z0-9_\-]+(\.[a-z0-9_\-]+)+"
        config = ConfigParser.ConfigParser()
        config.read("config.ini")
        self.oauth_adapters = {}
        for section in config.sections():
            if section != "sam":
                client_id = config.get(section, 'CLIENT_ID')
                client_secret = config.get(section, 'CLIENT_SECRET')
                open_id_config_url = config.get(section, 'OPEN_ID_CONFIG_URL')
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
            print("Please enter the \"code\" parameter from the resulting URL: ")
            sys.stdout.flush()
            auth_code = sys.stdin.readline().strip()
            authz = oauth_adapter.exchange_authz_code(auth_code, redirect_uri)

            self.assertEqual("Bearer", authz["token_type"], "Token type should be \"Bearer\" for provider: " + provider)
            self.assertTrue(authz["refresh_token"], "Missing refresh_token for provider: " + provider)
            self.assertTrue(authz["access_token"], "Missing access_token for provider: " + provider)
            self.assertTrue(authz["id_token"], "Missing id_token for provider: " + provider)
            self.assertIs(type(authz["expires_in"]), int)
            self.assertGreater(authz["expires_in"], 0)
            self.assertIs(type(authz["expires_at"]), float)
            self.assertGreater(authz["expires_at"], 0)
            calculated_expiry = time.time() + authz["expires_in"]
            self.assertAlmostEqual(authz["expires_at"], calculated_expiry, delta=60)
