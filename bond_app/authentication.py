import hashlib
import logging
from .sam_api import SamKeys
from werkzeug import exceptions


class UserInfo:
    def __init__(self, id, email, token, expires_in):
        self.id = id
        self.email = email
        self.token = token
        self.expires_in = expires_in

    def __str__(self):
        return 'id: {}, email: {}, token: {}, expires_id: {}'.format(self.id, self.email, self.token, self.expires_in)

    def __eq__(self, other):
        if isinstance(self, other.__class__):
            return self.__dict__ == other.__dict__
        return False

    def __ne__(self, other):
        return not self.__eq__(other)


class AuthenticationConfig:
    def __init__(self, max_token_life):
        self.max_token_life = max_token_life


class Authentication:
    def __init__(self, config, cache_api, sam_api):
        """
        :param config: An AuthenticationConfig instance.
        :param cache_api: A CacheApi instance.
        """
        self.config = config
        self.cache_api = cache_api
        self.sam_api = sam_api

    def auth_user(self, request_state):
        """
        Authenticate the user with Sam and return the Sam user id. Cache Sam user info by token.
        Verifies the user is enabled in Sam and throws unauthorized errors as appropriate.
        :param request_state: self.request_state from a class extending protorpc.remote.Service
        :return: UserId from Sam
        """
        auth_header = request_state.headers.get('Authorization')
        if auth_header is None:
            raise exceptions.Unauthorized('Request missing Authorization header.')

        auth_header_parts = auth_header.split()
        if len(auth_header_parts) != 2 or auth_header_parts[0].lower() != 'bearer':
            raise exceptions.Unauthorized('Malformed Authorization header, must be in the form of "bearer [token]".')

        token = auth_header_parts[1]
        # SHA256 the token so that it's a consistent length guaranteed to be less that 1500 bytes.
        cache_key = hashlib.sha256(str.encode(token)).hexdigest()

        # First check cache for Sam user info.
        sam_user_info = self.cache_api.get(namespace="SamUserInfo", key=cache_key)

        # If cache lookup failed, call Sam.
        # Note this will raise Unauthorized errors as appropriate.
        if sam_user_info is None:
            sam_user_info = self.sam_api.user_info(token)
            # cache successful Sam responses for 10 minutes.
            cache_result = self.cache_api.add(namespace="SamUserInfo", key=cache_key,
                                              value=sam_user_info, expires_in=self.config.max_token_life)
            if not cache_result:
                logging.warning('Unable to cache Sam lookup for user info: {}'.format(sam_user_info))

        return sam_user_info[SamKeys.USER_ID_KEY]
