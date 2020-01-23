import datetime
import time
from google.appengine.ext import ndb
from google.appengine.api.datastore_errors import TransactionFailedError

# How long to keep a fence service account key before expiring it.
_FSA_KEY_LIFETIME = datetime.timedelta(days=5)


def build_fence_service_account_key(provider_name, user_id):
    """Creates a datastore key to associate a (user, provier) to the credentials of a service account fetched from a Fence.
    :return Returns an ndb Key for the fence service account, i.e. a "fsa_key"
    """
    return ndb.Key("User", user_id, FenceServiceAccount, provider_name)


class FenceServiceAccount(ndb.Model):
    """Datastore model for storing fence service account json key and metadata for expiration and generation."""
    # The string json key token for the fence service account.
    key_json = ndb.TextProperty()
    # The datetime when to expire the service account key. Only set when the key_json is not None.
    expires_at = ndb.DateTimeProperty()
    # The datetime of when the current lock on updating this model expires. The model should only be updated by
    # a service that holds a lock. Only set when the key_json is not set or has expired.
    update_lock_timeout = ndb.DateTimeProperty()


class ServiceAccountNotUpdatedException(Exception):
    """An exception for when a fence service account was not updated after some service had grabbed the lock to update it."""
    pass


class FenceTokenStorage:
    """
    Stores service account tokens retrieved from fences and manages distributed concurrent updates so that only one access
    per (user, provider) occurs at a time.

    This is important to prevent many simultaneous requests from overloading a fence when they are all seeking the same
    service account credentials. Storage of the fence credentials (with an expiration time) allows the retrieved
    credentials to be shared.

    N.B. "fsa_key" refers to a Datastore key of the (user, provider_name) which is used to look up the fence service
    account credentials, i.e. "key_json."

    This is abstracted as its own class so that we can stub out the Datastore dependency in tests.
    """

    def delete(self, fsa_key):
        """
        Delete the stored fence service account info for the fsa_key.
        ":return returns the stored value for the key or None if it did not exist.
        """
        fence_service_account = fsa_key.get()
        if fence_service_account:
            fsa_key.delete()
        return fence_service_account.key_json if fence_service_account else None

    def retrieve(self, fsa_key, prep_key_fn, fence_fetch_fn):
        """
        Retrieve the stored fence service account json key for fsa_key, waiting as needed, or create, store, and
        return the fence service accoutn json key for the fsa_key.

        :param fsa_key The ndb Key of the provider name and user id to fetch service account credentials for.
        :param prep_key_fn The function to create the input to fence_fetch_fn from 'fsa_key' once we know
        fence_fetch_fn will be called. This is separated from fence_fetch_fn so that this can be slow but not spend as
         much time locking.
        :param fence_fetch_fn: The function to fetch the credentials from the fence. This function will ensure that
        fence_fetch_fn is not called multiple times concurrently. Arguments should work as
        fence_fetch_fn(prep_key_fn(key)) -> returns the string fence account credentials.
        :return returns the fence service account json key and the expiration time for that value.
        """
        fence_service_account = fsa_key.get()
        now = datetime.datetime.now()
        if fence_service_account is None or \
                fence_service_account.expires_at is None or \
                fence_service_account.expires_at < now:
            fence_service_account = self._fetch_and_cache_service_account(fsa_key, prep_key_fn, fence_fetch_fn)

        return (fence_service_account.key_json, fence_service_account.expires_at)

    def _fetch_and_cache_service_account(self, fsa_key, prep_key_fn, fence_fetch_fn):
        """
        Fetch a new service account from fence. We must be careful that concurrent requests result in only one
        key request to fence so the service account does not run out of keys (google limits to 10).
        """
        # Prep key before acquiring lock to keep lock duration as small as possible.
        prepped_key = prep_key_fn(fsa_key)

        if self._acquire_lock(fsa_key):
            key_json = fence_fetch_fn(prepped_key)
            fence_service_account = FenceServiceAccount(key_json=key_json,
                                                        expires_at=datetime.datetime.now() + _FSA_KEY_LIFETIME,
                                                        update_lock_timeout=None,
                                                        key=fsa_key)
            fence_service_account.put()

        else:
            fence_service_account = self._wait_for_update(fsa_key)
            if not fence_service_account.expires_at or fence_service_account.expires_at < datetime.datetime.now():
                # We waited for a fence service account update since someone else was holding the lock, but the
                # lock expired without a valid update.
                # we could recursively call _fetch_service_account_json at this point but let's start with failure
                raise ServiceAccountNotUpdatedException(
                    "lock on key {} expired but value was not updated".format(fsa_key))

        return fence_service_account

    def _acquire_lock(self, fsa_key):
        """
        :param fsa_key:
        :return: True if the lock was acquired, False otherwise
        """
        try:
            return self._lock_fence_service_account(fsa_key)
        # We expect a transaction failure or timeout when someone else acquires the lock instead of us. That's fine,
        # it's just a different way we could fail to acquire the lock. Unfortunately, docs imply it's possible to
        # receive an exception even when a transaction completes. In that case, we'll have acquired the lock but
        # will not update it. The lock will eventually time out.
        # https://cloud.google.com/appengine/docs/standard/python/datastore/transactions#using_transactions
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
        :return True if lock was successful, false otherwise.
        """
        update_lock_timeout = datetime.datetime.now() + datetime.timedelta(seconds=30)
        fence_service_account = fsa_key.get()
        if fence_service_account is None:
            fence_service_account = FenceServiceAccount(key=fsa_key, update_lock_timeout=update_lock_timeout)
        elif fence_service_account.update_lock_timeout and fence_service_account.update_lock_timeout > datetime.datetime.now():
            return False
        else:
            fence_service_account.update_lock_timeout = update_lock_timeout
        fence_service_account.put()
        return True
