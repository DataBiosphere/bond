import json
import datetime
import logging

from werkzeug import exceptions
from .bond import FenceKeys
from .fence_token_storage import ProviderUser
from google.oauth2 import service_account
import google.auth.transport.requests
from .sam_api import SamKeys


class FenceTokenVendingMachine:
    def __init__(self, fence_api, sam_api, cache_api, refresh_token_store, fence_oauth_adapter, provider_name,
                 fence_token_storage):
        self.fence_api = fence_api
        self.sam_api = sam_api
        self.cache_api = cache_api
        self.refresh_token_store = refresh_token_store
        self.fence_oauth_adapter = fence_oauth_adapter
        self.provider_name = provider_name
        self.fence_token_storage = fence_token_storage

    def remove_service_account(self, user_id):
        provider_user = ProviderUser(provider_name=self.provider_name, user_id=user_id)
        key_json = self.fence_token_storage.delete(provider_user)
        if key_json:
            access_token = self._get_oauth_access_token(provider_user)
            key_id = json.loads(key_json)["private_key_id"]
            # keys in cache will be invalid after we delete them with Google, but clear out the cache for good measure
            self.cache_api.delete(namespace=self.provider_name, key=user_id)
            self.fence_api.delete_credentials_google(access_token, key_id)

    def get_service_account_access_token(self, user_info, scopes=None):
        """
        Get a service account access token to access objects protected by fence

        :param user_info:
        :param scopes: scopes to request token, defaults to ["email", "profile"]
        :return: access token for service account
        """
        if scopes is None or len(scopes) == 0:
            scopes = ["email", "profile"]
        key_json = self.get_service_account_key_json(user_info)
        credentials = service_account.Credentials.from_service_account_info(json.loads(key_json), scopes=scopes)
        try:
            credentials.refresh(google.auth.transport.requests.Request())
        except Exception as e:
            logging.warning("Error refreshing service account credentials:\n%s".format(str(e)))
            raise exceptions.InternalServerError(
                description="Unable to refresh service account credentials. Consider relinking your account.\n%s".format(str(e)),
                original_exception=e)
        return credentials.token

    def get_service_account_key_json(self, user_info):
        """
        Get a service account key json to access objects protected by fence, using the cache as possible.
        :param user_info:
        :return: fence service account key_json
        """
        key_json = self.cache_api.get(namespace=self.provider_name, key=user_info.id)
        if key_json is not None:
            return key_json

        real_user_info = self._fetch_real_user_info(user_info)
        provider_user = ProviderUser(provider_name=self.provider_name, user_id=real_user_info[SamKeys.USER_ID_KEY])
        (key_json, expiration_datetime) = self.fence_token_storage.retrieve(
            provider_user, prep_key_fn=self._get_oauth_access_token,
            fence_fetch_fn=self.fence_api.get_credentials_google)
        seconds_to_expire = (expiration_datetime - datetime.datetime.now()).total_seconds()
        self.cache_api.add(namespace=self.provider_name, key=user_info.id, value=key_json, expires_in=seconds_to_expire)
        return key_json

    def _fetch_real_user_info(self, user_info):
        real_user_info = self.sam_api.user_info(user_info.token)
        if real_user_info is None:
            raise exceptions.Unauthorized("user not found in sam")
        return real_user_info

    def _get_oauth_access_token(self, provider_user):
        refresh_token = self.refresh_token_store.lookup(provider_user.user_id, self.provider_name)
        if refresh_token is None:
            raise exceptions.NotFound("Fence account not linked. {}".format(str(provider_user)))
        access_token = self.fence_oauth_adapter.refresh_access_token(refresh_token.token).get(FenceKeys.ACCESS_TOKEN)
        return access_token
