import unittest

from werkzeug import exceptions
from mock import MagicMock
from http_server_mock import HttpServerMock
from cryptography.hazmat.primitives.asymmetric import rsa
import json
import jwt
from jwt.utils import to_base64url_uint
import time

from bond_app.authentication import Authentication, AuthenticationConfig, UserInfo
from bond_app.sam_api import SamApi, SamKeys
from tests.unit.fake_cache_api import FakeCacheApi

ALGORITHM = "RS256"
PUBLIC_KEY_ID = "sample-key-id"

class TestRequestState:
    def __init__(self, auth_header):
        self.headers = {}
        if auth_header is not None:
            self.headers['Authorization'] = auth_header

class MockOidcServer:
    def __init__(self, public_key):
        super().__init__()
        self.app = HttpServerMock(__name__)
        self.public_key = public_key
        public_numbers = public_key.public_numbers()

        @self.app.route("/.well-known/openid-configuration", methods=["GET"])
        def metadata():
            return json.dumps({'jwks_uri': 'http://localhost:5000/keys'})

        @self.app.route("/keys", methods=["GET"])
        def jwks():
            return json.dumps({
                'keys': [
                    {
                        'kid': PUBLIC_KEY_ID,
                        'alg': ALGORITHM,
                        'kty': "RSA",
                        'use': "sig",
                        'n': to_base64url_uint(public_numbers.n).decode("ascii"),
                        'e': to_base64url_uint(public_numbers.e).decode("ascii")
                    }
                ]
            })


class AuthenticationTestCase(unittest.TestCase):

    def setUp(self):
        self.cache_api = FakeCacheApi()
        self.sam_api = SamApi("")
        self.auth = Authentication(AuthenticationConfig( ['32555940559'], ['.gserviceaccount.com'], 600), self.cache_api, self.sam_api)
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.public_key = self.private_key.public_key()
        self.mock_server = MockOidcServer(self.public_key)

    def test_good_user_no_cached_info(self):
        token = "testtoken"
        expected_user_info = UserInfo("193481341723041", "foo@bar.com", token, 100)
        self.sam_api.user_info = MagicMock(
            return_value=self._generate_sam_user_info(expected_user_info.id, expected_user_info.email, True))

        def token_fn(token):
            token_data = {
                "audience": "32555940559.apps.googleusercontent.com",
                "user_id": expected_user_info.id,
                "expires_in": expected_user_info.expires_in,
                "email": expected_user_info.email,
                "verified_email": True
            }
            return json.dumps(token_data)

        sam_user_id = self.auth.auth_user(TestRequestState('bearer ' + token), token_fn)
        self.assertEqual(expected_user_info.id, sam_user_id)

    def test_good_user_sam_info_cached(self):
        token = "testtoken"
        expected_user_info = UserInfo("193481341723041", "foo@bar.com", token, 100)
        self.cache_api.add(namespace="SamUserInfo", key=expected_user_info.id, expires_in=0,
                           value=self._generate_sam_user_info(expected_user_info.id, expected_user_info.email, True))

        def token_fn(token):
            token_data = {
                "audience": "32555940559.apps.googleusercontent.com",
                "user_id": expected_user_info.id,
                "expires_in": expected_user_info.expires_in,
                "email": expected_user_info.email,
                "verified_email": True
            }
            return json.dumps(token_data)

        sam_user_id = self.auth.auth_user(TestRequestState('bearer ' + token), token_fn)
        self.assertEqual(expected_user_info.id, sam_user_id)

    def test_good_user_google_info_cached(self):
        token = "testtoken"
        expected_user_info = UserInfo("193481341723041", "foo@bar.com", token, 100)
        self.cache_api.add(namespace="SamUserInfo", key=expected_user_info.id, expires_in=0,
                           value=self._generate_sam_user_info(expected_user_info.id, expected_user_info.email, True))

        def token_fn(token):
            token_data = {
                "audience": "32555940559.apps.googleusercontent.com",
                "user_id": expected_user_info.id,
                "expires_in": expected_user_info.expires_in,
                "email": expected_user_info.email,
                "verified_email": True
            }
            return json.dumps(token_data)

        self.auth.auth_user(TestRequestState('bearer ' + token), token_fn)

        def token_fn2(token):
            raise Exception("shouldn't be called")

        sam_user_id = self.auth.auth_user(TestRequestState('bearer ' + token), token_fn2)
        self.assertEqual(expected_user_info.id, sam_user_id)

    def test_good_user_cache_expire_token(self):
        token = "testtoken"
        expected_user_info = UserInfo("193481341723041", "foo@bar.com", token, 1)
        self.cache_api.add(namespace="SamUserInfo", key=expected_user_info.id, expires_in=0,
                           value=self._generate_sam_user_info(expected_user_info.id, expected_user_info.email, True))

        def token_fn(token):
            token_data = {
                "audience": "32555940559.apps.googleusercontent.com",
                "user_id": expected_user_info.id,
                "expires_in": expected_user_info.expires_in,
                "email": expected_user_info.email,
                "verified_email": True
            }
            return json.dumps(token_data)

        self.auth.auth_user(TestRequestState('bearer ' + token), token_fn)

        def token_fn2(token):
            raise Exception("should detect this exception")

        import time
        time.sleep(2)

        with self.assertRaises(Exception):
            self.auth.auth_user(TestRequestState('bearer ' + token), token_fn2)

    def test_good_user_cache_expire_config(self):
        auth = Authentication(AuthenticationConfig(['32555940559'], ['.gserviceaccount.com'], 1),
                              self.cache_api, self.sam_api)
        token = "testtoken"
        expected_user_info = UserInfo("193481341723041", "foo@bar.com", token, 100)
        self.cache_api.add(namespace="SamUserInfo", key=expected_user_info.id, expires_in=0,
                           value=self._generate_sam_user_info(expected_user_info.id, expected_user_info.email, True))

        def token_fn(token):
            token_data = {
                "audience": "32555940559.apps.googleusercontent.com",
                "user_id": expected_user_info.id,
                "expires_in": expected_user_info.expires_in,
                "email": expected_user_info.email,
                "verified_email": True
            }
            return json.dumps(token_data)

        auth.auth_user(TestRequestState('bearer ' + token), token_fn)

        def token_fn2(token):
            raise Exception("should detect this exception")

        import time
        time.sleep(2)

        with self.assertRaises(Exception):
            auth.auth_user(TestRequestState('bearer ' + token), token_fn2)

    def test_good_service_account(self):
        pet_token = "testtoken"
        user_token = "differenttoken"
        pet_info = UserInfo("193481341723041", "foo@bar.gserviceaccount.com", pet_token, 100)
        user_info = UserInfo("234567890123456", "foos_owner@bar.com", user_token, 100)
        self.cache_api.add(namespace="SamUserInfo", key=pet_info.id, expires_in=0,
                           value=self._generate_sam_user_info(user_info.id, user_info.email, True))

        def token_fn(token):
            token_data = {
                "audience": pet_info.id,
                "user_id": pet_info.id,
                "expires_in": pet_info.expires_in,
                "email": pet_info.email,
                "verified_email": True
            }
            return json.dumps(token_data)

        sam_user_id = self.auth.auth_user(TestRequestState('bearer ' + pet_token), token_fn)
        self.assertEqual(user_info.id, sam_user_id)

    def test_user_disabled_in_sam(self):
        token = "testtoken"
        expected_user_info = UserInfo("193481341723041", "foo@bar.com", token, 100)
        self.sam_api.user_info = MagicMock(
            return_value=self._generate_sam_user_info(expected_user_info.id, expected_user_info.email, False))

        def token_fn(token):
            token_data = {
                "audience": "32555940559.apps.googleusercontent.com",
                "user_id": expected_user_info.id,
                "expires_in": expected_user_info.expires_in,
                "email": expected_user_info.email,
                "verified_email": True
            }
            return json.dumps(token_data)

        with self.assertRaises(Exception):
            self.auth.auth_user(TestRequestState('bearer ' + token), token_fn)

    def test_pets_user_disabled_in_sam(self):
        pet_token = "testtoken"
        user_token = "differenttoken"
        pet_info = UserInfo("193481341723041", "foo@bar.gserviceaccount.com", pet_token, 100)
        user_info = UserInfo("234567890123456", "foos_owner@bar.com", user_token, 100)
        self.cache_api.add(namespace="SamUserInfo", key=pet_info.id, expires_in=0,
                           value=self._generate_sam_user_info(user_info.id, user_info.email, False))

        def token_fn(token):
            token_data = {
                "audience": pet_info.id,
                "user_id": pet_info.id,
                "expires_in": pet_info.expires_in,
                "email": pet_info.email,
                "verified_email": True
            }
            return json.dumps(token_data)

        with self.assertRaises(Exception):
            self.auth.auth_user(TestRequestState('bearer ' + pet_token), token_fn)

    def test_missing_auth_header(self):
        def token_fn(token):
            raise Exception("shouldn't be called")

        with self.assertRaises(exceptions.Unauthorized):
            self.auth.auth_user(TestRequestState(None), token_fn)

    def _unauthorized_test(self, token_data):
        def token_fn(token):
            return json.dumps(token_data)

        with self.assertRaises(exceptions.Unauthorized):
            self.auth.auth_user(TestRequestState('bearer testtoken'), token_fn)

    def test_missing_email(self):
        token_data = {
            "audience": "32555940559.apps.googleusercontent.com",
            "user_id": "193481341723041",
            "expires_in": 100,
            "verified_email": True
        }
        self._unauthorized_test(token_data)

    def test_unverified_email(self):
        token_data = {
            "audience": "32555940559.apps.googleusercontent.com",
            "user_id": "193481341723041",
            "expires_in": 100,
            "email": "foo@bar.com",
            "verified_email": False
        }
        self._unauthorized_test(token_data)

    def test_missing_user_id(self):
        token_data = {
            "audience": "32555940559.apps.googleusercontent.com",
            "expires_in": 100,
            "email": "foo@bar.com",
            "verified_email": True
        }
        self._unauthorized_test(token_data)

    def test_missing_audience(self):
        token_data = {
            "user_id": "193481341723041",
            "expires_in": 100,
            "email": "foo@bar.com",
            "verified_email": True
        }
        self._unauthorized_test(token_data)

    def test_unacceptable_audience(self):
        token_data = {
            "audience": "baaaaaad.apps.googleusercontent.com",
            "user_id": "193481341723041",
            "expires_in": 100,
            "email": "foo@bar.com",
            "verified_email": True
        }
        self._unauthorized_test(token_data)

    def test_missing_expires_in(self):
        token_data = {
            "audience": "32555940559.apps.googleusercontent.com",
            "user_id": "193481341723041",
            "email": "foo@bar.com",
            "verified_email": True
        }
        self._unauthorized_test(token_data)

    def test_unacceptable_expires_in_1(self):
        token_data = {
            "audience": "32555940559.apps.googleusercontent.com",
            "user_id": "193481341723041",
            "expires_in": -1,
            "email": "foo@bar.com",
            "verified_email": True
        }
        self._unauthorized_test(token_data)

    def test_unacceptable_expires_in_2(self):
        token_data = {
            "audience": "32555940559.apps.googleusercontent.com",
            "user_id": "193481341723041",
            "expires_in": "asdf",
            "email": "foo@bar.com",
            "verified_email": True
        }
        self._unauthorized_test(token_data)

    def test_valid_jwt(self):
        audience = 'my-test-audience'
        epoch_time = int(time.time())
        token_data = {
            "aud": audience,
            "sub": "my-sub",
            "exp": epoch_time + 300,
            "iat": epoch_time,
            "email": "fake@email.com"
        }
        token = self._encode_token(token_data)
        expected_user_info = UserInfo("193481341723041", "foo@bar.com", token, 100)
        self.sam_api.user_info = MagicMock(
            return_value=self._generate_sam_user_info(expected_user_info.id, expected_user_info.email, True))
        with self.mock_server.app.run("localhost", 5000):
            auth = Authentication(
                AuthenticationConfig([], [], 600,
                    'http://localhost:5000',
                    audience
                ), self.cache_api, self.sam_api)
            sam_user_id = auth.auth_user(TestRequestState('bearer ' + token))
            self.assertEqual(expected_user_info.id, sam_user_id)

    def test_jwt_invalid_audience(self):
        epoch_time = int(time.time())
        token_data = {
            "aud": "bad-audience",
            "sub": "my-sub",
            "exp": epoch_time + 300,
            "iat": epoch_time,
            "email": "fake@email.com"
        }
        token = self._encode_token(token_data)
        with self.mock_server.app.run("localhost", 5000):
            auth = Authentication(
                AuthenticationConfig([], [], 600,
                    'http://localhost:5000',
                    'good-audience'
                ), self.cache_api, self.sam_api)
            with self.assertRaises(exceptions.Unauthorized):
                auth.auth_user(TestRequestState('bearer ' + token))

    def test_jwt_fallback_to_google(self):
        with self.mock_server.app.run("localhost", 5000):
            token = "testtoken"
            expected_user_info = UserInfo("193481341723041", "foo@bar.com", token, 100)
            self.sam_api.user_info = MagicMock(
                return_value=self._generate_sam_user_info(expected_user_info.id, expected_user_info.email, True))

            def token_fn(token):
                token_data = {
                    "audience": "32555940559.apps.googleusercontent.com",
                    "user_id": expected_user_info.id,
                    "expires_in": expected_user_info.expires_in,
                    "email": expected_user_info.email,
                    "verified_email": True
                }
                return json.dumps(token_data)

            sam_user_id = self.auth.auth_user(TestRequestState('bearer ' + token), token_fn)
            self.assertEqual(expected_user_info.id, sam_user_id)

    def _generate_sam_user_info(self, user_id, email, enabled):
        return {SamKeys.USER_ID_KEY: user_id, SamKeys.USER_EMAIL_KEY: email, SamKeys.USER_ENABLED_KEY: enabled}

    def _encode_token(self, payload):
        return jwt.encode(
            payload=payload,
            key=self.private_key,
            algorithm='RS256',
            headers={
                'kid': PUBLIC_KEY_ID,
            }
        )
