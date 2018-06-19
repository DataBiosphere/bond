import unittest
import uuid
import jwt
from mock import MagicMock
from datetime import datetime
from google.appengine.api import datastore
from google.appengine.api import memcache
from google.appengine.ext import testbed

from oauth_adapter import OauthAdapter
from bond import Bond, FenceKeys
from refresh_token import RefreshToken


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
        data = {"context": {"user": {"name": self.name}}, 'iat': self.issued_at_epoch}
        encoded_jwt = jwt.encode(data, 'secret', 'HS256')
        fake_token_dict = {FenceKeys.ACCESS_TOKEN_KEY: self.fake_access_token,
                           FenceKeys.REFRESH_TOKEN_KEY: str(uuid.uuid4()),
                           FenceKeys.ID_TOKEN: encoded_jwt,
                           FenceKeys.EXPIRES_AT_KEY: self.expires_at_epoch}

        mock_oauth_adapter = OauthAdapter("foo", "bar", "baz", "qux")
        mock_oauth_adapter.exchange_authz_code = MagicMock(return_value=fake_token_dict)
        mock_oauth_adapter.refresh_access_token = MagicMock(return_value=fake_token_dict)

        self.bond = Bond(mock_oauth_adapter)

    def test_exchange_authz_code(self):
        user_id = str(uuid.uuid4())
        issued_at, username = self.bond.exchange_authz_code("irrelevantString", user_id)
        self.assertEqual(self.name, username)
        self.assertEqual(datetime.fromtimestamp(self.issued_at_epoch), issued_at)

    def test_generate_access_token(self):
        user_id = str(uuid.uuid4())
        token = str(uuid.uuid4())
        RefreshToken(id=user_id, token=token, issued_at=datetime.fromtimestamp(self.issued_at_epoch), username=self.name).put()
        access_token, expires_at = self.bond.generate_access_token(user_id)
        self.assertEqual(self.fake_access_token, access_token)
        self.assertEqual(datetime.fromtimestamp(self.expires_at_epoch), expires_at)

    def test_generate_access_token_errors_when_missing_token(self):
        user_id = str(uuid.uuid4())
        self.assertRaises(Bond.MissingTokenError, self.bond.generate_access_token, user_id)
