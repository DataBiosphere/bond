import urllib
import json
import endpoints
import os
import logging

from google.appengine.api import memcache
from google.appengine.api import urlfetch

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
    result = urlfetch.fetch(
        '%s?%s' % (_TOKENINFO_URL, urllib.urlencode({'access_token': token})))
    if result.status_code != 200:
        raise endpoints.InternalServerErrorException(message='Token info endpoint returned status {}: {}'.format(result.status_code, result.content))
    return result.content


class AuthenticationConfig:
    def __init__(self, accepted_audience_prefixes, accepted_email_suffixes, max_token_life):
        self.accepted_audience_prefixes = accepted_audience_prefixes
        self.accepted_email_suffixes = accepted_email_suffixes
        self.max_token_life = max_token_life


def default_config():
    return AuthenticationConfig(os.environ['BOND_ACCEPTED_AUDIENCE_PREFIXES'].split(),
                                os.environ['BOND_ACCEPTED_EMAIL_SUFFIXES'].split(),
                                os.environ.get('BOND_MAX_TOKEN_LIFE', 600))


class Authentication:
    def __init__(self, config):
        self.config = config

    def require_user_info(self, request_state, token_info_fn=_token_info):
        """Get the user's info from cache or from google if not in cache, throwing unauthorized errors as appropriate

        :param request_state: self.request_state from a class extending protorpc.remote.Service
        :param token_info_fn: function to get token info, defaults to google http request, override for testing one
        parameter, the token string, returns UserInfo
        :return: UserInfo instance
        """
        auth_header = request_state.headers.get('Authorization')
        if auth_header is None:
            raise endpoints.UnauthorizedException(message='Request missing Authorization header.')

        auth_header_parts = auth_header.split()
        if len(auth_header_parts) != 2 or auth_header_parts[0].lower() != 'bearer':
            raise endpoints.UnauthorizedException(message='Malformed Authorization header.')

        token = auth_header_parts[1]

        user_info = memcache.get(key=token)
        if user_info is None:
            user_info = self._fetch_user_info(token, token_info_fn)
            # cache for 10 minutes or until token expires
            expires_in = min([user_info.expires_in, self.config.max_token_life])
            logging.debug("caching token {} for {} seconds".format(token, expires_in))
            memcache.add(key=token, value=user_info, time=expires_in)
        else:
            logging.debug("auth token cache hit for token %s", token)

        return user_info

    def _fetch_user_info(self, token, token_info_fn):
        """Make the external call to get token info and create UserInfo object"""
        # Get token info from the tokeninfo endpoint.
        result = token_info_fn(token)

        token_info = json.loads(result)
        logging.debug("token info for %s: %s", token, json.dumps(token_info))

        # Validate email.
        if 'email' not in token_info:
            raise endpoints.UnauthorizedException(message='Oauth token doesn\'t include an email address.')
        if not token_info.get('verified_email'):
            raise endpoints.UnauthorizedException(message='Oauth token email isn\'t verified.')
        if 'user_id' not in token_info:
            raise endpoints.UnauthorizedException(message='Oauth token doesn\'t include user_id.')
        if 'audience' not in token_info:
            raise endpoints.UnauthorizedException(message='Oauth token doesn\'t include audience.')

        # Validate audience.
        audience = token_info.get('audience')
        if any(audience.startswith(prefix) for prefix in self.config.accepted_audience_prefixes) or \
                any(token_info.get('email').endswith(suffix) for suffix in self.config.accepted_email_suffixes):
            return UserInfo(token_info.get('user_id'), token_info.get('email'), token, int(token_info.get('expires_in')))

        else:
            raise endpoints.UnauthorizedException(message='Oauth token has unacceptable audience: {}.'.format(audience))
