from collections import namedtuple
import datetime
import time
import logging
from google.cloud import ndb

# This used to be set to 30 seconds, but GAE uses gunicorn as its http server, and the default request timeout for
# gunicorn is 30 seconds: https://docs.gunicorn.org/en/latest/settings.html#timeout
# Therefore, our timeout needs to be less than that.  See https://broadworkbench.atlassian.net/browse/CA-1529
LOCK_DURATION = 15

logger = logging.getLogger(__name__)

# How long to keep a fence service account key before expiring it.
_FSA_KEY_LIFETIME = datetime.timedelta(days=5)

# A tuple of a provider_name and user_id to use as a unique key for a user/provider combination.
ProviderUser = namedtuple("ProviderUser", ["provider_name", "user_id"])


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

    This is abstracted as its own class so that we can stub out the Datastore dependency in tests.
    """

    def delete(self, provider_user):
        """
        Delete the stored fence service account info for the ProviderUser.
        :param provider_user the ProviderUser.
        :return returns the stored value for the key or None if it did not exist.
        """
        fsa_key = self._build_fence_service_account_key(provider_user)
        fence_service_account = fsa_key.get()
        if fence_service_account:
            fsa_key.delete()
        return fence_service_account.key_json if fence_service_account else None

    def retrieve(self, provider_user, prep_key_fn, fence_fetch_fn):
        """
        Retrieve the stored fence service account json key for provider_user, waiting as needed, or create, store, and
        return the fence service accoutn json key for the provider_user.

        :param provider_user The ProviderUser fetch service account credentials for.
        :param prep_key_fn The function to create the input to fence_fetch_fn from 'provider_user' once we know
        fence_fetch_fn will be called. This is separated from fence_fetch_fn so that this can be slow but not spend as
         much time locking.
        :param fence_fetch_fn: The function to fetch the credentials from the fence. This function will ensure that
        fence_fetch_fn is not called multiple times concurrently. Arguments should work as
        fence_fetch_fn(prep_key_fn(key)) -> returns the string fence account credentials.
        :return returns the fence service account json key and the expiration time for that value.
        """
        fence_service_account = self._build_fence_service_account_key(provider_user).get()
        now = datetime.datetime.now()
        if fence_service_account is None or \
                fence_service_account.expires_at is None or \
                fence_service_account.expires_at < now:
            fence_service_account = self._fetch_and_cache_service_account(provider_user, prep_key_fn, fence_fetch_fn)

        return (fence_service_account.key_json, fence_service_account.expires_at)

    def _fetch_and_cache_service_account(self, provider_user, prep_key_fn, fence_fetch_fn, retries=1):
        """
        Fetch a new service account from fence. We must be careful that concurrent requests result in only one
        key request to fence so the service account does not run out of keys (google limits to 10).
        """
        # Prep key before acquiring lock to keep lock duration as small as possible.
        prepped_key = prep_key_fn(provider_user)
        fsa_key = self._build_fence_service_account_key(provider_user)

        if self._acquire_lock(fsa_key):
            key_json = fence_fetch_fn(prepped_key)
            fence_service_account = FenceServiceAccount(key_json=key_json,
                                                        expires_at=datetime.datetime.now() + _FSA_KEY_LIFETIME,
                                                        update_lock_timeout=None,
                                                        key=fsa_key)
            fence_service_account.put()
            return fence_service_account
        else:
            fence_service_account = self._wait_for_update(fsa_key)
            # if the record's expiry is in the future, we know it has been updated by another process and we can return
            # this fence_service_account.  If the record is _still_ expired, then it is deadlocked and we should clean
            # up the lock and try again.
            if not fence_service_account.expires_at or fence_service_account.expires_at < datetime.datetime.now():
                # We waited for a fence service account update since someone else was holding the lock, but the
                # lock expired without a valid update.  We are deadlocked, so cleanup the lock.
                logger.warning("Cleaning up deadlock. Current datetime is: {}. FenceServiceAccount {} expired at {} and was locked until {}."
                               .format(datetime.datetime.now(),
                                       fsa_key,
                                       fence_service_account.expires_at,
                                       fence_service_account.update_lock_timeout))

                fence_service_account.update_lock_timeout = None
                fence_service_account.put()

                if retries > 0:
                    return self._fetch_and_cache_service_account(provider_user, prep_key_fn, fence_fetch_fn, retries-1)
                else:
                    raise ServiceAccountNotUpdatedException(
                        "FenceServiceAccount: {} has expired and a lock prevented us from updating this record"
                        .format(fence_service_account))

    def _acquire_lock(self, fsa_key):
        """
        This thing can return FALSE for 2 different reasons!  And those "FALSE" responses might mean two very different
        things.  Either we were unable to successfully lock the FenceServiceAccount record because it is already locked,
        OR something else happened.  In the latter case, the transaction may have been successful, but the call to grab
        the lock still threw an Exception for some reason.
        :param fsa_key:
        :return: True if the lock was acquired, False otherwise
        """
        try:
            return self._lock_fence_service_account(fsa_key)
        # We expect a transaction failure or timeout when someone else acquires the lock instead of us. That's fine,
        # it's just a different way we could fail to acquire the lock. Unfortunately, docs indicate it is possible to
        # receive an exception even when a transaction completes. In that case, we'll have acquired the lock but
        # will not update it and the lock will eventually time out.
        # https://cloud.google.com/appengine/docs/standard/python/datastore/transactions#using_transactions
        except:
            logger.info("An exception was thrown while trying to lock the FenceServiceAccount entry", exc_info=True)
            return False

    def _wait_for_update(self, fsa_key):
        """
        wait for new fence service account, exit conditions are the lock goes away or expires
        :param fsa_key:
        :return: updated fence service account
        """
        # need to be sure to get the fence_service_account in a new transaction every time so that we get a fresh copy
        fence_service_account = self._get_fence_service_account_in_new_txn(fsa_key)
        # TODO: if the lock is far enough in the future, this will attempt to spin until that date.  I think the request
        # is timing out prior to that and GAE is killing the app
        while fence_service_account.update_lock_timeout and fence_service_account.update_lock_timeout > datetime.datetime.now():
            time.sleep(1)
            fence_service_account = self._get_fence_service_account_in_new_txn(fsa_key)
        logger.info("Lock expired on FenceServiceAccount: {}".format(fence_service_account))
        return fence_service_account

    @staticmethod
    def _build_fence_service_account_key(provider_user):
        """Creates a datastore key to associate a ProviderUser to the credentials of a service account fetched from a
         Fence.
        :return Returns an ndb Key for the fence service account, i.e. a "fsa_key"
        """
        return ndb.Key("User", provider_user.user_id, FenceServiceAccount, provider_user.provider_name)

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
        update_lock_timeout = datetime.datetime.now() + datetime.timedelta(seconds=LOCK_DURATION)
        fence_service_account = fsa_key.get()
        if fence_service_account is None:
            # TODO: This creates a record with NULL values for key_json and expires_at
            # This is a thing we DO see in prod.  Which means the put() call below succeeds, but subsequent calls for
            # this same request are failing, leaving around these "partial" records.  Need to investigate
            fence_service_account = FenceServiceAccount(key=fsa_key, update_lock_timeout=update_lock_timeout)
        elif fence_service_account.update_lock_timeout and fence_service_account.update_lock_timeout > datetime.datetime.now():
            logger.debug("Could not obtain lock on {} because it is already locked".format(fsa_key))
            return False
        else:
            fence_service_account.update_lock_timeout = update_lock_timeout
        fence_service_account.put()
        logger.debug("Successfully locked FenceServiceAccount Record: {}".format(fence_service_account))
        return True
