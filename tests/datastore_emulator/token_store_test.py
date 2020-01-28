import unittest

from google.appengine.ext import ndb
from token_store import TokenStore
from datetime import datetime

provider_name = "test"


class TokenStoreTestCase(unittest.TestCase):

    def setUp(self):
        # Make sure to run these tests with a Datastore Emulator running or else they will fail with 'InternalError.'
        # See the README in this directory.

        # Disable memcache for this test as we're not emulating a memcache environment and we will raise errors
        # as ndb tries to use memcache by default.
        ndb.get_context().set_memcache_policy(False)

        self.user_id = "abc123"
        self.token_str = "aaaaaabbbbbbcccccccddddddd"
        self.issued_at = datetime.now()
        self.username = "Ralph"
        self.key = TokenStore._token_store_key(self.user_id, provider_name)

    def tearDown(self):
        # Remove keys from the datastore.
        self.key.delete()

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
