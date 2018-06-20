import json
import endpoints
import os
import logging
import datetime
from google.appengine.api import memcache
from google.appengine.ext import ndb
from token_store import TokenStore
import time
from oauth2client.service_account import ServiceAccountCredentials
from sam_api import SamKeys


class FenceTokenVendingMachine:
    def __init__(self, fence_api, sam_api, fence_oauth_adapter):
        self.fence_api = fence_api
        self.sam_api = sam_api
        self.fence_oauth_adapter = fence_oauth_adapter

    def remove_service_account(self, user_id):
        fsa_key = ndb.Key(FenceServiceAccount, user_id)
        fence_service_account = fsa_key.get()
        if fence_service_account:
            access_token = self._get_oauth_access_token(user_id)
            key_id = json.loads(fence_service_account.key_json)["private_key_id"]
            # deleting the key will invalidate anything cached
            self.fence_api.delete_credentials_google(access_token, key_id)
            fsa_key.delete()

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
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(key_json), scopes=scopes)
        return credentials.get_access_token().access_token

    def get_service_account_key_json(self, user_info):
        """
        Get a service account key json to access objects protected by fence

        implementation:
        first see if there is a service account for the user id in memcache,
           if so, return it
        else, lookup who the user really is in sam and see if there is a service account for the real user in data store
           if so, put it in memcache under the passed in user and return it
        else, initiate a lock for the real user, fetch a service account from fence, put it in datastore, put it in memcache
        :param user_info:
        :return: fence service account key_json
        """
        key_json = memcache.get(namespace='fence_key', key=user_info.id)
        if key_json is None:
            real_user_info = self._fetch_real_user_info(user_info)
            fsa_key = ndb.Key(FenceServiceAccount, real_user_info[SamKeys.USER_ID_KEY])
            fence_service_account = fsa_key.get()
            now = datetime.datetime.now()
            if fence_service_account is None or \
                            fence_service_account.expires_at is None or \
                            fence_service_account.expires_at < now:
                fence_service_account = self._fetch_service_account(real_user_info, fsa_key)

            key_json = fence_service_account.key_json
            seconds_to_expire = (fence_service_account.expires_at - now).total_seconds()
            memcache.add(namespace='fence_key', key=user_info.id, value=key_json, time=seconds_to_expire)
        return key_json

    def _fetch_real_user_info(self, user_info):
        real_user_info = self.sam_api.user_info(user_info.token)
        if real_user_info is None:
            raise endpoints.UnauthorizedException("user not found in sam")
        return real_user_info

    def _fetch_service_account(self, real_user_info, fsa_key):
        """
        Fetch a new service account from fence. We must be careful that concurrent requests result in only one
        key request to fence so the service account does not run out of keys (google limits to 10).
        :param real_user_info:
        :param fsa_key:
        :return:
        """
        # get access_token before acquiring lock to keep lock duration as small as possible
        access_token = self._get_oauth_access_token(real_user_info[SamKeys.USER_ID_KEY])

        if self._acquire_lock(fsa_key):
            key_json = self.fence_api.get_credentials_google(access_token)
            fence_service_account = FenceServiceAccount(key_json=key_json,
                                                        expires_at=datetime.datetime.now() + datetime.timedelta(days=5),
                                                        update_lock_timeout=None,
                                                        key=fsa_key)
            fence_service_account.put()

        else:
            fence_service_account = self._wait_for_update(fsa_key)
            if fence_service_account.expires_at and fence_service_account.expires_at < datetime.datetime.now():
                # we could recursively call _fetch_service_account_json at this point but let's start with failure
                raise ServiceAccountNotUpdatedException("lock on key {} expired but service account was not updated".format(fsa_key))

        return fence_service_account

    def _get_oauth_access_token(self, user_id):
        refresh_token = TokenStore.lookup(user_id)
        if refresh_token is None:
            raise endpoints.BadRequestException("Fence account not linked")
        access_token = self.fence_oauth_adapter.refresh_access_token(refresh_token.token).get("access_token")
        return access_token

    def _acquire_lock(self, fsa_key):
        """
        :param fsa_key:
        :return: True if the lock was acquired, False otherwise
        """
        try:
            self._lock_fence_service_account(fsa_key)
            return True
        except:
            return False

    def _wait_for_update(self, fsa_key):
        """
        wait for new fence service account, exit conditions are the lock goes away or expires
        :param fsa_key:
        :return: updated fence service account
        """
        # need to be sure to get the fence_service_account in a new transaction every time so that we get a fresh copy
        fence_service_account = self._get_fence_service_account_in_new_txn(fsa_key)
        while fence_service_account.update_lock_timeout and fence_service_account.update_lock_timeout > datetime.datetime.now():
            time.sleep(1)
            fence_service_account = self._get_fence_service_account_in_new_txn(fsa_key)
        return fence_service_account

    @staticmethod
    @ndb.transactional(retries=0)
    def _get_fence_service_account_in_new_txn(fsa_key):
        return fsa_key.get()

    @ndb.transactional(retries=0)
    def _lock_fence_service_account(self, fsa_key):
        """
        within a transaction set the update_lock_timeout. There are 3 cases to consider:
        1) the key does not exist => create it and set update_lock_timeout
        2) the key does exist with update_lock_timeout set in the future => did not get lock raise exception
        3) the key does exist and update_lock_timeout is None or in the past => update update_lock_timeout

        If the transaction fails, did not get the lock.
        :param fsa_key:
        :return: fence_service_account if lock was successful or exception if not
        """
        update_lock_timeout = datetime.datetime.now() + datetime.timedelta(seconds=30)
        fence_service_account = fsa_key.get()
        if fence_service_account is None:
            fence_service_account = FenceServiceAccount(key=fsa_key, update_lock_timeout=update_lock_timeout)
        elif fence_service_account.update_lock_timeout and fence_service_account.update_lock_timeout > datetime.datetime.now():
            raise Exception("already locked")
        else:
            fence_service_account.update_lock_timeout = update_lock_timeout
        fence_service_account.put()
        return fence_service_account


class FenceServiceAccount(ndb.Model):
    key_json = ndb.TextProperty()
    expires_at = ndb.DateTimeProperty()
    update_lock_timeout = ndb.DateTimeProperty()


class ServiceAccountNotUpdatedException(Exception):
    pass