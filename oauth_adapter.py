from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session
from requests_toolbelt.adapters import appengine

# https://toolbelt.readthedocs.io/en/latest/adapters.html#appengineadapter
appengine.monkeypatch()


class OauthAdapter:

    def __init__(self, client_id, client_secret, redirect_url, token_url):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_url = redirect_url
        self.token_url = token_url
        self.basic_auth = HTTPBasicAuth(self.client_id, self.client_secret)

    def exchange_authz_code(self, authz_code):
        """
        Perform an authorization code exchange to get a token dict that includes an access token and a refresh token
        :param authz_code: The authorization code provided by the Oauth authorization response
        :return: A token dict including the access token, refresh token, and token type (amongst other details)
        """
        oauth = OAuth2Session(self.client_id, redirect_uri=self.redirect_url)
        return oauth.fetch_token(self.token_url, code=authz_code, auth=self.basic_auth)

    def refresh_access_token(self, token_dict):
        """
        Take a token dict which must include a 'refresh_token', 'access_token', and 'token_type'. Uses that token dict
        to get a new/refreshed token dict from the Oauth provider
        :param token_dict: A token dict like that returned from :func:`exchange_authz_code` or this method.  It must
        have keys for "access_token", "refresh_token", and "token_type"
        :return: A token dict including the access token, refresh token, and token type (amongst other details)
        """
        oauth = OAuth2Session(self.client_id, token=token_dict)
        return oauth.refresh_token(self.token_url, auth=self.basic_auth)
