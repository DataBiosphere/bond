import json

from werkzeug import exceptions
from .bond import FenceKeys
from .fence_token_storage import ProviderUser
from google.oauth2 import service_account
import google.auth.transport.requests
import logging

logger = logging.getLogger(__name__)


class FenceTokenVendingMachine:
    def __init__(self, fence_api, cache_api, refresh_token_store, fence_oauth_adapter, provider_name,
                 fence_token_storage):
        self.fence_api = fence_api
        self.cache_api = cache_api
        self.refresh_token_store = refresh_token_store
        self.fence_oauth_adapter = fence_oauth_adapter
        self.provider_name = provider_name
        self.fence_token_storage = fence_token_storage

    def remove_service_account(self, user_id):
        provider_user = ProviderUser(provider_name=self.provider_name, user_id=user_id)
        key_json = self.fence_token_storage.delete(provider_user)
        if key_json:
            try:
                access_token = self._get_oauth_access_token(provider_user)
                key_id = json.loads(key_json)["private_key_id"]
                self.fence_api.delete_credentials_google(access_token, key_id)
            except Exception as e:
                logger.warning(
                    "Error removing service account for {}. Key will not be deleted with provider {}:\n{}"
                    .format(user_id, self.provider_name, e))

    def get_service_account_access_token(self, sam_user_id, scopes=None):
        """
        Get a service account access token to access objects protected by fence

        :param sam_user_id: Id stored in Sam for user who initiated request
        :param scopes: scopes to request token, defaults to ["email", "profile"]
        :return: access token for service account
        """
        if scopes is None or len(scopes) == 0:
            scopes = ["email", "profile"]
        key_json = self.get_service_account_key_json(sam_user_id)
        credentials = service_account.Credentials.from_service_account_info(json.loads(key_json), scopes=scopes)
        try:
            credentials.refresh(google.auth.transport.requests.Request())
        except Exception as e:
            logger.warning("Error refreshing service account credentials:\n%s".format(str(e)))
            raise exceptions.InternalServerError(
                description="Unable to refresh service account credentials. Consider relinking your account.\n%s".format(str(e)),
                original_exception=e)
        return credentials.token

    def get_service_account_key_json(self, sam_user_id):
        """
        Get a service account key json to access objects protected by fence, using the cache as possible.
        :param sam_user_id: Id stored in Sam for user who initiated request
        :return: fence service account key_json
        """
        provider_user = ProviderUser(provider_name=self.provider_name, user_id=sam_user_id)
        (key_json, expiration_datetime) = self.fence_token_storage.retrieve(
            provider_user, prep_key_fn=self._get_oauth_access_token,
            fence_fetch_fn=self.fence_api.get_credentials_google)
        return key_json

    def _get_oauth_access_token(self, provider_user):
        refresh_token = self.refresh_token_store.lookup(provider_user.user_id, self.provider_name)
        if refresh_token is None:
            raise exceptions.NotFound("Fence account not linked. {}".format(str(provider_user)))
        logger.info("Using Refresh Token to generate Access Token for User: {}".format(provider_user))
        access_token = self.fence_oauth_adapter.refresh_access_token(refresh_token.token).get(FenceKeys.ACCESS_TOKEN)
        return access_token
