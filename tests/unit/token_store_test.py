import unittest

# Imports might be highlighted as "unused" by IntelliJ, but they are used, see setUp()
from google.appengine.api import datastore
from google.appengine.api import memcache
from google.appengine.ext import testbed
from google.appengine.ext import ndb
from token_store import TokenStore
from refresh_token import RefreshToken
from datetime import datetime

provider_name = "test"


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
        self.username = "Ralph"
        self.key = TokenStore._token_store_key(self.user_id, provider_name)

    def tearDown(self):
        ndb.get_context().clear_cache()  # Ensure data is truly flushed from datastore/memcache
        self.testbed.deactivate()

    def test_save(self):
        self.assertIsNone(self.key.get())
        result_key = TokenStore.save(self.user_id, self.token_str, self.issued_at, self.username, provider_name)
        self.assertEqual(result_key, self.key)
        saved_token = self.key.get()
        self.assertIsNotNone(saved_token)
        self.assertEqual(self.token_str, saved_token.token)
        self.assertEqual(self.issued_at, saved_token.issued_at)
        self.assertEqual(self.username, saved_token.username)

    def test_lookup(self):
        TokenStore.save(self.user_id, self.token_str, self.issued_at, self.username, provider_name)
        persisted_token = TokenStore.lookup(self.user_id, provider_name)
        self.assertEqual(self.token_str, persisted_token.token)
        self.assertEqual(self.issued_at, persisted_token.issued_at)
        self.assertEqual(self.username, persisted_token.username)
