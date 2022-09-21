import base64
import json
import unittest

from bond_app.oauth2_state_store import OAuth2StateStore
from tests.datastore_emulator import datastore_emulator_utils

provider_name = "test"


class OAuth2StateStoreTestCase(unittest.TestCase):

    def setUp(self):
        # Make sure to run these tests with a Datastore Emulator running or else they will fail with 'InternalError.'
        # See the README in this directory.
        datastore_emulator_utils.setUp(self)

        self.user_id = "abc123"
        self.state = base64.b64encode(json.dumps({}).encode('utf-8'))
        self.key = OAuth2StateStore._oauth2_state_store_key(self.user_id, provider_name)

    def test_save(self):
        oauth2_state_store = OAuth2StateStore()
        state, nonce = oauth2_state_store.state_with_nonce(self.state)
        self.assertIsNone(self.key.get())
        oauth2_state_store.save(self.user_id, provider_name, nonce)
        saved_state = self.key.get()
        self.assertIsNotNone(saved_state)
        self.assertEqual(nonce, saved_state.nonce)

    def test_validate_and_delete_success(self):
        oauth2_state_store = OAuth2StateStore()
        state, nonce = oauth2_state_store.state_with_nonce(self.state)
        oauth2_state_store.save(self.user_id, provider_name, nonce)
        is_valid = oauth2_state_store.validate_and_delete(self.user_id, provider_name, nonce)
        self.assertTrue(is_valid)
        self.assertIsNone(self.key.get())

    def test_validate_and_delete_failure(self):
        oauth2_state_store = OAuth2StateStore()
        state, nonce = oauth2_state_store.state_with_nonce(self.state)
        state2, nonce2 = oauth2_state_store.state_with_nonce(self.state)
        oauth2_state_store.save(self.user_id, provider_name, nonce)
        is_valid = oauth2_state_store.validate_and_delete(self.user_id, provider_name, nonce2)
        self.assertFalse(is_valid)
        # Even if the state is invalid, the key should still get deleted
        self.assertIsNone(self.key.get())
