import json

from werkzeug import exceptions
import requests
from requests_toolbelt.adapters import appengine

appengine.monkeypatch()

class OpenIdConfig:

    def __init__(self, provider_name, open_id_config_url, cache_api):
        self.provider_name = provider_name
        self.open_id_config_url = open_id_config_url
        self.cache_api = cache_api

    def load_dict(self):
        open_id_dict = self.cache_api.get(namespace="OauthAdapter", key=self.provider_name)
        if not open_id_dict:
            open_id_config_response = requests.get(self.open_id_config_url)
            if open_id_config_response.status_code != 200:
                raise exceptions.InternalServerError(
                    'open_id_config_url [{}] returned status {}: {}'.format(self.open_id_config_url,
                                                                                    open_id_config_response.status_code,
                                                                                    open_id_config_response.content))
            else:
                open_id_dict = json.loads(open_id_config_response.content)
                self.cache_api.add(namespace="OauthAdapter", key=self.provider_name, value=open_id_dict, expires_in=60*60*24)
        return open_id_dict

    def get_config_value(self, key, raise_error=True):
        """
        Looks in the open_id_config for an entry that matches the provided "key" parameter.  By default, if the key is
        not found in the config, then an exception will be raised.  This behavior can be disabled by setting the
        "raise_error" parameter to false.
        :param key: String value representing the key of the item you want to retrieve from the open_id_config
        :param raise_error: Boolean - default TRUE - set to false to avoid raising an exception when the "key" cannot be
        found
        :return: The object from the open_id_config identified by the "key"
        """
        config = self.load_dict()
        if key in config:
            return self.load_dict()[key]
        elif raise_error:
            raise exceptions.InternalServerError(key + " not found in openid config: " + self.open_id_config_url)

    def get_token_info_url(self):
        return self.get_config_value("token_endpoint")

    def get_revoke_url(self):
        revocation_endpoint = self.get_config_value("revocation_endpoint", False)
        if revocation_endpoint:
            return revocation_endpoint
        else:
            return self.get_token_info_url().replace("token", "revoke")
