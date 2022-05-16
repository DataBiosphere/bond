import urllib.request, urllib.parse, urllib.error
import json
import logging
from .sam_api import SamKeys

from werkzeug import exceptions
import requests
import jwt
from jwt import PyJWKClient


_TOKENINFO_URL = 'https://www.googleapis.com/oauth2/v1/tokeninfo'


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


def _token_info(token):
    result = requests.get(
        '{}?{}'.format(_TOKENINFO_URL, urllib.parse.urlencode({'access_token': token})))

    if result.status_code == 400 or result.status_code == 404:
        raise exceptions.Unauthorized("Invalid authorization token. {}".format(result.content))
    if result.status_code != 200:
        raise exceptions.InternalServerError('Token info endpoint returned status {}: {}'.format(result.status_code, result.content))

    return result.content

def _decode_jwt(token, jwks_uri, audience):
    jwks_client = PyJWKClient(jwks_uri)
    signing_key = jwks_client.get_signing_key_from_jwt(token)
    data = jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        audience=audience,
        options={
            'verify_signature': True, 
            'require': ["email", "sub", "exp", "iat"]
        }
    )
    return data

class AuthenticationConfig:
    def __init__(self, accepted_audience_prefixes, accepted_email_suffixes, max_token_life, b2c_authority_endpoint=None, b2c_audience=None):
        self.accepted_audience_prefixes = accepted_audience_prefixes
        self.accepted_email_suffixes = accepted_email_suffixes
        self.max_token_life = max_token_life
        self.b2c_authority_endpoint = b2c_authority_endpoint
        self.b2c_audience = b2c_audience
        self._process_b2c_metadata()

    def _process_b2c_metadata(self):
        if self.b2c_authority_endpoint:
            metadata_result = requests.get(self.b2c_authority_endpoint + '/.well-known/openid-configuration')
            if metadata_result.status_code != 200:
                raise exceptions.InternalServerError('Could not retrieve metadata from authority: {}'.format(self.b2c_authority_endpoint))
            metadata = json.loads(metadata_result.content)
            if 'jwks_uri' not in metadata:
                raise exceptions.InternalServerError('Could not determine jwks_uri from authority: {}'.format(self.b2c_authority_endpoint))
            self.jwks_uri = metadata.get('jwks_uri')

class Authentication:
    def __init__(self, config, cache_api, sam_api):
        """
        :param config: An AuthenticationConfig instance.
        :param cache_api: A CacheApi instance.
        """
        self.config = config
        self.cache_api = cache_api
        self.sam_api = sam_api

    def auth_user(self, request_state, token_info_fn=_token_info):
        """Get the user's info from cache or from google if not in cache, throwing unauthorized errors as appropriate
        Verify user is registered in Sam with Google user info and return Sam user id

        :param request_state: self.request_state from a class extending protorpc.remote.Service
        :param token_info_fn: function to get token info, defaults to google http request, override for testing one
        parameter, the token string, returns json token info (see https://www.googleapis.com/oauth2/v1/tokeninfo)
        :return: UserId from Sam
        """
        auth_header = request_state.headers.get('Authorization')
        if auth_header is None:
            raise exceptions.Unauthorized('Request missing Authorization header.')

        auth_header_parts = auth_header.split()
        if len(auth_header_parts) != 2 or auth_header_parts[0].lower() != 'bearer':
            raise exceptions.Unauthorized('Malformed Authorization header, must be in the form of "bearer [token]".')

        token = auth_header_parts[1]

        user_info = self.cache_api.get(key='access_token:' + token)
        if user_info is None:
            # First try to validate the token as a JWT.
            if self.config.b2c_authority_endpoint:
                try:
                    user_info = self._fetch_user_info_from_jwt(token)
                except:
                    logging.info("Failed to parse token as a JWT. Falling back to google tokeninfo...")
            
            # Fall back to Google tokeninfo if that fails.
            if user_info is None:
                user_info = self._fetch_user_info_from_google(token, token_info_fn)

            # cache for 10 minutes or until token expires
            expires_in = min([user_info.expires_in, self.config.max_token_life])
            logging.debug("caching token %s for %s seconds", token, expires_in)
            self.cache_api.add(key='access_token:' + token, value=user_info, expires_in=expires_in)
        else:
            logging.debug("auth token cache hit for token %s", token)

        sam_user_info = self.cache_api.get(namespace="SamUserInfo", key=user_info.id)
        if sam_user_info is None:
            sam_user_info = self.sam_api.user_info(user_info.token)
            # cache sam response for 10 minutes
            self.cache_api.add(namespace="SamUserInfo", key=user_info.id,
                               value=sam_user_info, expires_in=self.config.max_token_life)
        else:
            logging.debug("sam user info cache hit for id %s", user_info.id)

        if sam_user_info is None or not sam_user_info[SamKeys.USER_ENABLED_KEY]:
            logging.info(
                "Could not authenticate user {email} with subject id {id} in Sam. User info in Sam: {user_info}"
                .format(email=user_info.email, id=user_info.id, user_info=sam_user_info))
            raise exceptions.Unauthorized("could not authenticate with Sam")

        return sam_user_info[SamKeys.USER_ID_KEY]

    def _fetch_user_info_from_google(self, token, token_info_fn):
        """Make the external call to get token info and create UserInfo object"""
        # Get token info from the tokeninfo endpoint.
        result = token_info_fn(token)

        token_info = json.loads(result)
        logging.debug("token info for %s: %s", token, json.dumps(token_info))

        # Validate token info.
        if 'email' not in token_info:
            raise exceptions.Unauthorized('Oauth token doesn\'t include an email address.')
        if not token_info.get('verified_email'):
            raise exceptions.Unauthorized('Oauth token email isn\'t verified.')
        if 'user_id' not in token_info:
            raise exceptions.Unauthorized('Oauth token doesn\'t include user_id.')
        if 'audience' not in token_info:
            raise exceptions.Unauthorized('Oauth token doesn\'t include audience.')
        if 'expires_in' not in token_info:
            raise exceptions.Unauthorized('Oauth token doesn\'t include expires_in.')
        try:
            expires_in = int(token_info.get('expires_in'))
        except ValueError:
            raise exceptions.Unauthorized('expires_in must be a number')
        if expires_in <= 0:
            raise exceptions.Unauthorized('expires_in must be > 0')

        # Validate audience.
        audience = token_info.get('audience')
        if any(audience.startswith(prefix) for prefix in self.config.accepted_audience_prefixes) or \
                any(token_info.get('email').endswith(suffix) for suffix in self.config.accepted_email_suffixes):
            return UserInfo(token_info.get('user_id'), token_info.get('email'), token, expires_in)

        else:
            raise exceptions.Unauthorized('Oauth token has unacceptable audience: {}.'.format(audience))

    def _fetch_user_info_from_jwt(self, token):
        """Validate and decode the JWT and build the user info"""
        result = _decode_jwt(token, self.config.jwks_uri, self.config.audience)

        token_info = json.loads(result)
        logging.debug("token info for %s: %s", token, json.dumps(token_info))

        # Validate token info
        if 'email' not in token_info:
            raise exceptions.Unauthorized('Oauth token doesn\'t include an email address.')
        if 'sub' not in token_info:
            raise exceptions.Unauthorized('Oauth token doesn\'t include user id.')
        if 'aud' not in token_info:
            raise exceptions.Unauthorized('Oauth token doesn\'t include audience.')
        if 'exp' not in token_info:
            raise exceptions.Unauthorized('Oauth token doesn\'t include exp.')
        try:
            expires_in = int(token_info.get('exp'))
        except ValueError:
            raise exceptions.Unauthorized('exp must be a number')
        if expires_in <= 0:
            raise exceptions.Unauthorized('exp must be > 0')

        return UserInfo(token_info.get('sub'), token_info.get('email'), token, expires_in)
