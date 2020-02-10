from datetime import datetime
import logging
from .jwt_token import JwtToken
from .sam_api import SamKeys

from werkzeug import exceptions


class Bond:
    def __init__(self,
                 oauth_adapter,
                 fence_api,
                 sam_api,
                 refresh_token_store,
                 fence_tvm,
                 provider_name,
                 user_name_path_expr,
                 extra_authz_url_params):

        self.oauth_adapter = oauth_adapter
        self.fence_api = fence_api
        self.sam_api = sam_api
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

    def exchange_authz_code(self, authz_code, redirect_uri, user_info):
        """
        Given an authz_code and user information, exchange that code for an OAuth Access Token and Refresh Token.  Store
        the refresh token for later, and return the datetime the token was issued along with the username for whom it
        was issued to by the OAuth provider.
        :param authz_code: Authorization code from OAuth provider
        :param redirect_uri: redirect url that was used when generating the code - will use default if None
        :param user_info: Information of the user who issued the request to Bond (not necessarily the same as
        the username for whom the refresh token was issued by the OAuth provider)
        :return: Two values: datetime when token was issued, username for whom the token was issued
        """
        token_response = self.oauth_adapter.exchange_authz_code(authz_code, redirect_uri)
        jwt_token = JwtToken(token_response.get(FenceKeys.ID_TOKEN), self.user_name_path_expr)
        user_id = self._fetch_user_id(user_info)
        if FenceKeys.REFRESH_TOKEN not in token_response:
            logging.info(
                "Exchange authz code did not include refresh token in response.\n{}".format(str(token_response)))
            raise exceptions.BadRequest("authorization response did not include " + FenceKeys.REFRESH_TOKEN)
        self.refresh_token_store.save(user_id, token_response.get(FenceKeys.REFRESH_TOKEN), jwt_token.issued_at,
                                      jwt_token.username, self.provider_name)
        return jwt_token.issued_at, jwt_token.username

    def generate_access_token(self, user_info):
        """
        Given a user, lookup their refresh token and use it to generate a new refresh token from their OAuth
        provider.  If a refresh token cannot be found for the user_id provided, a NotFound will be raised.
        :param user_info: Information of the user who issued the request to Bond (not necessarily the same as
        the username for whom the refresh token was issued by the OAuth provider)
        :return: Two values: An Access Token string, datetime when that token expires
        """
        user_id = self._fetch_user_id(user_info)
        refresh_token = self.refresh_token_store.lookup(user_id, self.provider_name)
        if refresh_token is not None:
            token_response = self.oauth_adapter.refresh_access_token(refresh_token.token)
            expires_at = datetime.fromtimestamp(token_response.get(FenceKeys.EXPIRES_AT))
            return token_response.get("access_token"), expires_at
        else:
            raise exceptions.NotFound(
                "Could not find refresh token for user_id: {} provider_name: {}\nConsider relinking your account to Bond.".format(
                    user_id, self.provider_name))

    def unlink_account(self, user_info):
        """
        Revokes user's refresh token and deletes the linkage from the system
        :param user_info:
        :return:
        """
        user_id = self._fetch_user_id(user_info)
        refresh_token = self.refresh_token_store.lookup(user_id, self.provider_name)
        if refresh_token:
            self.fence_tvm.remove_service_account(user_id)
            self.oauth_adapter.revoke_refresh_token(refresh_token.token)
            self.refresh_token_store.delete(user_id, self.provider_name)
        else:
            logging.warning(
                "Tried to remove user refresh token, but none was found: user_id: {}, provider_name: {}".format(user_id,
                                                                                                                self.provider_name))

    def get_link_info(self, user_info):
        """
        Get information about a account link
        :param user_info: Information of the user who issued the request to Bond (not necessarily the same as
        the username for whom the refresh token was issued by the OAuth provider)
        :return: RefreshTokenInfo or None if not found.
        """
        user_id = self._fetch_user_id(user_info)
        return self.refresh_token_store.lookup(user_id, self.provider_name)

    def _fetch_user_id(self, user_info):
        sam_result = self.sam_api.user_info(user_info.token)
        if sam_result is None:
            raise exceptions.Unauthorized("user not found in sam")
        return sam_result[SamKeys.USER_ID_KEY]


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
