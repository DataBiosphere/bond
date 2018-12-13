import json
import unittest
import requests
import urlparse
from automation.helpers.user_credentials import UserCredentials


class BaseApiTestCase(unittest.TestCase):
    bond_base_url = "https://bond-fiab.dsde-dev.broadinstitute.org:31443"
    provider = "fence"


class PublicApiTestCase(BaseApiTestCase):
    """Tests Bond APIs that are publicly available and do not require a bearer token"""

    def test_status(self):
        r = requests.get(self.bond_base_url + "/api/status/v1/status")
        self.assertEqual(200, r.status_code)
        status = json.loads(r.text)
        self.assertTrue(status['ok'])

    def test_list_providers(self):
        url = self.bond_base_url + "/api/link/v1/providers"
        r = requests.get(url)
        self.assertEqual(200, r.status_code)
        providers = json.loads(r.text)
        self.assertIsNotNone(providers["providers"])

    def test_get_auth_url(self):
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

    def test_get_auth_url_without_params(self):
        url = self.bond_base_url + "/api/link/v1/" + self.provider + "/authorization-url"
        r = requests.get(url)
        self.assertEqual(400, r.status_code)

    def test_get_auth_url_with_only_redirect_param(self):
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


class AuthorizedApiTestCase(BaseApiTestCase):
    """
    Provides UserCredentials objects for obtaining OAuth2 Access Tokens that we can use as bearer tokens during
    tests.
    """
    hermione_email = "hermione.owner@test.firecloud.org"
    harry_email = "harry.potter@test.firecloud.org"
    path_to_key_file = "key.json"
    user_credentials = {hermione_email: UserCredentials(hermione_email, path_to_key_file),
                        harry_email: UserCredentials(harry_email, path_to_key_file)}

    @staticmethod
    def link(token):
        url = BaseApiTestCase.bond_base_url + "/api/link/v1/" + BaseApiTestCase.provider + "/oauthcode?oauthcode=IgnoredByMockProvider&redirect_uri=http%3A%2F%2Flocal.broadinstitute.org%2F%23fence-callback"
        return requests.post(url, headers=AuthorizedApiTestCase.bearer_token_header(token))

    @staticmethod
    def unlink(token):
        url = BaseApiTestCase.bond_base_url + "/api/link/v1/" + BaseApiTestCase.provider
        return requests.delete(url, headers=AuthorizedApiTestCase.bearer_token_header(token))

    @staticmethod
    def unlink_all(self):
        for credential in self.user_credentials.values():
            token = credential.get_access_token()
            r = self.unlink(token)
            self.assertIn(r.status_code, [204, 400])

    @staticmethod
    def bearer_token_header(token):
        return {"Authorization": "Bearer %s" % token}


class UnlinkedUserTestCase(AuthorizedApiTestCase):
    """Tests APIs that require a bearer token, but the users' accounts are NOT linked in Bond"""

    def setUp(self):
        self.token = self.user_credentials[self.hermione_email].get_access_token()
        self.unlink(self.token)

    def test_delete_link_for_unlinked_user(self):
        r = self.unlink(self.token)
        self.assertEqual(204, r.status_code)

    def test_get_link_status_for_unlinked_user(self):
        url = self.bond_base_url + "/api/link/v1/" + self.provider
        r = requests.get(url, headers=self.bearer_token_header(self.token))
        self.assertEqual(404, r.status_code)

    def test_get_access_token_for_unlinked_user(self):
        url = self.bond_base_url + "/api/link/v1/" + self.provider + "/accesstoken"
        r = requests.get(url, headers=self.bearer_token_header(self.token))
        self.assertEqual(400, r.status_code)


class ExchangeAuthCodeTestCase(UnlinkedUserTestCase):
    """Tests the Exchange Auth Code API"""
    def setUp(self):
        super(ExchangeAuthCodeTestCase, self).setUp()

    def test_exchange_auth_code(self):
        url = self.bond_base_url + "/api/link/v1/" + self.provider + "/oauthcode?oauthcode=IgnoredByMockProvider&redirect_uri=http%3A%2F%2Flocal.broadinstitute.org%2F%23fence-callback"
        r = requests.post(url, headers=self.bearer_token_header(self.token))
        self.assertEqual(200, r.status_code)
        response = json.loads(r.text)
        self.assertIsNotNone(response["issued_at"])
        self.assertIsNotNone(response["username"])


class ExchangeAuthCodeNegativeTestCase(UnlinkedUserTestCase):
    """
    Separate class for testing negative test cases that avoids setUp and tearDown that links and unlinks users.
    The process of linking and unlinking slows things down, so these tests are extracted to be on their own.
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


class LinkedUserTestCase(AuthorizedApiTestCase):
    """Tests that require the user account to be linked as a precondition to the test"""

    @classmethod
    def setUpClass(cls):
        cls.token = cls.user_credentials[cls.hermione_email].get_access_token()
        cls.link(cls.token)

    @classmethod
    def tearDownClass(cls):
        cls.unlink(cls.token)

    def test_get_link_status(self):
        url = self.bond_base_url + "/api/link/v1/" + self.provider
        r = requests.get(url, headers=self.bearer_token_header(LinkedUserTestCase.token))
        self.assertEqual(200, r.status_code)

    def test_get_access_token(self):
        url = self.bond_base_url + "/api/link/v1/" + self.provider + "/accesstoken"
        r = requests.get(url, headers=self.bearer_token_header(LinkedUserTestCase.token))
        self.assertEqual(200, r.status_code)
        response = json.loads(r.text)
        self.assertIsNotNone(response["expires_at"])
        self.assertIsNotNone(response["token"])


class UserCredentialsTestCase(AuthorizedApiTestCase):
    """
    Tests to confirm that we're able to use the provided service account key to assume generate access tokens for
    test users
    """
    def setUp(self):
        self.token = UserCredentials("hermione.owner@test.firecloud.org", "key.json").get_access_token()

    def test_token(self):
        self.assertEqual(len(self.token), 185)

    def test_user_info_for_delegated_user(self):
        r = requests.get("https://www.googleapis.com/oauth2/v1/userinfo?alt=json",
                         headers=self.bearer_token_header(self.token))
        user_info = json.loads(r.text)
        self.assertEqual(self.hermione_email, user_info["email"])
