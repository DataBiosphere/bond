import unittest

from token_store import TokenStore, RefreshToken
from datetime import datetime
import datastore_emulator_utils

provider_name = "test"


class TokenStoreTestCase(unittest.TestCase):

    def setUp(self):
        # Make sure to run these tests with a Datastore Emulator running or else they will fail with 'InternalError.'
        # See the README in this directory.
        datastore_emulator_utils.setUp(self)

        self.user_id = "abc123"
        self.token_str = "aaaaaabbbbbbcccccccddddddd"
        self.issued_at = datetime.now()
        self.username = "Ralph"
        self.key = TokenStore._token_store_key(self.user_id, provider_name)

    def test_save(self):
        token_store = TokenStore()
        self.assertIsNone(self.key.get())
        token_store.save(self.user_id, self.token_str, self.issued_at, self.username, provider_name)
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


class RefreshTokenTestCase(unittest.TestCase):
    def setUp(self):
        datastore_emulator_utils.setUp(self)

    def test_kind_name(self):
        self.assertEqual("RefreshToken", RefreshToken.kind_name())

    def test_properties(self):
        user_id = "123456"
        token_str = "foobarbaz"
        issued_at = datetime.now()
        username = "bob@email-address.gov"
        refresh_token = RefreshToken(id=user_id, token=token_str, issued_at=issued_at, username=username)
        self.assertEqual(user_id, refresh_token.key.id())
        self.assertEqual(token_str, refresh_token.token)
        self.assertEqual(issued_at, refresh_token.issued_at)
