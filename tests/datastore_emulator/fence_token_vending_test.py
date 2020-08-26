from bond_app.fence_token_vending import FenceTokenVendingMachine
from bond_app.fence_token_storage import FenceTokenStorage
from bond_app.datastore_cache_api import DatastoreCacheApi
from bond_app.sam_api import SamKeys, SamApi
from bond_app.fence_api import FenceApi
from bond_app.oauth_adapter import OauthAdapter
from bond_app.authentication import UserInfo
from tests.unit.fake_token_store import FakeTokenStore
from mock import MagicMock

import unittest
import datetime
import random
import string
from tests.datastore_emulator import datastore_emulator_utils


class FenceTokenVendingTestCase(unittest.TestCase):

    def setUp(self):
        # Make sure to run these tests with a Datastore Emulator running or else they will fail with 'InternalError.'
        # See the README in this directory.

        datastore_emulator_utils.setUp(self)
        self.cache_api = DatastoreCacheApi()
        self.refresh_token_store = FakeTokenStore()
        self.provider_name = "fake_provider"
        self.fence_token_storage = FenceTokenStorage()

    def test_remove_service_account_from_cache(self):
        fake_token = "fake_token"
        user_info = UserInfo(self._random_subject_id(), "splat@bar.com", fake_token, 10)
        expected_json = '{"private_key_id": "fake_token_value"}'

        ftvm = FenceTokenVendingMachine(self._mock_fence_api(expected_json),
                                        self._mock_sam_api(user_info.id, user_info.email),
                                        self.cache_api,
                                        self.refresh_token_store,
                                        self._mock_oauth_adapter(fake_token),
                                        self.provider_name,
                                        self.fence_token_storage)
        self.refresh_token_store.save(user_info.id,
                                      fake_token,
                                      datetime.datetime.now(),
                                      user_info.email,
                                      self.provider_name)
        key = ftvm.get_service_account_key_json(user_info)
        self.assertEqual(self.cache_api.get(namespace=self.provider_name, key=user_info.id), key)
        ftvm.remove_service_account(user_info.id)
        self.assertIsNone(self.cache_api.get(namespace=self.provider_name, key=user_info.id))

    @staticmethod
    def _random_subject_id():
        return ''.join(random.choice(string.digits) for _ in list(range(21)))

    @staticmethod
    def _mock_sam_api(subject_id, email):
        sam_api = SamApi("")
        sam_api.user_info = MagicMock(return_value={SamKeys.USER_ID_KEY: subject_id, SamKeys.USER_EMAIL_KEY: email})
        return sam_api

    @staticmethod
    def _mock_fence_api(service_account_json):
        fence_api = FenceApi("")
        fence_api.get_credentials_google = MagicMock(return_value=service_account_json)
        fence_api.delete_credentials_google = MagicMock(return_value=service_account_json)
        return fence_api

    @staticmethod
    def _mock_oauth_adapter(access_token):
        oauth_adapter = OauthAdapter("", "", "", "")
        oauth_adapter.refresh_access_token = MagicMock(return_value={"access_token": access_token})
        return oauth_adapter
