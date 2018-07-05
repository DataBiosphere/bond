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

    def refresh_access_token(self, refresh_token_str):
        """
        Take a refresh token string to get a new access token from the Oauth provider
        :param refresh_token_str: A refresh token string
        :return: An access token
        """
        token_dict = {'refresh_token': refresh_token_str}
        oauth = OAuth2Session(self.client_id, token=token_dict)
        return oauth.refresh_token(self.token_url, auth=self.basic_auth)
