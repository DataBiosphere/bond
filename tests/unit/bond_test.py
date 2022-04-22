import json
import unittest
import uuid
from datetime import datetime

import jwt
from mock import MagicMock
from werkzeug import exceptions

from bond_app.authentication import UserInfo
from bond_app.bond import Bond, FenceKeys
from bond_app.fence_api import FenceApi
from bond_app.fence_token_vending import FenceTokenVendingMachine
from bond_app.oauth_adapter import OauthAdapter
from tests.unit.fake_token_store import FakeTokenStore
from tests.unit.fake_cache_api import FakeCacheApi
from tests.unit.fake_fence_token_storage import FakeFenceTokenStorage

provider_name = "test"


class BondTestCase(unittest.TestCase):
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
        self.bond = Bond(mock_oauth_adapter,
                         fence_api,
                         FakeCacheApi(),
                         self.refresh_token_store,
                         FenceTokenVendingMachine(fence_api, FakeCacheApi(), self.refresh_token_store,
                                                  mock_oauth_adapter,
                                                  provider_name, FakeFenceTokenStorage()),
                         provider_name,
                         "/context/user/name",
                         {})

    def test_exchange_authz_code(self):
        issued_at, username = self.bond.exchange_authz_code("irrelevantString", "redirect", self.user_id)
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
                    FenceTokenVendingMachine(fence_api, FakeCacheApi(), self.refresh_token_store,
                                             mock_oauth_adapter, provider_name,
                                             FakeFenceTokenStorage()),
                    provider_name,
                    "/context/user/name",
                    {})

        with self.assertRaises(exceptions.BadRequest):
            bond.exchange_authz_code("irrelevantString", "redirect", UserInfo(str(uuid.uuid4()), "", "", 30))

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
        self.bond.exchange_authz_code("irrelevantString", "redirect", self.user_id)
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
        state = "baz"
        self.bond.build_authz_url(scopes, redirect_uri, state)
        self.bond.oauth_adapter.build_authz_url.assert_called_once_with(scopes, redirect_uri, state, {})

    def test_build_authz_url_with_extra_params(self):
        scopes = ['foo', 'bar']
        redirect_uri = 'http://anything.url'
        state = "baz"
        extra_params = {"bar": "foo"}
        self.bond.extra_authz_url_params = extra_params
        self.bond.build_authz_url(scopes, redirect_uri, state)
        self.bond.oauth_adapter.build_authz_url.assert_called_once_with(scopes, redirect_uri, state, extra_params)

    @staticmethod
    def _mock_fence_api(service_account_json):
        fence_api = FenceApi("")
        fence_api.get_credentials_google = MagicMock(return_value=service_account_json)
        fence_api.delete_credentials_google = MagicMock()
        return fence_api
