import base64

# import endpoints
from google.appengine.api import urlfetch
from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session
from requests_toolbelt.adapters import appengine

# https://toolbelt.readthedocs.io/en/latest/adapters.html#appengineadapter
appengine.monkeypatch()


class OauthAdapter:

    def __init__(self, client_id, client_secret, open_id_config, provider_name):
        self.client_id = client_id
        self.client_secret = client_secret
        self.open_id_config = open_id_config
        self.basic_auth = HTTPBasicAuth(self.client_id, self.client_secret)
        self.provider_name = provider_name

    def build_authz_url(self, scopes, redirect_uri, state=None, extra_authz_url_params=None):
        """
        Builds an OAuth authorization URL that a user must use to initiate the OAuth dance.
        :param scopes: Array of scopes (0 to many) that the client requires
        :param redirect_uri: A URL encoded string representing the URI that the Authorizing Service will redirect the
        user to after the user successfully authorizes this client
        :param state: A URL encoded Base64 string representing a JSON object of state information that the requester
        requires back with the redirect
        :param extra_authz_url_params: Optional list of additional url query parameters we want appended to the
        resulting authz url
        :return: A plain (not URL encoded) String
        """
        if extra_authz_url_params is None:
            extra_authz_url_params = {}
        authz_endpoint = self.open_id_config.get_config_value("authorization_endpoint")
        oauth = OAuth2Session(self.client_id, redirect_uri=redirect_uri, scope=scopes, state=state)
        authorization_url, state = oauth.authorization_url(authz_endpoint, **extra_authz_url_params)
        return authorization_url

    def exchange_authz_code(self, authz_code, redirect_uri):
        """
        Perform an authorization code exchange to get a token dict that includes an access token and a refresh token
        :param authz_code: The authorization code provided by the Oauth authorization response
        :param redirect_uri: redirect_uri that was used to get the token - will use self.redirect_url if None
        :return: A token dict including the access token, refresh token, and token type (amongst other details)
        """
        oauth = OAuth2Session(self.client_id, redirect_uri=redirect_uri)
        return oauth.fetch_token(self.open_id_config.get_token_info_url(), code=authz_code, auth=self.basic_auth)

    def refresh_access_token(self, refresh_token_str):
        """
        Take a refresh token string to get a new access token from the Oauth provider
        :param refresh_token_str: A refresh token string
        :return: An access token
        """
        token_dict = {'refresh_token': refresh_token_str}
        oauth = OAuth2Session(self.client_id, token=token_dict)
        return oauth.refresh_token(self.open_id_config.get_token_info_url(), auth=self.basic_auth)

    def revoke_refresh_token(self, refresh_token):
        """
        Calls the auth provider to revoke the given refresh token
        :param refresh_token:
        :return:
        """
        revoke_url = self.open_id_config.get_revoke_url()
        result = urlfetch.fetch(url=revoke_url,
                                method=urlfetch.POST,
                                payload="token=" + refresh_token,
                                headers={"Authorization": "Basic %s" % base64.b64encode("{}:{}".format(self.client_id, self.client_secret))})
        if result.status_code // 100 != 2:
            # raise endpoints.InternalServerErrorException("revoke url {}, status code {}, error body {}".
            #                                              format(revoke_url, result.status_code, result.content))
