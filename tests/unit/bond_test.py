import json
import unittest
import uuid
from datetime import datetime

import endpoints
import jwt
from google.appengine.ext import ndb
from google.appengine.ext import testbed
from mock import MagicMock

from authentication import UserInfo
from fence_token_storage import build_fence_service_account_key
from memcache_api import MemcacheApi
from bond import Bond, FenceKeys
from fence_api import FenceApi
from fence_token_vending import FenceTokenVendingMachine
import fence_token_storage
from oauth_adapter import OauthAdapter
from sam_api import SamApi
from sam_api import SamKeys
from token_store import TokenStore

provider_name = "test"


class BondTestCase(unittest.TestCase):
    def setUp(self):
        super(BondTestCase, self).setUp()
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

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
        sam_api = self._mock_sam_api(self.user_id, "email")
        self.bond = Bond(mock_oauth_adapter,
                         fence_api,
                         sam_api,
                         FenceTokenVendingMachine(fence_api, sam_api, MemcacheApi(), mock_oauth_adapter, provider_name,
                                                  fence_token_storage.FenceTokenStorage()),
                         provider_name,
                         "/context/user/name",
                         {})

    def tearDown(self):
        ndb.get_context().clear_cache()  # Ensure data is truly flushed from datastore/memcache
        self.testbed.deactivate()

    def test_exchange_authz_code(self):
        issued_at, username = self.bond.exchange_authz_code("irrelevantString", "redirect", UserInfo(str(uuid.uuid4()), "", "", 30))
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
        sam_api = self._mock_sam_api(self.user_id, "email")
        bond = Bond(mock_oauth_adapter,
                    fence_api,
                    sam_api,
                    FenceTokenVendingMachine(fence_api, sam_api, MemcacheApi(), mock_oauth_adapter, provider_name,
                                             fence_token_storage.FenceTokenStorage()),
                    provider_name,
                    "/context/user/name",
                    {})

        with self.assertRaises(endpoints.BadRequestException):
            bond.exchange_authz_code("irrelevantString", "redirect", UserInfo(str(uuid.uuid4()), "", "", 30))

    def test_generate_access_token(self):
        token = str(uuid.uuid4())
        TokenStore.save(user_id=self.user_id,
                        refresh_token_str=token,
                        issued_at=datetime.fromtimestamp(self.issued_at_epoch),
                        username=self.name,
                        provider_name=provider_name)
        access_token, expires_at = self.bond.generate_access_token(UserInfo(str(uuid.uuid4()), "", "", 30))
        self.assertEqual(self.fake_access_token, access_token)
        self.assertEqual(datetime.fromtimestamp(self.expires_at_epoch), expires_at)

    def test_generate_access_token_errors_when_missing_token(self):
        self.assertRaises(Bond.MissingTokenError, self.bond.generate_access_token, UserInfo(str(uuid.uuid4()), "", "", 30))

    def test_revoke_link_exists(self):
        token = str(uuid.uuid4())
        TokenStore.save(self.user_id, token, datetime.now(), self.name, provider_name)
        user_info = UserInfo(str(uuid.uuid4()), "", "", 30)
        self.bond.fence_tvm.get_service_account_key_json(user_info)
        self.assertIsNotNone(build_fence_service_account_key(self.bond.fence_tvm.provider_name, self.user_id).get())

        self.bond.unlink_account(user_info)

        self.assertIsNone(build_fence_service_account_key(self.bond.fence_tvm.provider_name, self.user_id).get())
        self.assertIsNone(TokenStore.lookup(self.user_id, provider_name))
        self.bond.oauth_adapter.revoke_refresh_token.assert_called_once()
        self.bond.fence_api.delete_credentials_google.assert_called_once()

    def test_revoke_link_does_not_exists(self):
        user_info = UserInfo(str(uuid.uuid4()), "", "", 30)
        self.bond.unlink_account(user_info)

    def test_link_info_exists(self):
        token = str(uuid.uuid4())
        TokenStore.save(user_id=self.user_id,
                        refresh_token_str=token,
                        issued_at=datetime.fromtimestamp(self.issued_at_epoch),
                        username=self.name,
                        provider_name=provider_name)
        link_info = self.bond.get_link_info(UserInfo(str(uuid.uuid4()), "", "", 30))
        self.assertEqual(token, link_info.token)

    def test_link_info_not_exists(self):
        link_info = self.bond.get_link_info(UserInfo(str(uuid.uuid4()), "", "", 30))
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

    @staticmethod
    def _mock_sam_api(subject_id, email):
        sam_api = SamApi("")
        sam_api.user_info = MagicMock(return_value={SamKeys.USER_ID_KEY: subject_id, SamKeys.USER_EMAIL_KEY: email})
        return sam_api
