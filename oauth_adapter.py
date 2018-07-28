from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session
from requests_toolbelt.adapters import appengine
from google.appengine.api import memcache
from google.appengine.api import urlfetch
import endpoints
import json
import base64


# https://toolbelt.readthedocs.io/en/latest/adapters.html#appengineadapter
appengine.monkeypatch()


class OauthAdapter:

    def __init__(self, client_id, client_secret, open_id_config_url, provider_name):
        self.client_id = client_id
        self.client_secret = client_secret
        self.open_id_config_url = open_id_config_url
        self.basic_auth = HTTPBasicAuth(self.client_id, self.client_secret)
        self.provider_name = provider_name

    def exchange_authz_code(self, authz_code, redirect_uri):
        """
        Perform an authorization code exchange to get a token dict that includes an access token and a refresh token
        :param authz_code: The authorization code provided by the Oauth authorization response
        :param redirect_uri: redirect_uri that was used to get the token - will use self.redirect_url if None
        :return: A token dict including the access token, refresh token, and token type (amongst other details)
        """
        oauth = OAuth2Session(self.client_id, redirect_uri=redirect_uri)
        return oauth.fetch_token(self._get_token_info_url(), code=authz_code, auth=self.basic_auth)

    def refresh_access_token(self, refresh_token_str):
        """
        Take a refresh token string to get a new access token from the Oauth provider
        :param refresh_token_str: A refresh token string
        :return: An access token
        """
        token_dict = {'refresh_token': refresh_token_str}
        oauth = OAuth2Session(self.client_id, token=token_dict)
        return oauth.refresh_token(self._get_token_info_url(), auth=self.basic_auth)

    def revoke_refresh_token(self, refresh_token):
        """
        Calls the auth provider to revoke the given refresh token
        :param refresh_token:
        :return:
        """
        revoke_url = self._get_revoke_url()
        result = urlfetch.fetch(url=revoke_url,
                                method=urlfetch.POST,
                                payload="token=" + refresh_token,
                                headers={"Authorization": "Basic %s" % base64.b64encode("{}:{}".format(self.client_id, self.client_secret))})
        if result.status_code // 100 != 2:
            raise endpoints.InternalServerErrorException("revoke url {}, status code {}, error body {}".
                                                         format(revoke_url, result.status_code, result.content))

    def _get_open_id_config(self):
        open_id_config = memcache.get(namespace="OauthAdapter", key=self.provider_name)
        if not open_id_config:
            open_id_config_response = urlfetch.fetch(self.open_id_config_url)
            if open_id_config_response.status_code != 200:
                raise endpoints.InternalServerErrorException(
                    message='open_id_config_url [{}] returned status {}: {}'.format(self.open_id_config_url,
                                                                                    open_id_config_response.status_code,
                                                                                    open_id_config_response.content))
            else:
                open_id_config = json.loads(open_id_config_response.content)
                memcache.add(namespace="OauthAdapter", key=self.provider_name, value=open_id_config)
        return open_id_config

    def _get_token_info_url(self):
        config = self._get_open_id_config()
        if "token_endpoint" in config:
            return self._get_open_id_config()["token_endpoint"]
        else:
            raise endpoints.InternalServerErrorException("token_endpoint not found in openid config: " + self.open_id_config_url)

    def _get_revoke_url(self):
        config = self._get_open_id_config()
        if "revocation_endpoint" in config:
            return config["revocation_endpoint"]
        else:
            return self._get_open_id_config()["token_endpoint"].replace("token", "revoke")
