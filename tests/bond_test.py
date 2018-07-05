import unittest
import uuid
import jwt
from datetime import datetime
from google.appengine.api import datastore
from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.ext import testbed

from oauth_adapter import OauthAdapter
from bond import Bond, FenceKeys
from refresh_token import RefreshToken
from sam_api import SamApi
from sam_api import SamKeys
from fence_api import FenceApi
from authentication import UserInfo
from fence_token_vending import FenceTokenVendingMachine, FenceServiceAccount
from mock import MagicMock
from token_store import TokenStore
import json


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
        fake_token_dict = {FenceKeys.ACCESS_TOKEN_KEY: self.fake_access_token,
                           FenceKeys.REFRESH_TOKEN_KEY: str(uuid.uuid4()),
                           FenceKeys.ID_TOKEN: encoded_jwt,
                           FenceKeys.EXPIRES_AT_KEY: self.expires_at_epoch}

        mock_oauth_adapter = OauthAdapter("foo", "bar", "baz", "qux")
        mock_oauth_adapter.exchange_authz_code = MagicMock(return_value=fake_token_dict)
        mock_oauth_adapter.refresh_access_token = MagicMock(return_value=fake_token_dict)

        fence_api = self._mock_fence_api(json.dumps({"private_key_id": "asfasdfasdf"}))
        sam_api = self._mock_sam_api(self.user_id, "email")
        self.bond = Bond(mock_oauth_adapter, fence_api, sam_api, FenceTokenVendingMachine(fence_api, sam_api, mock_oauth_adapter))

    def tearDown(self):
        ndb.get_context().clear_cache()  # Ensure data is truly flushed from datastore/memcache
        self.testbed.deactivate()

    def test_exchange_authz_code(self):
        issued_at, username = self.bond.exchange_authz_code("irrelevantString", UserInfo(str(uuid.uuid4()), "", "", 30))
        self.assertEqual(self.name, username)
        self.assertEqual(datetime.fromtimestamp(self.issued_at_epoch), issued_at)

    def test_generate_access_token(self):
        token = str(uuid.uuid4())
        RefreshToken(id=self.user_id, token=token, issued_at=datetime.fromtimestamp(self.issued_at_epoch), username=self.name).put()
        access_token, expires_at = self.bond.generate_access_token(UserInfo(str(uuid.uuid4()), "", "", 30))
        self.assertEqual(self.fake_access_token, access_token)
        self.assertEqual(datetime.fromtimestamp(self.expires_at_epoch), expires_at)

    def test_generate_access_token_errors_when_missing_token(self):
        self.assertRaises(Bond.MissingTokenError, self.bond.generate_access_token, UserInfo(str(uuid.uuid4()), "", "", 30))

    def test_revoke_link_exists(self):
        token = str(uuid.uuid4())
        TokenStore.save(self.user_id, token, datetime.now(), self.name)
        user_info = UserInfo(str(uuid.uuid4()), "", "", 30)
        self.bond.fence_tvm.get_service_account_key_json(user_info)
        self.assertIsNotNone(ndb.Key(FenceServiceAccount, self.user_id).get())

        self.bond.unlink_account(user_info)

        self.assertIsNone(ndb.Key(FenceServiceAccount, self.user_id).get())
        self.assertIsNone(TokenStore.lookup(self.user_id))
        self.bond.fence_api.revoke_refresh_token.assert_called_once()
        self.bond.fence_api.delete_credentials_google.assert_called_once()

    def test_revoke_link_does_not_exists(self):
        user_info = UserInfo(str(uuid.uuid4()), "", "", 30)
        self.bond.unlink_account(user_info)

    def test_link_info_exists(self):
        token = str(uuid.uuid4())
        refresh_token = RefreshToken(id=self.user_id, token=token, issued_at=datetime.fromtimestamp(self.issued_at_epoch), username=self.name)
        refresh_token.put()
        link_info = self.bond.get_link_info(UserInfo(str(uuid.uuid4()), "", "", 30))
        self.assertEqual(refresh_token, link_info)

    def test_link_info_not_exists(self):
        link_info = self.bond.get_link_info(UserInfo(str(uuid.uuid4()), "", "", 30))
        self.assertIsNone(link_info)

    @staticmethod
    def _mock_fence_api(service_account_json):
        fence_api = FenceApi("")
        fence_api.get_credentials_google = MagicMock(return_value=service_account_json)
        fence_api.delete_credentials_google = MagicMock()
        fence_api.revoke_refresh_token = MagicMock()
        return fence_api

    @staticmethod
    def _mock_sam_api(subject_id, email):
        sam_api = SamApi("")
        sam_api.user_info = MagicMock(return_value={SamKeys.USER_ID_KEY: subject_id, SamKeys.USER_EMAIL_KEY: email})
        return sam_api
