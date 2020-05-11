import configparser
import re
import sys
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request

from bond_app.bond import FenceKeys
from bond_app.jwt_token import JwtToken
from bond_app.oauth_adapter import OauthAdapter
from bond_app.open_id_config import OpenIdConfig
from tests.unit.fake_cache_api import FakeCacheApi


class OauthAdapterTestCase(unittest.TestCase):

    url_prefix_regex = "^http(s)?:\/\/[a-z0-9_\-]+(\.[a-z0-9_\-]+)+"
    config = None
    oauth_adapters = {}
    authz_responses = {}
    using_mock_providers = True

    @classmethod
    def setUpClass(cls):
        OauthAdapterTestCase.config = configparser.ConfigParser()
        OauthAdapterTestCase.config.read("config.ini")
        OauthAdapterTestCase.oauth_adapters = OauthAdapterTestCase.init_oauth_adapters(OauthAdapterTestCase.config)
        print("Testing %i provider(s) per test: [%s]" % (len(OauthAdapterTestCase.oauth_adapters), list(OauthAdapterTestCase.oauth_adapters)))
        OauthAdapterTestCase.authz_responses = OauthAdapterTestCase.authorize_with_providers(OauthAdapterTestCase.oauth_adapters)

    @classmethod
    def init_oauth_adapters(cls, config):
        oauth_adapters = {}
        for section in config.sections():
            if section != "sam" and section != "bond_accepted":
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
            auth_code = cls.get_auth_code(authz_url, provider, redirect_uri)
            authz_responses[provider] = oauth_adapter.exchange_authz_code(auth_code, redirect_uri)
        return authz_responses

    # If we're testing against mock providers, we don't care what the `auth_code` is that we exchange with the provider.
    # If you want to run these tests against real providers, you will need to set the `using_mock_providers` variable to
    # be `False`, which means that the test execution will require the test runner to follow the generated links to
    # log into each provider and paste the auth code into the terminal in order to complete the oauth token exchange
    # required for the tests to execute against a real provider.
    @classmethod
    def get_auth_code(cls, authz_url, provider, redirect_uri):
        return "X" if cls.using_mock_providers else cls.ask_user_for_auth_code(authz_url, provider, redirect_uri)

    @classmethod
    def ask_user_for_auth_code(cls, authz_url, provider, redirect_uri):
        print("Please go to %s to authorize access: %s" % (provider, authz_url))
        print("YOU WILL BE REDIRECTED TO %s WHICH WILL PROBABLY UNREACHABLE -- THIS IS EXPECTED!" % redirect_uri)
        print("Please copy/paste the \"code\" parameter from the resulting URL: ")
        sys.stdout.flush()
        return sys.stdin.readline().strip()

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

    # Note: Since this test revokes the refresh token, it can/will break other tests if it doesn't run last.
    # Thankfully, unittest runs tests alphabetically by default and revoke_refresh_token is alphabetically last in this
    # test suite. Yes, we are aware that this is not ideal and a bit fragile, but this whole test suite isn't ideal,
    # so we're okay with it. If you are adding a new test, you'll want to name it so it runs before this test
    @unittest.skipIf(using_mock_providers,
                     "Since the mock provider can't actually revoke refresh tokens, we won't test that it can")
    def test_revoke_refresh_token(self):
        for provider, oauth_adapter in self.oauth_adapters.items():
            refresh_token = self.authz_responses[provider][FenceKeys.REFRESH_TOKEN]
            oauth_adapter.revoke_refresh_token(refresh_token)
            with self.assertRaises(Exception):
                oauth_adapter.refresh_access_token(refresh_token)

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
