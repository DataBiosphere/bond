import base64
import json
from datetime import datetime
import logging
from .jwt_token import JwtToken

from werkzeug import exceptions
from dataclasses import dataclass

from .oauth2_state_store import OAuth2StateStore


class Bond:
    def __init__(self,
                 oauth_adapter,
                 fence_api,
                 cache_api,
                 refresh_token_store,
                 oauth2_state_store,
                 fence_tvm,
                 provider_name,
                 user_name_path_expr,
                 extra_authz_url_params):

        self.oauth_adapter = oauth_adapter
        self.fence_api = fence_api
        self.cache_api = cache_api
        self.refresh_token_store = refresh_token_store
        self.oauth2_state_store = oauth2_state_store
        self.fence_tvm = fence_tvm
        self.provider_name = provider_name
        self.user_name_path_expr = user_name_path_expr
        self.extra_authz_url_params = extra_authz_url_params

    def build_authz_url(self, scopes, redirect_uri, sam_user_id, provider, state=None):
        """
        Builds an OAuth authorization URL that a user must use to initiate the OAuth dance.  Will automatically append
        all `self.extra_authz_url_params` to the resulting url.
        :param scopes: Array of scopes (0 to many) that the client requires
        :param redirect_uri: A URL encoded string representing the URI that the Authorizing Service will redirect the
        user to after the user successfully authorizes this client
        :param sam_user_id: The Sam user of this request
        :param provider: The OAuth Provider of this request
        :param state: A URL encoded Base64 string representing a JSON object of state information that the requester requires
        back with the redirect
        :return: A plain (not URL encoded) String
        """
        encoded_state_with_nonce, nonce = self.oauth2_state_store.state_with_nonce(state)
        authz_url = self.oauth_adapter.build_authz_url(scopes, redirect_uri, encoded_state_with_nonce,
                                                       self.extra_authz_url_params)
        # save nonce after creating authz_url so that we don't save states of invalid requests
        self.oauth2_state_store.save(sam_user_id, provider, nonce)
        return authz_url

    def exchange_authz_code(self, authz_code, redirect_uri, sam_user_id, b64_state, provider):
        """
        Given an authz_code and user information, exchange that code for an OAuth Access Token and Refresh Token.  Store
        the refresh token for later, and return the datetime the token was issued along with the username for whom it
        was issued to by the OAuth provider.
        :param authz_code: Authorization code from OAuth provider
        :param redirect_uri: redirect url that was used when generating the code - will use default if None
        :param sam_user_id: Id stored in Sam for user who initiated request
        :param b64_state: Base64-encoded state with OAuth2State nonce
        :param provider: OAuth provider
        :return: Two values: datetime when token was issued, username for whom the token was issued
        """
        decoded_state = base64.b64decode(b64_state)
        state = json.loads(decoded_state)
        if 'nonce' not in state:
            raise exceptions.InternalServerError("Invalid OAuth2 State: No nonce provided")
        state_valid = self.oauth2_state_store.validate_and_delete(sam_user_id, provider, state['nonce'])
        if not state_valid:
            raise exceptions.InternalServerError("Invalid OAuth2 State: Invalid nonce")
        token_response = self.oauth_adapter.exchange_authz_code(authz_code, redirect_uri)
        jwt_token = JwtToken(token_response.get(FenceKeys.ID_TOKEN), self.user_name_path_expr)
        if FenceKeys.REFRESH_TOKEN not in token_response:
            logging.info(
                "Exchange authz code did not include refresh token in response.\n{}".format(str(token_response)))
            raise exceptions.BadRequest("authorization response did not include " + FenceKeys.REFRESH_TOKEN)

        if self.refresh_token_store.lookup(sam_user_id, self.provider_name) is not None:
            # clear out any existing information if user has previously linked this account before relinking
            self.unlink_account(sam_user_id)
        self.refresh_token_store.save(sam_user_id, token_response.get(FenceKeys.REFRESH_TOKEN), jwt_token.issued_at,
                                      jwt_token.username, self.provider_name)
        return jwt_token.issued_at, jwt_token.username


    def generate_access_token(self, sam_user_id, refresh_token=None):
        """
        Given a user, lookup their refresh token (if not provided) and use it to generate a new access token from their OAuth
        provider.  If a refresh token cannot be found for the sam_user_id provided, a NotFound will be raised.
        :param sam_user_id: Id stored in Sam for user who initiated request
        :param refresh_token: a refresh token (optional). 
        If not present, the refresh token will be found using the "sam_user_id" parameter.
        :return: Two values: An Access Token string, datetime when that token expires
        """

        refresh_token = refresh_token or self.refresh_token_store.lookup(sam_user_id, self.provider_name)
        if refresh_token is not None:
            token_response = self.oauth_adapter.refresh_access_token(refresh_token.token)
            expires_at = datetime.fromtimestamp(token_response.get(FenceKeys.EXPIRES_AT))
            return token_response.get("access_token"), expires_at
        else:
            raise exceptions.NotFound(
                "Could not find refresh token for sam_user_id: {} provider_name: {}\nConsider relinking your account to Bond.".format(
                    sam_user_id, self.provider_name))


    def get_access_token(self, sam_user_id, refresh_threshold: int = 600):
        """
        Given a user, lookup their refresh token and use it to retrieve an access token from their OAuth
        provider.
        If an access token was already generated for the user, 
        and that token has greater than `refresh_threshold` seconds before expiration, return that token. 
        Otherwise, generate a new token.
        
        If a refresh token cannot be found for the sam_user_id provided, a NotFound will be raised.
        :param sam_user_id: Id stored in Sam for user who initiated request
        :return: Two values: An Access Token string, datetime when that token expires
        """
        refresh_token = self.refresh_token_store.lookup(sam_user_id, self.provider_name)
        if refresh_token is not None:
            access_token: FenceAccessToken = self.cache_api.get(
                namespace=f"{self.provider_name}:AccessTokens", 
                key=sam_user_id,
            )
            if access_token:
                expires_at = access_token.expires_at
                access_token_value = access_token.value
                logging.debug(
                    "Retrieved access token from cache. " +
                    f"Access token will expire at {expires_at}. " +
                    f"SAM user ID: {sam_user_id}. Provider: {self.provider_name}"
                )
            else:
                access_token_value, expires_at = self.generate_access_token(sam_user_id, refresh_token=refresh_token)
                logging.debug(
                    "Generated new access token. " +
                    f"Access token will expire at {expires_at} seconds. " +
                    f"SAM user ID: {sam_user_id}. Provider: {self.provider_name}"
                )
                self.cache_api.add(
                    namespace=f"{self.provider_name}:AccessTokens", 
                    key=sam_user_id, 
                    value=FenceAccessToken(value=access_token_value, expires_at=expires_at),
                    expires_in=(expires_at - datetime.now()).total_seconds() - refresh_threshold,
                )
            return access_token_value, expires_at
        else:
            raise exceptions.NotFound(
                "Could not find refresh token for sam_user_id: {} provider_name: {}\nConsider relinking your account to Bond.".format(
                    sam_user_id, self.provider_name))
            
    def unlink_account(self, sam_user_id):
        """
        Revokes user's refresh token and deletes the linkage from the system
        :param sam_user_id: Id stored in Sam for user who initiated request
        :return:
        """
        refresh_token = self.refresh_token_store.lookup(sam_user_id, self.provider_name)
        if refresh_token:
            self.fence_tvm.remove_service_account(sam_user_id)
            self.oauth_adapter.revoke_refresh_token(refresh_token.token)
            self.refresh_token_store.delete(sam_user_id, self.provider_name)
            self.cache_api.delete(key=sam_user_id, namespace=f"{self.provider_name}:AccessTokens")
        else:
            logging.warning(
                "Tried to remove user refresh token, but none was found: sam_user_id: {}, provider_name: {}".format(sam_user_id,
                                                                                                                self.provider_name))

    def get_link_info(self, sam_user_id):
        """
        Get information about a account link
        :param sam_user_id: Id stored in Sam for user who initiated request
        :return: RefreshTokenInfo or None if not found.
        """
        return self.refresh_token_store.lookup(sam_user_id, self.provider_name)


class FenceKeys:
    """
    Namespaced set of keys expected to be included in a token response from the Fence OAuth provider.
    """
    REFRESH_TOKEN = 'refresh_token'
    EXPIRES_AT = 'expires_at'
    EXPIRES_IN = 'expires_in'
    ACCESS_TOKEN = 'access_token'
    ID_TOKEN = 'id_token'
    TOKEN_TYPE = 'token_type'


@dataclass
class FenceAccessToken:
    """
    Simple data class for representing a Fence access token.
    """
    value: str
    expires_at: datetime

