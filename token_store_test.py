import unittest

# Imports might be highlighted as "unused" by IntelliJ, but they are used, see setUp()
from google.appengine.api import datastore
from google.appengine.api import memcache
from google.appengine.ext import testbed
from google.appengine.ext import ndb
from token_store import TokenStore
from refresh_token import RefreshToken
from datetime import datetime


class TokenStoreTestCase(unittest.TestCase):

    def setUp(self):
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

        self.user_id = "abc123"
        self.token_str = "aaaaaabbbbbbcccccccddddddd"
        self.issued_at = datetime.now()
        self.key = ndb.Key(RefreshToken.kind_name(), self.user_id)

    def tearDown(self):
        self.testbed.deactivate()

    def test_save(self):
        self.assertIsNone(self.key.get())
        self.assertEqual(TokenStore.save(self.user_id, self.token_str, self.issued_at), self.key)
        self.assertIsNotNone(self.key.get())

    def test_lookup(self):
        RefreshToken(id=self.user_id, token=self.token_str, issued_at=self.issued_at).put()
        persisted_token = TokenStore.lookup(self.user_id)
        self.assertEqual(persisted_token.token, self.token_str)
        self.assertEqual(persisted_token.issued_at, self.issued_at)
