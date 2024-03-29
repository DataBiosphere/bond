import base64
import json
import unittest
import urllib.parse

import requests
import os
from automation.helpers.user_credentials import UserCredentials
from jsonschema import validate
from automation.helpers.json_responses import *


class BaseApiTestCase(unittest.TestCase):
    env = os.getenv("ENV", "dev")
    bond_base_url = os.getenv("BOND_BASE_URL", "https://bond-fiab.dsde-%s.broadinstitute.org:31443" % env)
    provider = "fence"
    email_domain = "quality.firecloud.org" if (env == "qa") else "test.firecloud.org"

    def assertCorrectResponseHeaders(self, response):
        self.assertEqual(response.headers["Content-Type"], "application/json")
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response.headers["X-Frame-Options"], "deny")
        self.assertEqual(response.headers["Strict-Transport-Security"], "max-age=63072000; includeSubDomains; preload")
        self.assertEqual(response.headers["Cache-Control"], "max-age=0, must-revalidate, no-cache, no-store, private")


class PublicApiTestCase(BaseApiTestCase):
    """Tests Bond APIs that are publicly available and do not require a bearer token"""

    def test_status(self):
        url = self.bond_base_url + "/api/status/v1/status"
        r = requests.get(url)
        self.assertEqual(200, r.status_code)
        response_json_dict = json.loads(r.text)
        validate(instance=response_json_dict, schema=json_schema_test_status)
        self.assertCorrectResponseHeaders(r)

    def test_list_providers(self):
        url = self.bond_base_url + "/api/link/v1/providers"
        r = requests.get(url)
        self.assertEqual(200, r.status_code)
        response_json_dict = json.loads(r.text)
        validate(instance=response_json_dict, schema=json_schema_test_list_providers)
        self.assertCorrectResponseHeaders(r)

    def test_get_swagger_ui(self):
        url = self.bond_base_url + "/api/docs"
        r = requests.get(url)
        self.assertEqual(200, r.status_code)

    def test_get_nonexistant_url(self):
        url = self.bond_base_url + "/not/a/url/that/exists"
        r = requests.get(url)
        self.assertEqual(404, r.status_code)
        self.assertCorrectResponseHeaders(r)


class CronApiTestCase(BaseApiTestCase):
    """Tests Bond APIs that are for GAE cron use."""
    CRON_HEADER = {"X-Appengine-Cron": "true"}

    def test_clear_cache_with_cron_header(self):
        url = self.bond_base_url + "/api/link/v1/clear-expired-cache-datastore-entries"
        r = requests.get(url, headers=CronApiTestCase.CRON_HEADER)
        self.assertEqual(204, r.status_code)

    def test_clear_cache_without_cron_header(self):
        url = self.bond_base_url + "/api/link/v1/clear-expired-cache-datastore-entries"
        r = requests.get(url, headers={})
        self.assertEqual(403, r.status_code)
        response_json_dict = json.loads(r.text)
        self.assertEqual("Missing required cron header.", response_json_dict["error"]["message"])


class AuthorizedBaseCase(BaseApiTestCase):
    """
    Provides UserCredentials objects for obtaining OAuth2 Access Tokens that we can use as bearer tokens during
    tests.
    """
    hermione_email = "hermione.owner@%s" % BaseApiTestCase.email_domain
    harry_email = "harry.potter@%s" % BaseApiTestCase.email_domain
    path_to_key_file = "automation/firecloud-account.json"
    user_credentials = {hermione_email: UserCredentials(hermione_email, path_to_key_file),
                        harry_email: UserCredentials(harry_email, path_to_key_file)}

    @staticmethod
    def link(token):
        url = BaseApiTestCase.bond_base_url + "/api/link/v1/" + BaseApiTestCase.provider + "/oauthcode?oauthcode=IgnoredByMockProvider&redirect_uri=http%3A%2F%2Flocal.broadinstitute.org%2F%23fence-callback"
        return requests.post(url, headers=AuthorizedBaseCase.bearer_token_header(token))

    @staticmethod
    def unlink(token):
        url = BaseApiTestCase.bond_base_url + "/api/link/v1/" + BaseApiTestCase.provider
        return requests.delete(url, headers=AuthorizedBaseCase.bearer_token_header(token))

    @staticmethod
    def unlink_all(self):
        for credential in list(self.user_credentials.values()):
            token = credential.get_access_token()
            r = self.unlink(token)
            self.assertIn(r.status_code, [204, 400])

    @staticmethod
    def bearer_token_header(token):
        return {"Authorization": "Bearer %s" % token}


class AuthorizedUnlinkedUser(AuthorizedBaseCase):
    """Base class for setting up test cases that need the user to be logged in but not linked in Bond"""

    # {"foo":"bar"}
    foo_bar_state = "eyJmb28iOiJiYXIifQ%3D%3D"

    def setUp(self):
        self.token = self.user_credentials[self.hermione_email].get_access_token()
        self.unlink(self.token)

    def get_state_with_nonce(self):
        authz_url = self.bond_base_url + "/api/link/v1/" + self.provider + "/authorization-url?scopes=openid&scopes=google_credentials&redirect_uri=http%3A%2F%2Flocal.broadinstitute.org%2F%23fence-callback"
        authz_url_response = requests.get(authz_url, headers=self.bearer_token_header(self.token))
        authz_url_with_state = json.loads(authz_url_response.text)['url']
        query_params_dict = urllib.parse.parse_qs(urllib.parse.urlparse(authz_url_with_state).query)
        return query_params_dict['state'][0]


class AuthorizationUrlApiTestCase(AuthorizedUnlinkedUser):
    """Tests Bond's authorization-url endpoints that now require a bearer token"""

    def test_get_auth_url(self):
        url = self.bond_base_url + "/api/link/v1/" + self.provider + "/authorization-url" + "?scopes=openid&scopes=google_credentials&redirect_uri=http%3A%2F%2Flocal.broadinstitute.org%2F%23fence-callback&state=" + self.foo_bar_state
        r = requests.get(url, headers=self.bearer_token_header(self.token))
        self.assertEqual(200, r.status_code)
        response_json_dict = json.loads(r.text)
        validate(instance=response_json_dict, schema=json_schema_test_get_auth_url)
        self.assertCorrectResponseHeaders(r)

    def test_get_auth_url_without_params(self):
        url = self.bond_base_url + "/api/link/v1/" + self.provider + "/authorization-url"
        r = requests.get(url, headers=self.bearer_token_header(self.token))
        self.assertEqual(400, r.status_code)
        response_json_dict = json.loads(r.text)
        validate(instance=response_json_dict, schema=json_schema_test_get_auth_url_without_params)
        self.assertCorrectResponseHeaders(r)

    def test_get_auth_url_with_only_redirect_param(self):
        url = self.bond_base_url + "/api/link/v1/" + self.provider + "/authorization-url" + "?redirect_uri=http%3A%2F%2Flocal.broadinstitute.org%2F%23fence-callback"
        r = requests.get(url, headers=self.bearer_token_header(self.token))
        self.assertEqual(200, r.status_code)
        response_json_dict = json.loads(r.text)
        validate(instance=response_json_dict, schema=json_schema_test_get_auth_url_with_only_redirect_param)
        self.assertCorrectResponseHeaders(r)


class UnlinkedUserTestCase(AuthorizedUnlinkedUser):
    """Tests APIs that require a bearer token, but the users' accounts are NOT linked in Bond"""

    def test_delete_link_for_unlinked_user(self):
        r = self.unlink(self.token)
        self.assertEqual(204, r.status_code)
        self.assertEqual("NO CONTENT", r.reason)  # Delete call returns an empty body

    def test_get_link_status_for_unlinked_user(self):
        url = self.bond_base_url + "/api/link/v1/" + self.provider
        r = requests.get(url, headers=self.bearer_token_header(self.token))
        self.assertEqual(404, r.status_code)
        response_json_dict = json.loads(r.text)
        validate(instance=response_json_dict, schema=json_schema_test_get_link_status_for_unlinked_user)
        self.assertCorrectResponseHeaders(r)

    def test_get_link_status_for_invalid_provider(self):
        url = self.bond_base_url + "/api/link/v1/" + "does_not_exist"
        r = requests.get(url, headers=self.bearer_token_header(self.token))
        self.assertEqual(404, r.status_code)
        response_json_dict = json.loads(r.text)
        validate(instance=response_json_dict, schema=json_schema_test_get_link_status_for_invalid_provider)
        self.assertCorrectResponseHeaders(r)

    def test_get_access_token_for_unlinked_user(self):
        url = self.bond_base_url + "/api/link/v1/" + self.provider + "/accesstoken"
        r = requests.get(url, headers=self.bearer_token_header(self.token))
        self.assertEqual(404, r.status_code)
        response_json_dict = json.loads(r.text)
        validate(instance=response_json_dict, schema=json_schema_test_get_access_token_for_unlinked_user)
        self.assertCorrectResponseHeaders(r)


class ExchangeAuthCodeTestCase(AuthorizedUnlinkedUser):
    """Tests the Exchange Auth Code API"""

    def test_exchange_auth_code(self):
        state = self.get_state_with_nonce()
        url = self.bond_base_url + "/api/link/v1/" + self.provider + "/oauthcode?oauthcode=IgnoredByMockProvider&redirect_uri=http%3A%2F%2Flocal.broadinstitute.org%2F%23fence-callback&state=" + state
        r = requests.post(url, headers=self.bearer_token_header(self.token))
        self.assertEqual(200, r.status_code, "Response code was not 200.  Response Body: %s" % r.text)
        response_json_dict = json.loads(r.text)
        validate(instance=response_json_dict, schema=json_schema_test_exchange_auth_code)
        self.assertCorrectResponseHeaders(r)


class ExchangeAuthCodeNegativeTestCase(AuthorizedUnlinkedUser):
    """
    Negative test cases that avoids setUp and tearDown that links and unlinks users.
    The process of linking and unlinking slows things down, so these tests are extracted to be on their own.

    Note:  We cannot test an "invalid" oauthcode in these tests because the mock provider does not verification of the
    oauthcode, it only checks that it is present.
    """
    def test_exchange_auth_code_without_authz_header(self):
        url = self.bond_base_url + "/api/link/v1/" + self.provider + "/oauthcode?oauthcode=IgnoredByMockProvider&redirect_uri=http%3A%2F%2Flocal.broadinstitute.org%2F%23fence-callback&state=" + self.foo_bar_state
        r = requests.post(url)
        self.assertEqual(401, r.status_code)
        response_json_dict = json.loads(r.text)
        validate(instance=response_json_dict, schema=json_schema_test_exchange_auth_code_without_authz_header)
        self.assertCorrectResponseHeaders(r)

    def test_exchange_auth_code_without_redirect_uri_param(self):
        url = self.bond_base_url + "/api/link/v1/" + self.provider + "/oauthcode?oauthcode=IgnoredByMockProvider&state=" + self.foo_bar_state
        r = requests.post(url, headers=self.bearer_token_header(self.token))
        self.assertEqual(400, r.status_code)
        response_json_dict = json.loads(r.text)
        validate(instance=response_json_dict, schema=json_schema_test_exchange_auth_code_without_redirect_uri_param)
        self.assertCorrectResponseHeaders(r)

    def test_exchange_auth_code_without_oauthcode_param(self):
        url = self.bond_base_url + "/api/link/v1/" + self.provider + "/oauthcode?redirect_uri=http%3A%2F%2Flocal.broadinstitute.org%2F%23fence-callback&state=" + self.foo_bar_state
        r = requests.post(url, headers=self.bearer_token_header(self.token))
        self.assertEqual(400, r.status_code)
        response_json_dict = json.loads(r.text)
        validate(instance=response_json_dict, schema=json_schema_test_exchange_auth_code_without_oauthcode_param)
        self.assertCorrectResponseHeaders(r)

    def test_exchange_auth_code_without_state_param(self):
        url = self.bond_base_url + "/api/link/v1/" + self.provider + "/oauthcode?oauthcode=IgnoredByMockProvider&redirect_uri=http%3A%2F%2Flocal.broadinstitute.org%2F%23fence-callback"
        r = requests.post(url, headers=self.bearer_token_header(self.token))
        self.assertEqual(400, r.status_code)
        response_json_dict = json.loads(r.text)
        validate(instance=response_json_dict, schema=json_schema_test_exchange_auth_code_without_oauthcode_param)
        self.assertCorrectResponseHeaders(r)

    def test_exchange_auth_code_with_wrong_state_param(self):
        self.get_state_with_nonce()
        different_state = json.dumps({'nonce': 'different_nonce_than_saved'}).encode('utf-8')
        b64_different_state = base64.b64encode(different_state)
        url_encoded_different_state = urllib.parse.quote(b64_different_state)
        url = self.bond_base_url + "/api/link/v1/" + self.provider + "/oauthcode?oauthcode=IgnoredByMockProvider&redirect_uri=http%3A%2F%2Flocal.broadinstitute.org%2F%23fence-callback&state=" + url_encoded_different_state
        r = requests.post(url, headers=self.bearer_token_header(self.token))
        self.assertEqual(500, r.status_code)
        response_json_dict = json.loads(r.text)
        validate(instance=response_json_dict, schema=json_schema_test_exchange_auth_code_invalid_nonce_param)
        self.assertCorrectResponseHeaders(r)


class LinkedUserTestCase(AuthorizedBaseCase):
    """Tests that require the user account to be linked as a precondition to the test"""

    @classmethod
    def setUpClass(cls):
        cls.token = cls.user_credentials[cls.hermione_email].get_access_token()
        cls.link(cls.token)

    @classmethod
    def tearDownClass(cls):
        cls.unlink(cls.token)

    # The lack of a fence testing environment (See: https://broadworkbench.atlassian.net/browse/CA-303) is preventing
    #  4 test cases from running as integration tests - the 3 below as well as test_exchange_auth_code. We are running
    #  these tests against mocks due to this.
    def test_get_link_status(self):
        url = self.bond_base_url + "/api/link/v1/" + self.provider
        r = requests.get(url, headers=self.bearer_token_header(LinkedUserTestCase.token))
        self.assertEqual(200, r.status_code, "Response code was not 200.  Response Body: %s" % r.text)
        response_json_dict = json.loads(r.text)
        validate(instance=response_json_dict, schema=json_schema_test_get_link_status)
        self.assertCorrectResponseHeaders(r)


    def test_get_access_token(self):
        url = self.bond_base_url + "/api/link/v1/" + self.provider + "/accesstoken"
        r = requests.get(url, headers=self.bearer_token_header(LinkedUserTestCase.token))
        self.assertEqual(200, r.status_code, "Response code was not 200.  Response Body: %s" % r.text)
        response_json_dict = json.loads(r.text)
        validate(instance=response_json_dict, schema=json_schema_test_get_access_token)
        self.assertCorrectResponseHeaders(r)

    def test_get_serviceaccount_key(self):
        url = self.bond_base_url + "/api/link/v1/" + self.provider + "/serviceaccount/key"
        r = requests.get(url, headers=self.bearer_token_header(LinkedUserTestCase.token))
        self.assertEqual(200, r.status_code, "Response code was not 200.  Response Body: %s" % r.text)
        response_json_dict = json.loads(r.text)
        validate(instance=response_json_dict, schema=json_schema_test_get_serviceaccount_key)
        self.assertCorrectResponseHeaders(r)

    def test_get_serviceaccount_accesstoken(self):
        url = self.bond_base_url + "/api/link/v1/" + self.provider + "/serviceaccount/accesstoken"
        r = requests.get(url, headers=self.bearer_token_header(LinkedUserTestCase.token))
        self.assertEqual(200, r.status_code, "Response code was not 200.  Response Body: %s" % r.text)
        response_json_dict = json.loads(r.text)
        validate(instance=response_json_dict, schema=json_schema_test_get_serviceaccount_accesstoken)
        self.assertCorrectResponseHeaders(r)


class UnlinkLinkedUserTestCase(AuthorizedBaseCase):
    """Tests the unlink functionality when a user is already linked"""

    def setUp(self):
        self.token = self.user_credentials[self.hermione_email].get_access_token()
        self.link(self.token)

    def test_delete_link_for_linked_user(self):
        r = self.unlink(self.token)
        self.assertEqual(204, r.status_code)
        self.assertEqual("NO CONTENT", r.reason)  # Delete call returns an empty body

    def test_delete_link_for_invalid_provider(self):
        url = BaseApiTestCase.bond_base_url + "/api/link/v1/" + "some-made-up-provider"
        r = requests.delete(url, headers=AuthorizedBaseCase.bearer_token_header(self.token))
        self.assertEqual(404, r.status_code)
        response_json_dict = json.loads(r.text)
        validate(instance=response_json_dict, schema=json_schema_test_delete_link_for_invalid_provider)
        self.assertCorrectResponseHeaders(r)


class UserCredentialsTestCase(AuthorizedBaseCase):
    """
    Tests to confirm that we're able to use the provided service account key to assume generate access tokens for
    test users
    """
    def setUp(self):
        self.token = UserCredentials(AuthorizedBaseCase.hermione_email, "automation/firecloud-account.json").get_access_token()

    def test_token(self):
        self.assertGreaterEqual(len(self.token), 100)
        self.assertIn("ya29.", self.token)

    def test_user_info_for_delegated_user(self):
        r = requests.get("https://www.googleapis.com/oauth2/v1/userinfo?alt=json",
                         headers=self.bearer_token_header(self.token))
        response_json_dict = json.loads(r.text)
        validate(instance=response_json_dict, schema=json_schema_test_user_info_for_delegated_user)
