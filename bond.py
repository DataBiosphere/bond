from datetime import datetime
from jwt_token import JwtToken
from token_store import TokenStore
from sam_api import SamKeys
import endpoints


class Bond:
    def __init__(self, oauth_adapter, fence_api, sam_api, fence_tvm, provider_name, user_name_path_expr):
        self.oauth_adapter = oauth_adapter
        self.fence_api = fence_api
        self.sam_api = sam_api
        self.fence_tvm = fence_tvm
        self.provider_name = provider_name
        self.user_name_path_expr = user_name_path_expr

    def build_authz_url(self, scopes, redirect_uri, state=None):
        """
        Builds an OAuth authorization URL that a user must use to initiate the OAuth dance.
        :param scopes: Array of scopes (0 to many) that the client requires
        :param redirect_uri: A URL encoded string representing the URI that the Authorizing Service will redirect the
        user to after the user successfully authorizes this client
        :param state: A URL encoded Base64 string representing a JSON object of state information that the requester requires
        back with the redirect
        :return: A plain (not URL encoded) String
        """
        return self.oauth_adapter.build_authz_url(scopes, redirect_uri, state)

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
        user_id = self.sam_api.user_info(user_info.token)[SamKeys.USER_ID_KEY]
        if FenceKeys.REFRESH_TOKEN not in token_response:
            raise endpoints.BadRequestException("authorization response did not include " + FenceKeys.REFRESH_TOKEN)
        TokenStore.save(user_id, token_response.get(FenceKeys.REFRESH_TOKEN), jwt_token.issued_at,
                        jwt_token.username, self.provider_name)
        return jwt_token.issued_at, jwt_token.username

    def generate_access_token(self, user_info):
        """
        Given a user, lookup their refresh token and use it to generate a new refresh token from their OAuth
        provider.  If a refresh token cannot be found for the user_id provided, a MissingTokenError will be raised.
        :param user_info: Information of the user who issued the request to Bond (not necessarily the same as
        the username for whom the refresh token was issued by the OAuth provider)
        :return: Two values: An Access Token string, datetime when that token expires
        """
        user_id = self.sam_api.user_info(user_info.token)[SamKeys.USER_ID_KEY]
        refresh_token = TokenStore.lookup(user_id, self.provider_name)
        if refresh_token is not None:
            token_response = self.oauth_adapter.refresh_access_token(refresh_token.token)
            expires_at = datetime.fromtimestamp(token_response.get(FenceKeys.EXPIRES_AT))
            return token_response.get("access_token"), expires_at
        else:
            raise Bond.MissingTokenError("Could not find refresh token for user")

    def unlink_account(self, user_info):
        """
        Revokes user's refresh token and deletes the linkage from the system
        :param user_info:
        :return:
        """
        user_id = self.sam_api.user_info(user_info.token)[SamKeys.USER_ID_KEY]
        refresh_token = TokenStore.lookup(user_id, self.provider_name)
        if refresh_token:
            self.fence_tvm.remove_service_account(user_id)
            self.oauth_adapter.revoke_refresh_token(refresh_token.token)
            TokenStore.delete(user_id, self.provider_name)

    def get_link_info(self, user_info):
        """
        Get information about a account link
        :param user_info: Information of the user who issued the request to Bond (not necessarily the same as
        the username for whom the refresh token was issued by the OAuth provider)
        :return: refresh_token
        """
        user_id = self.sam_api.user_info(user_info.token)[SamKeys.USER_ID_KEY]
        return TokenStore.lookup(user_id, self.provider_name)

    class MissingTokenError(Exception):
        pass


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
