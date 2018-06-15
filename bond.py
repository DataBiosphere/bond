from datetime import datetime
from jwt_token import JwtToken
from token_store import TokenStore


class Bond:
    def __init__(self, oauth_adapter):
        self.oauth_adapter = oauth_adapter

    def exchange_authz_code(self, authz_code, user_id):
        """
        Given an authz_code and user information, exchange that code for an OAuth Access Token and Refresh Token.  Store
        the refresh token for later, and return the datetime the token was issued along with the username for whom it
        was issued to by the OAuth provider.
        :param authz_code: Authorization code from OAuth provider
        :param user_id: Unique identifier string of the user who issued the request to Bond (not necessarily the same as
        the username for whom the refresh token was issued by the OAuth provider)
        :return: Two values: datetime when token was issued, username for whom the token was issued
        """
        token_response = self.oauth_adapter.exchange_authz_code(authz_code)
        jwt_token = JwtToken(token_response.get(FenceKeys.ID_TOKEN))
        TokenStore.save(user_id, token_response.get(FenceKeys.REFRESH_TOKEN_KEY), jwt_token.issued_at, jwt_token.username)
        return jwt_token.issued_at, jwt_token.username

    def access_token_for_user(self, user_id):
        """
        Given a user's unique id, lookup their refresh token and use it to generate a new refresh token from their OAuth
        provider.  If a refresh token cannot be found for the user_id provided, a MissingTokenError will be raised.
        :param user_id: Unique identifier string of the user who issued the request to Bond (not necessarily the same as
        the username for whom the refresh token was issued by the OAuth provider)
        :return: Two values: An Access Token string, datetime when that token expires
        """
        refresh_token = TokenStore.lookup(user_id)
        if refresh_token is not None:
            token_response = self.oauth_adapter.refresh_access_token(refresh_token.token)
            expires_at = datetime.fromtimestamp(token_response.get(FenceKeys.EXPIRES_AT_KEY))
            return token_response.get("access_token"), expires_at
        else:
            raise Bond.MissingTokenError("Could not find refresh token for user")

    class MissingTokenError(Exception):
        pass


class FenceKeys:
    """
    Namespaced set of keys expected to be included in a token response from the Fence OAuth provider.
    """
    REFRESH_TOKEN_KEY = 'refresh_token'
    EXPIRES_AT_KEY = 'expires_at'
    ACCESS_TOKEN_KEY = 'access_token'
    ID_TOKEN = 'id_token'
