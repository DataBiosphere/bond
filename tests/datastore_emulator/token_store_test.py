import unittest

# Imports might be highlighted as "unused" by IntelliJ, but they are used, see setUp()
from google.appengine.api import datastore
from google.appengine.ext import ndb
from google.appengine.ext import testbed
from token_store import TokenStore
from refresh_token import RefreshToken
from datetime import datetime

provider_name = "test"


class TokenStoreTestCase(unittest.TestCase):

    def setUp(self):
        # Datastore uses memcache by default, so set up memcache stub.
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_memcache_stub()

        self.user_id = "abc123"
        self.token_str = "aaaaaabbbbbbcccccccddddddd"
        self.issued_at = datetime.now()
        self.username = "Ralph"
        self.key = TokenStore._token_store_key(self.user_id, provider_name)

    def tearDown(self):
        ndb.get_context().clear_cache()  # Ensure data is truly flushed from datastore/memcache
        self.testbed.deactivate()

    def test_save(self):
        token_store = TokenStore()
        self.assertIsNone(self.key.get())
        result_key = token_store.save(self.user_id, self.token_str, self.issued_at, self.username, provider_name)
        self.assertEqual(result_key, self.key)
        saved_token = self.key.get()
        self.assertIsNotNone(saved_token)
        self.assertEqual(self.token_str, saved_token.token)
        self.assertEqual(self.issued_at, saved_token.issued_at)
        self.assertEqual(self.username, saved_token.username)

    def test_lookup(self):
        token_store = TokenStore()
        token_store.save(self.user_id, self.token_str, self.issued_at, self.username, provider_name)
        persisted_token = token_store.lookup(self.user_id, provider_name)
        self.assertEqual(self.token_str, persisted_token.token)
        self.assertEqual(self.issued_at, persisted_token.issued_at)
        self.assertEqual(self.username, persisted_token.username)
