import collections
import json
import unittest
import requests
import urlparse
import os
from automation.helpers.user_credentials import UserCredentials
from jsonschema import validate
from automation.helpers.json_responses import *

class BaseApiTestCase(unittest.TestCase):
    env = os.getenv("ENV", "dev")
    # bond_base_url = "https://bond-fiab.dsde-%s.broadinstitute.org:31443" % env
    bond_base_url = "http://localhost:8080"
    provider = "fence"
    email_domain = "quality.firecloud.org" if (env == "qa") else "test.firecloud.org"


class PublicApiTestCase(BaseApiTestCase):
    """Tests Bond APIs that are publicly available and do not require a bearer token"""

    def test_status(self):
        url = self.bond_base_url + "/api/status/v1/status"
        r = requests.get(url)
        self.assertEqual(200, r.status_code)
        response_json_dict = json.loads(r.text)  # sorted??
        self.assertTrue(response_json_dict['ok'])
        validate(instance=response_json_dict, schema=json_schema_test_list_providers)

    def test_list_providers(self):
        url = self.bond_base_url + "/api/link/v1/providers"
        r = requests.get(url)
        self.assertEqual(200, r.status_code)
        providers = json.loads(r.text)
        self.assertIsNotNone(providers["providers"])
        validate(instance=providers, schema=json_schema_test_status)

    def test_get_auth_url(self):
        expected_json = {u'url': u'https://staging.datastage.io/user/oauth2/authorize?response_type=code&client_id=4EmZnWKVMoPyhdJMh7EB8SSl3Uojo20QfsAR77gu&redirect_uri=http%3A%2F%2Flocal.broadinstitute.org%2F%23fence-callback&scope=openid+google_credentials&state=eyJmb28iPSJiYXIifQ%3D%3D&idp=fence'}
        url = self.bond_base_url + "/api/link/v1/" + self.provider + "/authorization-url" + "?scopes=openid&scopes=google_credentials&redirect_uri=http%3A%2F%2Flocal.broadinstitute.org%2F%23fence-callback&state=eyJmb28iPSJiYXIifQ=="
        r = requests.get(url)
        self.assertEqual(200, r.status_code)
        response = json.loads(r.text)
        authz_url = urlparse.urlparse(response["url"])
        query_params = urlparse.parse_qs(authz_url.query)
        self.assertEqual("https", authz_url.scheme)
        self.assertIsNotNone(authz_url.netloc)
        self.assertIsNotNone(query_params["redirect_uri"])
        self.assertIsNotNone(query_params["response_type"])
        self.assertIsNotNone(query_params["client_id"])
        self.assertIsNotNone(query_params["state"])
        assert response == expected_json
        self.assertDictEqual(response, expected_json)

    def test_get_auth_url_without_params(self):
        expected_json = {u'url': u'https://staging.datastage.io/user/oauth2/authorize?response_type=code&client_id=4EmZnWKVMoPyhdJMh7EB8SSl3Uojo20QfsAR77gu&redirect_uri=http%3A%2F%2Flocal.broadinstitute.org%2F%23fence-callback&state=FfuEMeu4yIyUlk3RhrhjYMaWF84rQR&idp=fence'}
        url = self.bond_base_url + "/api/link/v1/" + self.provider + "/authorization-url"
        r = requests.get(url)
        self.assertEqual(400, r.status_code)
        response = json.loads(r.text)
        self.assertDictEqual(response, expected_json)

    def test_get_auth_url_with_only_redirect_param(self):
        expected_json = {u'url': u'https://staging.datastage.io/user/oauth2/authorize?response_type=code&client_id=4EmZnWKVMoPyhdJMh7EB8SSl3Uojo20QfsAR77gu&redirect_uri=http%3A%2F%2Flocal.broadinstitute.org%2F%23fence-callback&state=tyM3PomDKtGPAHYUHs0FJooIorBZ3N&idp=fence'}
        url = self.bond_base_url + "/api/link/v1/" + self.provider + "/authorization-url" + "?redirect_uri=http%3A%2F%2Flocal.broadinstitute.org%2F%23fence-callback"
        r = requests.get(url)
        self.assertEqual(200, r.status_code)
        response = json.loads(r.text)
        authz_url = urlparse.urlparse(response["url"])
        query_params = urlparse.parse_qs(authz_url.query)
        self.assertIsNotNone(query_params["redirect_uri"])
        self.assertIsNotNone(query_params["response_type"])
        self.assertIsNotNone(query_params["client_id"])
        self.assertIsNotNone(query_params["state"])
        self.assertDictEqual(response, expected_json)


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
        for credential in self.user_credentials.values():
            token = credential.get_access_token()
            r = self.unlink(token)
            self.assertIn(r.status_code, [204, 400])

    @staticmethod
    def bearer_token_header(token):
        return {"Authorization": "Bearer %s" % token}


class AuthorizedUnlinkedUser(AuthorizedBaseCase):
    """Base class for setting up test cases that need the user to be logged in but not linked in Bond"""

    def setUp(self):
        self.token = self.user_credentials[self.hermione_email].get_access_token()
        self.unlink(self.token)


class UnlinkedUserTestCase(AuthorizedUnlinkedUser):
    """Tests APIs that require a bearer token, but the users' accounts are NOT linked in Bond"""

    def test_delete_link_for_unlinked_user(self):
        r = self.unlink(self.token)
        self.assertEqual(204, r.status_code)

    def test_get_link_status_for_unlinked_user(self):
        url = self.bond_base_url + "/api/link/v1/" + self.provider
        r = requests.get(url, headers=self.bearer_token_header(self.token))
        self.assertEqual(404, r.status_code)

    def test_get_link_status_for_invalid_provider(self):
        url = self.bond_base_url + "/api/link/v1/" + "does_not_exist"
        r = requests.get(url, headers=self.bearer_token_header(self.token))
        self.assertEqual(404, r.status_code)

    def test_get_access_token_for_unlinked_user(self):
        url = self.bond_base_url + "/api/link/v1/" + self.provider + "/accesstoken"
        r = requests.get(url, headers=self.bearer_token_header(self.token))
        self.assertEqual(400, r.status_code)


class ExchangeAuthCodeTestCase(AuthorizedUnlinkedUser):
    """Tests the Exchange Auth Code API"""

    def test_exchange_auth_code(self):
        url = self.bond_base_url + "/api/link/v1/" + self.provider + "/oauthcode?oauthcode=IgnoredByMockProvider&redirect_uri=http%3A%2F%2Flocal.broadinstitute.org%2F%23fence-callback"
        r = requests.post(url, headers=self.bearer_token_header(self.token))
        self.assertEqual(200, r.status_code, "Response code was not 200.  Response Body: %s" % r.text)
        response = json.loads(r.text)
        self.assertIsNotNone(response["issued_at"])
        self.assertIsNotNone(response["username"])


class ExchangeAuthCodeNegativeTestCase(AuthorizedUnlinkedUser):
    """
    Negative test cases that avoids setUp and tearDown that links and unlinks users.
    The process of linking and unlinking slows things down, so these tests are extracted to be on their own.

    Note:  We cannot test an "invalid" oauthcode in these tests because the mock provider does not verification of the
    oauthcode, it only checks that it is present.
    """
    def test_exchange_auth_code_without_authz_header(self):
        url = self.bond_base_url + "/api/link/v1/" + self.provider + "/oauthcode?oauthcode=IgnoredByMockProvider&redirect_uri=http%3A%2F%2Flocal.broadinstitute.org%2F%23fence-callback"
        r = requests.post(url)
        self.assertEqual(401, r.status_code)

    def test_exchange_auth_code_without_redirect_uri_param(self):
        url = self.bond_base_url + "/api/link/v1/" + self.provider + "/oauthcode?oauthcode=IgnoredByMockProvider"
        r = requests.post(url, headers=self.bearer_token_header(self.token))
        self.assertEqual(400, r.status_code)

    def test_exchange_auth_code_without_oauthcode_param(self):
        url = self.bond_base_url + "/api/link/v1/" + self.provider + "/oauthcode?redirect_uri=http%3A%2F%2Flocal.broadinstitute.org%2F%23fence-callback"
        r = requests.post(url, headers=self.bearer_token_header(self.token))
        self.assertEqual(400, r.status_code)


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

    def test_get_access_token(self):
        url = self.bond_base_url + "/api/link/v1/" + self.provider + "/accesstoken"
        r = requests.get(url, headers=self.bearer_token_header(LinkedUserTestCase.token))
        self.assertEqual(200, r.status_code, "Response code was not 200.  Response Body: %s" % r.text)
        response = json.loads(r.text)
        self.assertIsNotNone(response["expires_at"])
        self.assertIsNotNone(response["token"])

    def test_get_serviceaccount_key(self):
        url = self.bond_base_url + "/api/link/v1/" + self.provider + "/serviceaccount/key"
        r = requests.get(url, headers=self.bearer_token_header(LinkedUserTestCase.token))
        self.assertEqual(200, r.status_code, "Response code was not 200.  Response Body: %s" % r.text)
        response = json.loads(r.text)
        # We could assert that more elements are present here in the result, but we're basically just verifying the
        # structure of a Google Service Account Key, which is probably not something we should test here
        self.assertIsNotNone(response["data"]["private_key"])
        self.assertEqual("service_account", response["data"]["type"])


class UnlinkLinkedUserTestCase(AuthorizedBaseCase):
    """Tests the unlink functionality when a user is already linked"""

    def setUp(self):
        self.token = self.user_credentials[self.hermione_email].get_access_token()
        self.link(self.token)

    def test_delete_link_for_linked_user(self):
        r = self.unlink(self.token)
        self.assertEqual(204, r.status_code)

    def test_delete_link_for_invalid_provider(self):
        url = BaseApiTestCase.bond_base_url + "/api/link/v1/" + "some-made-up-provider"
        r = requests.delete(url, headers=AuthorizedBaseCase.bearer_token_header(self.token))
        self.assertEqual(404, r.status_code)


class UserCredentialsTestCase(AuthorizedBaseCase):
    """
    Tests to confirm that we're able to use the provided service account key to assume generate access tokens for
    test users
    """
    def setUp(self):
        self.token = UserCredentials(AuthorizedBaseCase.hermione_email, "automation/firecloud-account.json").get_access_token()

    def test_token(self):
        self.assertGreaterEqual(len(self.token), 100)

    def test_user_info_for_delegated_user(self):
        r = requests.get("https://www.googleapis.com/oauth2/v1/userinfo?alt=json",
                         headers=self.bearer_token_header(self.token))
        user_info = json.loads(r.text)
        self.assertEqual(self.hermione_email, user_info["email"])
