from datetime import datetime, timedelta
import logging
from .jwt_token import JwtToken

from werkzeug import exceptions


class Bond:
    def __init__(self,
                 oauth_adapter,
                 fence_api,
                 cache_api,
                 refresh_token_store,
                 fence_tvm,
                 provider_name,
                 user_name_path_expr,
                 extra_authz_url_params):

        self.oauth_adapter = oauth_adapter
        self.fence_api = fence_api
        self.cache_api = cache_api
        self.refresh_token_store = refresh_token_store
        self.fence_tvm = fence_tvm
        self.provider_name = provider_name
        self.user_name_path_expr = user_name_path_expr
        self.extra_authz_url_params = extra_authz_url_params

    def build_authz_url(self, scopes, redirect_uri, state=None):
        """
        Builds an OAuth authorization URL that a user must use to initiate the OAuth dance.  Will automatically append
        all `self.extra_authz_url_params` to the resulting url.
        :param scopes: Array of scopes (0 to many) that the client requires
        :param redirect_uri: A URL encoded string representing the URI that the Authorizing Service will redirect the
        user to after the user successfully authorizes this client
        :param state: A URL encoded Base64 string representing a JSON object of state information that the requester requires
        back with the redirect
        :return: A plain (not URL encoded) String
        """
        return self.oauth_adapter.build_authz_url(scopes, redirect_uri, state, self.extra_authz_url_params)

    def exchange_authz_code(self, authz_code, redirect_uri, sam_user_id):
        """
        Given an authz_code and user information, exchange that code for an OAuth Access Token and Refresh Token.  Store
        the refresh token for later, and return the datetime the token was issued along with the username for whom it
        was issued to by the OAuth provider.
        :param authz_code: Authorization code from OAuth provider
        :param redirect_uri: redirect url that was used when generating the code - will use default if None
        :param sam_user_id: Id stored in Sam for user who initiated request
        :return: Two values: datetime when token was issued, username for whom the token was issued
        """
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
        Given a user, lookup their refresh token (if not provided) and use it to retrieve an access token from their OAuth
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
            cached_access_data = self.cache_api.get(namespace="AccessTokens", key=sam_user_id)
            if cached_access_data and cached_access_data.get(FenceKeys.ACCESS_TOKEN):
                expires_at = cached_access_data.get(FenceKeys.EXPIRES_AT)
                access_token = cached_access_data.get(FenceKeys.ACCESS_TOKEN)
                expires_in_cache = (expires_at - datetime.now()).total_seconds() - refresh_threshold
                logging.debug(
                    "Retrieved access token from cache. " +
                    f"Access token will expire in {expires_in_cache:.2f} seconds. " +
                    f"SAM user ID: {sam_user_id}. Provider: {self.provider_name}"
                )
            else:
                access_token, expires_at = self.generate_access_token(sam_user_id, refresh_token=refresh_token)
                expires_in_cache = (expires_at - datetime.now()).total_seconds() - refresh_threshold
                logging.debug(
                    "Generated new access token. " +
                    f"Access token will expire in {expires_in_cache:.2f} seconds. " +
                    f"SAM user ID: {sam_user_id}. Provider: {self.provider_name}"
                )
                
                self.cache_api.add(
                    namespace="AccessTokens", 
                    key=sam_user_id, 
                    value={
                        FenceKeys.EXPIRES_AT: expires_at,
                        FenceKeys.ACCESS_TOKEN: access_token,
                    },
                    expires_in=expires_in_cache,
                )
            return access_token, expires_at
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
