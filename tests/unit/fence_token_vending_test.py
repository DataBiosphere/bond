import unittest
from bond_app.fence_token_vending import FenceTokenVendingMachine
from werkzeug import exceptions

from bond_app.authentication import UserInfo
from mock import MagicMock
from bond_app.fence_api import FenceApi
from bond_app.fence_token_storage import ProviderUser
from bond_app.sam_api import SamApi
from bond_app.oauth_adapter import OauthAdapter
from tests.unit.fake_token_store import FakeTokenStore
from tests.unit.fake_cache_api import FakeCacheApi
from tests.unit.fake_fence_token_storage import FakeFenceTokenStorage
import datetime
import string
import random
from bond_app.sam_api import SamKeys

provider_name = "test"


class FenceTokenVendingMachineTestCase(unittest.TestCase):
    def setUp(self):
        self.cache_api = FakeCacheApi()
        self.refresh_token_store = FakeTokenStore()
        self.fence_token_storage = FakeFenceTokenStorage()

    def test_no_service_account(self):
        expected_json = 'fake service account json'
        caller_uid = self._random_subject_id()
        real_user_id = self._random_subject_id()

        ftvm = FenceTokenVendingMachine(self._mock_fence_api(expected_json),
                                        self._mock_sam_api(real_user_id, "foo@bar.com"),
                                        self.cache_api, self.refresh_token_store,
                                        self._mock_oauth_adapter("fake_token"), provider_name,
                                        self.fence_token_storage)

        self.refresh_token_store.save(real_user_id, "fake_refresh_token", datetime.datetime.now(), "foo@bar.com", provider_name)

        self.assertIsNone(self.cache_api.get(namespace=provider_name, key=caller_uid))

        service_account_json = ftvm.get_service_account_key_json(
            UserInfo(caller_uid, "splat@bar.com", "fake_token_too", 10))

        self.assertEqual(expected_json, service_account_json)
        self.assertIsNotNone(self.cache_api.get(namespace=provider_name, key=caller_uid))

    def test_active_service_account_in_cache(self):
        expected_json = 'fake service account json'
        caller_uid = self._random_subject_id()
        real_user_id = self._random_subject_id()

        ftvm = FenceTokenVendingMachine(None, None, self.cache_api, self.refresh_token_store, None, provider_name,
                                        self.fence_token_storage)  # none of the apis should be called

        self.cache_api.add(namespace=provider_name, key=caller_uid, value=expected_json, expires_in=20)

        provider_user = ProviderUser(ftvm.provider_name, real_user_id)
        self.assertIsNone(self.fence_token_storage.delete(provider_user))

        service_account_json = ftvm.get_service_account_key_json(
            UserInfo(caller_uid, "splat@bar.com", "fake_token_too", 10))

        self.assertEqual(expected_json, service_account_json)
        self.assertIsNone(self.fence_token_storage.delete(provider_user))

    def test_not_linked(self):
        caller_uid = self._random_subject_id()
        real_user_id = self._random_subject_id()

        ftvm = FenceTokenVendingMachine(self._mock_fence_api(None), self._mock_sam_api(real_user_id, "foo@bar.com"),
                                        self.cache_api, self.refresh_token_store, None, provider_name, self.fence_token_storage)

        self.assertIsNone(self.cache_api.get(namespace=provider_name, key=caller_uid))
        provider_user = ProviderUser(ftvm.provider_name, real_user_id)
        self.assertIsNone(self.fence_token_storage.delete(provider_user))

        with self.assertRaises(exceptions.NotFound):
            ftvm.get_service_account_key_json(UserInfo(caller_uid, "splat@bar.com", "fake_token_too", 10))

    @staticmethod
    def _mock_fence_api(service_account_json):
        fence_api = FenceApi("")
        fence_api.get_credentials_google = MagicMock(return_value=service_account_json)
        return fence_api

    @staticmethod
    def _mock_sam_api(subject_id, email):
        sam_api = SamApi("")
        sam_api.user_info = MagicMock(return_value={SamKeys.USER_ID_KEY: subject_id, SamKeys.USER_EMAIL_KEY: email})
        return sam_api

    @staticmethod
    def _mock_oauth_adapter(access_token):
        oauth_adapter = OauthAdapter("", "", "", "")
        oauth_adapter.refresh_access_token = MagicMock(return_value={"access_token": access_token})
        return oauth_adapter

    @staticmethod
    def _random_subject_id():
        return ''.join(random.choice(string.digits) for _ in list(range(21)))
