import configparser
import unittest
import re
import urllib.request, urllib.parse, urllib.error
import sys
import time

from bond_app.bond import FenceKeys
from tests.unit.fake_cache_api import FakeCacheApi
from bond_app.jwt_token import JwtToken
from bond_app.oauth_adapter import OauthAdapter
from bond_app.open_id_config import OpenIdConfig


class OauthAdapterTestCase(unittest.TestCase):

    url_prefix_regex = "^http(s)?:\/\/[a-z0-9_\-]+(\.[a-z0-9_\-]+)+"
    config = None
    oauth_adapters = {}
    authz_responses = {}

    @classmethod
    def setUpClass(cls):
        OauthAdapterTestCase.config = configparser.ConfigParser()
        OauthAdapterTestCase.config.read("config.ini")
        OauthAdapterTestCase.oauth_adapters = OauthAdapterTestCase.init_oauth_adapters(OauthAdapterTestCase.config)
        OauthAdapterTestCase.authz_responses = OauthAdapterTestCase.authorize_with_providers(OauthAdapterTestCase.oauth_adapters)

    @classmethod
    def init_oauth_adapters(cls, config):
        oauth_adapters = {}
        for section in config.sections():
            if section != "sam":
                client_id = config.get(section, 'CLIENT_ID')
                client_secret = config.get(section, 'CLIENT_SECRET')
                open_id_config_url = config.get(section, 'OPEN_ID_CONFIG_URL')
                open_id_config = OpenIdConfig(section, open_id_config_url, FakeCacheApi())
                oauth_adapters[section] = OauthAdapter(client_id, client_secret, open_id_config, section)
        return oauth_adapters

    @classmethod
    def authorize_with_providers(cls, oauth_adapters):
        scopes = ["openid", "google_credentials"]
        redirect_uri = "http://local.broadinstitute.org/#fence-callback"
        state = "abc123"
        authz_responses = {}
        for provider, oauth_adapter in oauth_adapters.items():
            authz_url = oauth_adapter.build_authz_url(scopes,
                                                      redirect_uri,
                                                      state,
                                                      extra_authz_url_params={"foo": "bar"})
            print("Please go to %s to authorize access: %s" % (provider, authz_url))
            print("YOU WILL BE REDIRECTED TO %s WHICH WILL PROBABLY UNREACHABLE -- THIS IS EXPECTED!" % redirect_uri)
            print("Please copy/paste the \"code\" parameter from the resulting URL: ")
            sys.stdout.flush()
            # auth_code = sys.stdin.readline().strip()
            auth_code = "X"
            authz_responses[provider] = oauth_adapter.exchange_authz_code(auth_code, redirect_uri)
        return authz_responses

    @staticmethod
    def param_regex(key, value):
        return "[\?&]" + re.escape(key) + "=" + re.escape(value) + "[&]?"

    def test_adapters_exist(self):
        self.assertTrue(self.oauth_adapters, "Failed to create OAuth Adapters - nothing to test")

    def test_get_open_id_config(self):
        for provider, oauth_adapter in self.oauth_adapters.items():
            open_id_config = oauth_adapter.open_id_config.load_dict()
            self.assertIsNotNone(open_id_config, "Expected open_id_config for " + provider + " to not be None")

    def test_build_authz_url(self):
        scopes = ["foo", "bar"]
        redirect_uri = "http://something.something/"
        state = "abc123"
        for provider, oauth_adapter in self.oauth_adapters.items():
            authz_url = oauth_adapter.build_authz_url(scopes, redirect_uri, state)
            msg = "For provider: " + provider
            self.assertRegex(authz_url, self.url_prefix_regex, msg)
            self.assertRegex(authz_url, self.param_regex("response_type", "code"), msg)
            self.assertRegex(authz_url, self.param_regex("scope", "+".join(scopes)), msg)
            self.assertRegex(authz_url, self.param_regex("redirect_uri", urllib.parse.quote_plus(redirect_uri)), msg)
            self.assertRegex(authz_url, self.param_regex("state", state), msg)

    def test_exchange_authz_code(self):
        # The calls to `exchange_authz_code` happen in the `setUpClass` method so that they are only called once for
        # this test suite
        for provider, authz in self.authz_responses.items():
            self.assert_token_response(authz, provider)

    def test_refresh_access_token(self):
        for provider, authz in self.authz_responses.items():
            if provider != "dcf-fence":
                oauth_adapter = self.oauth_adapters[provider]
                refresh_token = authz[FenceKeys.REFRESH_TOKEN]
                self.assert_token_response(oauth_adapter.refresh_access_token(refresh_token), provider)

    @unittest.skip("Test should be implemented.  Saving time now by not implementing so we can get mock Fence working")
    def test_revoke_refresh_token(self):
        self.assertTrue(False, "This test needs to be implemented")

    def assert_token_response(self, authz, provider):
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
