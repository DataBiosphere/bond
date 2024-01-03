import hashlib
import unittest

from werkzeug import exceptions
from mock import MagicMock

from bond_app.authentication import Authentication, AuthenticationConfig, UserInfo
from bond_app.sam_api import SamApi, SamKeys
from tests.unit.fake_cache_api import FakeCacheApi
import time


class TestRequestState:
    def __init__(self, auth_header):
        self.headers = {}
        if auth_header is not None:
            self.headers['Authorization'] = auth_header


class AuthenticationTestCase(unittest.TestCase):

    def setUp(self):
        self.cache_api = FakeCacheApi()
        self.sam_api = SamApi("")
        self.auth = Authentication(AuthenticationConfig(600),
                                   self.cache_api, self.sam_api)

    def test_good_user_no_cached_info(self):
        # set up mock Sam
        token = "testtoken"
        expected_user_info = UserInfo("193481341723041", "foo@bar.com", token, 100)
        cache_key = hashlib.sha256(str.encode(token)).hexdigest()
        sam_user_info = self._generate_sam_user_info(expected_user_info.id, expected_user_info.email, True)
        self.sam_api.user_info = MagicMock(return_value=sam_user_info)

        # make request and validate returned user id
        sam_user_id = self.auth.auth_user(TestRequestState('bearer ' + token))
        self.assertEqual(expected_user_info.id, sam_user_id)

        # sam user info should now be cached
        cached_sam_user_info = self.cache_api.get(namespace="SamUserInfo", key=cache_key)
        self.assertEqual(sam_user_info, cached_sam_user_info)

    def test_good_user_sam_info_cached(self):
        # populate cache
        token = "testtoken"
        expected_user_info = UserInfo("193481341723041", "foo@bar.com", token, 100)
        cache_key = hashlib.sha256(str.encode(token)).hexdigest()
        sam_user_info = self._generate_sam_user_info(expected_user_info.id, expected_user_info.email, True)
        self.cache_api.add(namespace="SamUserInfo", key=cache_key, expires_in=0, value=sam_user_info)

        # set up mock Sam to throw an exception
        mock = MagicMock()
        mock.side_effect=Exception("shouldn't be called")
        self.sam_api.user_info = mock

        # make request and validate returned user id
        sam_user_id = self.auth.auth_user(TestRequestState('bearer ' + token))
        self.assertEqual(expected_user_info.id, sam_user_id)

        # sam user info should still be cached
        cached_sam_user_info = self.cache_api.get(namespace="SamUserInfo", key=cache_key)
        self.assertEqual(sam_user_info, cached_sam_user_info)

    def test_good_user_cache_expire_config(self):
        # populate cache with 1 second expiry
        token = "testtoken"
        expected_user_info = UserInfo("193481341723041", "foo@bar.com", token, 100)
        cache_key = hashlib.sha256(str.encode(token)).hexdigest()
        sam_user_info = self._generate_sam_user_info(expected_user_info.id, expected_user_info.email, True)
        self.cache_api.add(namespace="SamUserInfo", key=cache_key, expires_in=1, value=sam_user_info)

        # set up mock Sam to throw an exception
        mock = MagicMock()
        mock.side_effect=exceptions.Unauthorized("Sam error!")
        self.sam_api.user_info = mock

        # make request and validate returned user id
        sam_user_id = self.auth.auth_user(TestRequestState('bearer ' + token))
        self.assertEqual(expected_user_info.id, sam_user_id)

        # wait 2 seconds
        time.sleep(2)

        # make request again, cache should have expired and throw 401
        with self.assertRaises(exceptions.Unauthorized):
            self.auth.auth_user(TestRequestState('bearer ' + token))

    def test_sam_error(self):
        # set up mock Sam to throw an error
        token = "testtoken"
        mock = MagicMock()
        mock.side_effect=exceptions.Unauthorized("Sam error!")
        self.sam_api.user_info = mock

        # request should return 401
        with self.assertRaises(exceptions.Unauthorized):
            self.auth.auth_user(TestRequestState('bearer ' + token))


    def test_missing_auth_header(self):
        # request should return 401 for no auth token
        with self.assertRaises(exceptions.Unauthorized):
            self.auth.auth_user(TestRequestState(None))

    def _generate_sam_user_info(self, user_id, email, enabled):
        return {SamKeys.USER_ID_KEY: user_id, SamKeys.USER_EMAIL_KEY: email, SamKeys.USER_ENABLED_KEY: enabled}
