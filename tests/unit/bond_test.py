import base64
import json
import unittest
import uuid
from datetime import datetime

import jwt
from urllib.parse import urlparse, parse_qs
from mock import MagicMock
from werkzeug import exceptions

from bond_app.authentication import UserInfo
from bond_app.bond import Bond, FenceKeys
from bond_app.fence_api import FenceApi
from bond_app.fence_token_vending import FenceTokenVendingMachine
from bond_app.oauth_adapter import OauthAdapter
from tests.unit.fake_oauth2_state_store import FakeOAuth2StateStore
from tests.unit.fake_token_store import FakeTokenStore
from tests.unit.fake_cache_api import FakeCacheApi
from tests.unit.fake_fence_token_storage import FakeFenceTokenStorage

provider_name = "test"


def encoded_state():
    return base64.b64encode(json.dumps({'foo': 'bar'}).encode('utf-8'))


def get_url_state(url):
    parsed_url = urlparse(url)
    return parse_qs(parsed_url.query)['state'][0]


def parse_nonce_from_url_state(url):
    return json.loads(base64.b64decode(get_url_state(url)))['nonce']


class BondTestCase(unittest.TestCase):

    def encoded_state_with_nonce(self):
        return self.oauth2_state_store.state_with_nonce(encoded_state())

    def setUp(self):
        super(BondTestCase, self).setUp()

        self.name = "Bob McBob"
        self.issued_at_epoch = 1528896868
        self.expires_at_epoch = 1529081182
        self.fake_access_token = str(uuid.uuid4())
        self.user_id = str(uuid.uuid4())

        data = {"context": {"user": {"name": self.name}}, 'iat': self.issued_at_epoch}
        encoded_jwt = jwt.encode(data, 'secret', 'HS256')
        fake_token_dict = {FenceKeys.ACCESS_TOKEN: self.fake_access_token,
                           FenceKeys.REFRESH_TOKEN: str(uuid.uuid4()),
                           FenceKeys.ID_TOKEN: encoded_jwt,
                           FenceKeys.EXPIRES_AT: self.expires_at_epoch}

        mock_oauth_adapter = OauthAdapter("foo", "bar", "baz", "qux")
        mock_oauth_adapter.exchange_authz_code = MagicMock(return_value=fake_token_dict, name="exchange_authz_code")
        mock_oauth_adapter.refresh_access_token = MagicMock(return_value=fake_token_dict, name="refresh_access_token")
        mock_oauth_adapter.revoke_refresh_token = MagicMock(name="revoke_refresh_token")
        mock_oauth_adapter.build_authz_url = MagicMock(name="build_authz_url")

        fence_api = self._mock_fence_api(json.dumps({"private_key_id": "asfasdfasdf"}))
        self.refresh_token_store = FakeTokenStore()
        self.oauth2_state_store = FakeOAuth2StateStore()
        self.bond = Bond(mock_oauth_adapter,
                         fence_api,
                         FakeCacheApi(),
                         self.refresh_token_store,
                         self.oauth2_state_store,
                         FenceTokenVendingMachine(fence_api, FakeCacheApi(), self.refresh_token_store,
                                                  mock_oauth_adapter,
                                                  provider_name, FakeFenceTokenStorage()),
                         provider_name,
                         "/context/user/name",
                         {})

    def test_exchange_authz_code(self):
        state, nonce = self.encoded_state_with_nonce()
        self.oauth2_state_store.save(self.user_id, provider_name, nonce)
        issued_at, username = self.bond.exchange_authz_code("irrelevantString", "redirect", self.user_id,
                                                            state, provider_name)
        self.assertEqual(self.name, username)
        self.assertEqual(datetime.fromtimestamp(self.issued_at_epoch), issued_at)

    def test_exchange_authz_code_missing_token(self):
        data = {"context": {"user": {"name": self.name}}, 'iat': self.issued_at_epoch}
        encoded_jwt = jwt.encode(data, 'secret', 'HS256')
        fake_token_dict = {FenceKeys.ACCESS_TOKEN: self.fake_access_token,
                           FenceKeys.ID_TOKEN: encoded_jwt,
                           FenceKeys.EXPIRES_AT: self.expires_at_epoch}

        mock_oauth_adapter = OauthAdapter("foo", "bar", "baz", "qux")
        mock_oauth_adapter.exchange_authz_code = MagicMock(return_value=fake_token_dict)
        mock_oauth_adapter.refresh_access_token = MagicMock(return_value=fake_token_dict)
        mock_oauth_adapter.revoke_refresh_token = MagicMock()

        fence_api = self._mock_fence_api(json.dumps({"private_key_id": "asfasdfasdf"}))
        bond = Bond(mock_oauth_adapter,
                    fence_api,
                    FakeCacheApi(),
                    self.refresh_token_store,
                    self.oauth2_state_store,
                    FenceTokenVendingMachine(fence_api, FakeCacheApi(), self.refresh_token_store,
                                             mock_oauth_adapter, provider_name,
                                             FakeFenceTokenStorage()),
                    provider_name,
                    "/context/user/name",
                    {})

        state, nonce = self.encoded_state_with_nonce()
        self.oauth2_state_store.save(self.user_id, provider_name, nonce)

        with self.assertRaises(exceptions.BadRequest):
            bond.exchange_authz_code("irrelevantString", "redirect", self.user_id, state, provider_name)

    def test_exchange_authz_code_existing_token_clears_cache(self):
        token = str(uuid.uuid4())
        self.refresh_token_store.save(user_id=self.user_id,
                                      refresh_token_str=token,
                                      issued_at=datetime.fromtimestamp(self.issued_at_epoch),
                                      username=self.name,
                                      provider_name=provider_name)
        self.bond.fence_api.get_credentials_google = MagicMock(
            return_value=json.dumps({"private_key_id": "before_key"})
        )
        before_key = self.bond.fence_tvm.get_service_account_key_json(self.user_id)
        state, nonce = self.encoded_state_with_nonce()
        self.oauth2_state_store.save(self.user_id, provider_name, nonce)
        self.bond.exchange_authz_code("irrelevantString", "redirect", self.user_id, state, provider_name)
        self.bond.fence_api.get_credentials_google = MagicMock(
            return_value=json.dumps({"private_key_id": "after_key"})
        )
        after_key = self.bond.fence_tvm.get_service_account_key_json(self.user_id)
        self.assertNotEqual(before_key, after_key)

    def test_generate_access_token(self):
        token = str(uuid.uuid4())
        self.refresh_token_store.save(user_id=self.user_id,
                                      refresh_token_str=token,
                                      issued_at=datetime.fromtimestamp(self.issued_at_epoch),
                                      username=self.name,
                                      provider_name=provider_name)
        access_token, expires_at = self.bond.generate_access_token(self.user_id)
        self.assertEqual(self.fake_access_token, access_token)
        self.assertEqual(datetime.fromtimestamp(self.expires_at_epoch), expires_at)

    def test_get_access_token_from_cache(self):
        data = {"context": {"user": {"name": self.name}}, 'iat': self.issued_at_epoch}
        encoded_jwt = jwt.encode(data, 'secret', 'HS256')
        expires_at_initial = datetime.now().timestamp() + 1
        
        fake_token_defaults = {
            FenceKeys.ACCESS_TOKEN: self.fake_access_token,
            FenceKeys.ID_TOKEN: encoded_jwt,
        }

        mock_oauth_adapter = OauthAdapter("foo", "bar", "baz", "qux")
        mock_oauth_adapter.refresh_access_token = MagicMock(
            return_value={**fake_token_defaults, **{FenceKeys.EXPIRES_AT: expires_at_initial}}
        )

        fence_api = self._mock_fence_api(json.dumps({"private_key_id": "asfasdfasdf"}))
        cache_api = FakeCacheApi()
        bond = Bond(mock_oauth_adapter,
                    fence_api,
                    cache_api,
                    self.refresh_token_store,
                    self.oauth2_state_store,
                    FenceTokenVendingMachine(fence_api, cache_api, self.refresh_token_store,
                                             mock_oauth_adapter, provider_name,
                                             FakeFenceTokenStorage()),
                    provider_name,
                    "/context/user/name",
                    {})
        
        token = str(uuid.uuid4())
        self.refresh_token_store.save(user_id=self.user_id,
                                      refresh_token_str=token,
                                      issued_at=datetime.fromtimestamp(self.issued_at_epoch),
                                      username=self.name,
                                      provider_name=provider_name)

        # verify that the `expires_at_initial` value is returned with `get_access_token`,
        # because nothing has been cached yet.
        access_token, expires_at = bond.get_access_token(self.user_id, refresh_threshold=0)
        self.assertEqual(self.fake_access_token, access_token)
        self.assertEqual(datetime.fromtimestamp(expires_at_initial), expires_at)

        # Update the expiration date of the token that is returned by the mock oauth adapter,
        # simulating the behavior of the real oauth adapter when a new access token is created.
        # (in reality, the token would be updated too, but it's not necessary for this test)
        expires_at_new = expires_at_initial + 100
        mock_oauth_adapter.refresh_access_token = MagicMock(
            return_value={**fake_token_defaults, **{FenceKeys.EXPIRES_AT: expires_at_new}}
        )

        # verify that the cached `expires_at_initial` value is returned with `get_access_token`,
        # *not* the new `expires_at_new` value.
        access_token, expires_at = bond.get_access_token(self.user_id)
        self.assertEqual(self.fake_access_token, access_token)
        self.assertEqual(datetime.fromtimestamp(expires_at_initial), expires_at)

    def test_get_access_token_from_generate(self):
        data = {"context": {"user": {"name": self.name}}, 'iat': self.issued_at_epoch}
        encoded_jwt = jwt.encode(data, 'secret', 'HS256')
        refresh_threshold = 1  # refresh threshold intentionally set to expire
        expires_at_initial = datetime.now().timestamp() + refresh_threshold

        fake_token_defaults = {
            FenceKeys.ACCESS_TOKEN: self.fake_access_token,
            FenceKeys.ID_TOKEN: encoded_jwt,
        }

        mock_oauth_adapter = OauthAdapter("foo", "bar", "baz", "qux")
        mock_oauth_adapter.refresh_access_token = MagicMock(
            return_value={**fake_token_defaults, **{FenceKeys.EXPIRES_AT: expires_at_initial}}
        )

        fence_api = self._mock_fence_api(json.dumps({"private_key_id": "asfasdfasdf"}))
        cache_api = FakeCacheApi()
        bond = Bond(mock_oauth_adapter,
                    fence_api,
                    cache_api,
                    self.refresh_token_store,
                    self.oauth2_state_store,
                    FenceTokenVendingMachine(fence_api, cache_api, self.refresh_token_store,
                                             mock_oauth_adapter, provider_name,
                                             FakeFenceTokenStorage()),
                    provider_name,
                    "/context/user/name",
                    {})
        
        token = str(uuid.uuid4())
        self.refresh_token_store.save(user_id=self.user_id,
                                      refresh_token_str=token,
                                      issued_at=datetime.fromtimestamp(self.issued_at_epoch),
                                      username=self.name,
                                      provider_name=provider_name)

        # verify that the `expires_at_initial` value is returned with `get_access_token`,
        # because nothing has been cached yet.
        access_token, expires_at = bond.get_access_token(self.user_id, refresh_threshold=refresh_threshold)
        self.assertEqual(self.fake_access_token, access_token)
        self.assertEqual(datetime.fromtimestamp(expires_at_initial), expires_at)
        
        # Update the expiration date of the token that is returned by the mock oauth adapter,
        # simulating the behavior of the real oauth adapter when a new access token is created.
        # (in reality, the token would be updated too, but it's not necessary for this test)
        expires_at_new = expires_at_initial + 100
        mock_oauth_adapter.refresh_access_token = MagicMock(
            return_value={**fake_token_defaults, **{FenceKeys.EXPIRES_AT: expires_at_new}}
        )

        # verify that the new (uncached) `expired_at_new` value is returned with `get_access_token`,
        # because the refresh_threshold was set to expire the token immediately.
        access_token, expires_at = bond.get_access_token(self.user_id)
        self.assertEqual(self.fake_access_token, access_token)
        self.assertEqual(datetime.fromtimestamp(expires_at_new), expires_at)


    def test_generate_access_token_errors_when_missing_token(self):
        self.assertRaises(exceptions.NotFound, self.bond.generate_access_token, self.user_id)

    def test_revoke_link_exists(self):
        token = str(uuid.uuid4())
        self.refresh_token_store.save(self.user_id, token, datetime.now(), self.name, provider_name)
        self.bond.fence_tvm.get_service_account_key_json(self.user_id)

        self.bond.unlink_account(self.user_id)

        self.assertIsNone(self.refresh_token_store.lookup(self.user_id, provider_name))
        self.bond.oauth_adapter.revoke_refresh_token.assert_called_once()
        self.bond.fence_api.delete_credentials_google.assert_called_once()

        # there should be no remaining information for the deleted link
        with self.assertRaises(exceptions.NotFound):
            self.bond.generate_access_token(self.user_id)
        with self.assertRaises(exceptions.NotFound):
            self.bond.fence_tvm.get_service_account_key_json(self.user_id)

    def test_revoke_link_access_token(self):
        '''
        Ensures that cached access tokens are dumped when a user unlinks their account.
        '''

        data = {"context": {"user": {"name": self.name}}, 'iat': self.issued_at_epoch}
        refresh_token_initial = str(uuid.uuid4())
        refresh_token_renewed = str(uuid.uuid4())
        encoded_jwt = jwt.encode(data, 'secret', 'HS256')
        expires_at = datetime.now().timestamp() + 100000
        access_token_initial = "access_token_initial"
        access_token_renewed = "access_token_renewed"
        
        fake_token_defaults = {
            FenceKeys.ACCESS_TOKEN: access_token_initial,
            FenceKeys.REFRESH_TOKEN: refresh_token_initial,
            FenceKeys.ID_TOKEN: encoded_jwt,
            FenceKeys.EXPIRES_AT: expires_at,
        }

        mock_oauth_adapter = OauthAdapter("foo", "bar", "baz", "qux")
        mock_oauth_adapter.exchange_authz_code = MagicMock(return_value=fake_token_defaults, name="exchange_authz_code")
        mock_oauth_adapter.refresh_access_token = MagicMock(return_value=fake_token_defaults, name="refresh_access_token")
        mock_oauth_adapter.revoke_refresh_token = MagicMock(name="revoke_refresh_token")
        mock_oauth_adapter.build_authz_url = MagicMock(name="build_authz_url")

        fence_api = self._mock_fence_api(json.dumps({"private_key_id": "asfasdfasdf"}))
        cache_api = FakeCacheApi()
        
        bond = Bond(
            mock_oauth_adapter,
            fence_api,
            cache_api,
            self.refresh_token_store,
            self.oauth2_state_store,
            FenceTokenVendingMachine(
                fence_api, 
                cache_api, 
                self.refresh_token_store, 
                mock_oauth_adapter, 
                provider_name, 
                FakeFenceTokenStorage(),
            ),
            provider_name,
            "/context/user/name",
            {},
        )
        
        # link
        self.refresh_token_store.save(
            user_id=self.user_id,
            refresh_token_str=refresh_token_initial,
            issued_at=datetime.fromtimestamp(self.issued_at_epoch),
            username=self.name,
            provider_name=provider_name,
        )
        bond.fence_tvm.get_service_account_key_json(self.user_id)

        # generate and cache a token `access_token_initial` by calling `get_access_token`
        access_token, expires_at = bond.get_access_token(self.user_id)
        self.assertEqual(access_token_initial, access_token)

        # re-mock refresh_access_token return values to simulate a new access token to be issued
        mock_oauth_adapter.refresh_access_token = MagicMock(
            return_value={**fake_token_defaults, **{FenceKeys.ACCESS_TOKEN: access_token_renewed}}, 
            name="refresh_access_token"
        )

        # demonstrate that `access_token_initial` has been cached
        access_token, expires_at = bond.get_access_token(self.user_id)
        self.assertEqual(access_token_initial, access_token)

        # unlink account and verify that the access token has been cleared
        bond.unlink_account(self.user_id)
        self.assertIsNone(cache_api.get(self.user_id, namespace=f"{provider_name}:AccessTokens"))

        # relink account
        self.refresh_token_store.save(
            user_id=self.user_id,
            refresh_token_str=refresh_token_renewed,
            issued_at=datetime.fromtimestamp(self.issued_at_epoch),
            username=self.name,
            provider_name=provider_name,
        )
        bond.fence_tvm.get_service_account_key_json(self.user_id)
        
        # check cache to ensure that it was dumped
        access_token, expires_at = bond.get_access_token(self.user_id)
        self.assertEqual(access_token_renewed, access_token)

    def test_revoke_link_does_not_exists(self):
        self.bond.unlink_account(self.user_id)

    def test_link_info_exists(self):
        token = str(uuid.uuid4())
        self.refresh_token_store.save(user_id=self.user_id,
                                      refresh_token_str=token,
                                      issued_at=datetime.fromtimestamp(self.issued_at_epoch),
                                      username=self.name,
                                      provider_name=provider_name)
        link_info = self.bond.get_link_info(self.user_id)
        self.assertEqual(token, link_info.token)

    def test_link_info_not_exists(self):
        link_info = self.bond.get_link_info(self.user_id)
        self.assertIsNone(link_info)

    def test_build_authz_url_without_extra_params(self):
        scopes = ['foo', 'bar']
        redirect_uri = 'http://anything.url'
        state = encoded_state()

        self.bond.build_authz_url(scopes, redirect_uri, self.user_id, provider_name, state)

        state_with_nonce, nonce = self.oauth2_state_store.state_with_nonce(state)
        self.bond.oauth_adapter.build_authz_url.assert_called_once_with(scopes, redirect_uri, state_with_nonce, {})

        valid_oauth2_state = self.bond.oauth2_state_store.validate_and_delete(self.user_id, provider_name, nonce)
        self.assertTrue(valid_oauth2_state)

    def test_build_authz_url_with_extra_params(self):
        scopes = ['foo', 'bar']
        redirect_uri = 'http://anything.url'
        state = encoded_state()
        extra_params = {"bar": "foo"}

        self.bond.extra_authz_url_params = extra_params
        self.bond.build_authz_url(scopes, redirect_uri, self.user_id, provider_name, state)

        state_with_nonce, nonce = self.oauth2_state_store.state_with_nonce(state)
        self.bond.oauth_adapter.build_authz_url.assert_called_once_with(scopes, redirect_uri, state_with_nonce,
                                                                        extra_params)

        valid_oauth2_state = self.bond.oauth2_state_store.validate_and_delete(self.user_id, provider_name, nonce)
        self.assertTrue(valid_oauth2_state)

    def test_nonce_success(self):
        scopes = ['foo', 'bar']
        redirect_uri = 'http://anything.url'
        state = encoded_state()

        self.bond.build_authz_url(scopes, redirect_uri, self.user_id, provider_name, state)
        state_with_nonce, nonce = self.oauth2_state_store.state_with_nonce(state)

        self.bond.exchange_authz_code("irrelevantString", redirect_uri, self.user_id, state_with_nonce, provider_name)
        self.bond.oauth_adapter.exchange_authz_code.assert_called_once_with("irrelevantString", redirect_uri)

    def test_nonce_failure(self):
        scopes = ['foo', 'bar']
        redirect_uri = 'http://anything.url'
        state = encoded_state()

        self.bond.build_authz_url(scopes, redirect_uri, self.user_id, provider_name, state)
        state_with_bad_nonce = base64.b64encode(json.dumps({'nonce': 'unsaved_nonce'}).encode('utf-8'))

        with self.assertRaisesRegex(exceptions.InternalServerError, "Invalid OAuth2 State: Invalid nonce"):
            self.bond.exchange_authz_code("irrelevantString", "redirect", self.user_id, state_with_bad_nonce,
                                          provider_name)

    def test_no_nonce(self):
        scopes = ['foo', 'bar']
        redirect_uri = 'http://anything.url'
        state = encoded_state()

        self.bond.build_authz_url(scopes, redirect_uri, self.user_id, provider_name, state)

        with self.assertRaisesRegex(exceptions.InternalServerError, "Invalid OAuth2 State: No nonce provided"):
            self.bond.exchange_authz_code("irrelevantString", "redirect", self.user_id, state,
                                          provider_name)

    def test_double_nonce_success(self):
        scopes = ['foo', 'bar']
        redirect_uri = 'http://anything.url'
        state = encoded_state()

        self.bond.build_authz_url(scopes, redirect_uri, self.user_id, provider_name, state)
        state_with_nonce, _ = self.oauth2_state_store.state_with_nonce(state, override_nonce="second_nonce")
        self.oauth2_state_store.save(self.user_id, provider_name, "second_nonce")

        self.bond.exchange_authz_code("irrelevantString", redirect_uri, self.user_id, state_with_nonce, provider_name)
        self.bond.oauth_adapter.exchange_authz_code.assert_called_once_with("irrelevantString", redirect_uri)

    def test_double_nonce_failure(self):
        scopes = ['foo', 'bar']
        redirect_uri = 'http://anything.url'
        state = encoded_state()

        self.bond.build_authz_url(scopes, redirect_uri, self.user_id, provider_name, state)
        state_with_nonce, _ = self.oauth2_state_store.state_with_nonce(state)
        self.oauth2_state_store.save(self.user_id, provider_name, "second_nonce")

        with self.assertRaisesRegex(exceptions.InternalServerError, "Invalid OAuth2 State: Invalid nonce"):
            self.bond.exchange_authz_code("irrelevantString", "redirect", self.user_id, state_with_nonce, provider_name)

    @staticmethod
    def _mock_fence_api(service_account_json):
        fence_api = FenceApi("")
        fence_api.get_credentials_google = MagicMock(return_value=service_account_json)
        fence_api.delete_credentials_google = MagicMock()
        return fence_api
