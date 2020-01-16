import datetime
import time
from google.appengine.ext import ndb
from google.appengine.api.datastore_errors import TransactionFailedError

# How long to use a created value before it is considered expired.
_VALUE_LIFETIME = datetime.timedelta(days=5)


class ServiceAccountNotUpdatedException(Exception):
    pass


class FenceServiceAccount(ndb.Model):
    key_json = ndb.TextProperty()
    expires_at = ndb.DateTimeProperty()
    update_lock_timeout = ndb.DateTimeProperty()


class DatastoreLockedStorage:
    """TODO write me"""

    def delete(self, fsa_key):
        """
        Delete the stored value for the key.
        ":return returns the stored value for the key or None if it did not exist.
        """
        fence_service_account = fsa_key.get()
        if fence_service_account:
            fsa_key.delete()
        return fence_service_account.key_json if fence_service_account else None

    def get_or_create(self, fsa_key, prep_key_fn, create_value_fn):
        """Retrieve the stored value for key, waiting as needed, or create and store the value for the key.

        :param prep_key_fn The function to create the input to create_value_fn from 'key' once we know create_value_fn
        will be called. This is separated from create_value_fn so that this can be slow but not spend as much time locking.
        :param create_value_fn: The function to create a value that should not be called multiple times. Arguments should work as
        creaet_value_fn(prep_key_fn(key)) -> returns the string value.
        :return (value, expiration_datetime) returns the value and the expiration time for that value.
        """
        fence_service_account = fsa_key.get()
        now = datetime.datetime.now()
        if fence_service_account is None or \
                fence_service_account.expires_at is None or \
                fence_service_account.expires_at < now:
            fence_service_account = self._fetch_service_account(fsa_key, prep_key_fn, create_value_fn)

        return (fence_service_account.key_json, fence_service_account.expires_at)

    def _fetch_service_account(self, fsa_key, prep_key_fn, create_value_fn):
        """
        Fetch a new service account from fence. We must be careful that concurrent requests result in only one
        key request to fence so the service account does not run out of keys (google limits to 10).
        """
        # Prep key before acquiring lock to keep lock duration as small as possible.
        prepped_key = prep_key_fn(fsa_key)

        if self._acquire_lock(fsa_key):
            key_json = create_value_fn(prepped_key)
            fence_service_account = FenceServiceAccount(key_json=key_json,
                                                        expires_at=datetime.datetime.now() + _VALUE_LIFETIME,
                                                        update_lock_timeout=None,
                                                        key=fsa_key)
            fence_service_account.put()

        else:
            fence_service_account = self._wait_for_update(fsa_key)
            if fence_service_account.expires_at and fence_service_account.expires_at < datetime.datetime.now():
                # we could recursively call _fetch_service_account_json at this point but let's start with failure
                raise ServiceAccountNotUpdatedException("lock on key {} expired but value was not updated".format(fsa_key))

        return fence_service_account

    def _acquire_lock(self, fsa_key):
        """
        :param fsa_key:
        :return: True if the lock was acquired, False otherwise
        """
        try:
            return self._lock_fence_service_account(fsa_key)
        # We expect a transaction failure when someone else acquires the lock instead of us. That's fine, it's just
        # a different way we could fail to acquire the lock.
        except TransactionFailedError:
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


class InMemoryLockedStorage:
    """
    An in-memory implementation of the DatastoreLockedStorage class for use as a fake in testing. Not thread safe, only
    works in a single thread, so does not do real locking.
    """

    @staticmethod
    def create(prep_key_fn, create_value_fn):
        return InMemoryLockedStorage(prep_key_fn=prep_key_fn, create_value_fn=create_value_fn)

    def __init__(self, prep_key_fn, create_value_fn, ):
        self.prep_key_fn = prep_key_fn
        self.create_value_fn = create_value_fn
        # Dict from fsa_keys to FenceServiceAccounts.
        self.accounts = {}

    def delete(self, fsa_key):
        if fsa_key not in self.accounts:
            return None
        account = self.accounts.pop(fsa_key)
        return account.json_key

    def get_or_create(self, fsa_key):
        if fsa_key in self.accounts:
            return self.accounts[fsa_key]

        json_key = self.create_value_fn(self.prep_key_fn(fsa_key))
        fence_service_account = FenceServiceAccount(key_json=json_key,
                                                    expires_at=datetime.datetime.now() + _VALUE_LIFETIME,
                                                    update_lock_timeout=None,
                                                    key=fsa_key)
        self.accounts[fsa_key] = fence_service_account
        return fence_service_account
