import datetime
from google.cloud import ndb
from google.api_core.exceptions import InvalidArgument
from .cache_api import CacheApi
import logging

_NO_EXPIRATION_DATETIME = datetime.datetime(year=3000, month=1, day=1)


class CacheEntry(ndb.Model):
    """Datastore model for cache values and expirations."""
    # The value stored in the cache.
    value = ndb.PickleProperty()
    # The datetime when to expire the cache entry, or _NO_EXPIRATION_DATETIME for no expiration.
    # Datastore docs warn against doing this at high write rates.
    # https://cloud.google.com/datastore/docs/best-practices#deletions
    expires_at = ndb.DateTimeProperty()


class DatastoreCacheApi(CacheApi):
    """
    A CacheApi backed by Datastore.

    N.B. expiration does not happen automatically. In appengine we use a cron.yml to ensure that we periodically
    delete expired entries.
    """

    def add(self, key, value, expires_in=0, namespace=None):
        try:
            CacheEntry(key=DatastoreCacheApi._build_cache_key(key, namespace), value=value,
                       expires_at=DatastoreCacheApi._calculate_expiration(expires_in)).put()
            return True
        except InvalidArgument:
            return False

    def get(self, key, namespace=None):
        try:
            entry = DatastoreCacheApi._build_cache_key(key, namespace).get()
            if entry and entry.expires_at >= datetime.datetime.now():
                return entry.value
            return None
        except InvalidArgument:
            return None

    def delete(self, key, namespace=None):
        try:
            DatastoreCacheApi._build_cache_key(key, namespace).delete()
        except InvalidArgument:
            pass

    @staticmethod
    def delete_expired_entries():
        """Deletes the entries that have expired. This must be done periodically. """
        expired_entries = CacheEntry.query(CacheEntry.expires_at < datetime.datetime.now())
        logging.info("Found %d expired cache entries.", expired_entries.count())
        try:
            deletions = ndb.delete_multi([key for key in expired_entries.iter(keys_only=True)])
            logging.info("Deleted %d cache entries.", len(deletions))
        except Exception as e:
            logging.error("Failed to delete expired cache entries: %s", e)

    @staticmethod
    def _build_cache_key(key, namespace):
        """
        Create an ndb Key for the key and namespace.
        Raises InvalidArgument if the cache key is invalid. Note Datastore string cache keys
        must be at most 1500 bytes.
        """
        if namespace is not None:
            return ndb.Key("cache namespace", namespace, CacheEntry, key)
        else:
            return ndb.Key(CacheEntry, key)

    @staticmethod
    def _calculate_expiration(expires_in):
        """
        Calculates the datetime that an entry should expire.
        :param expires_in in how many seconds to expire the key, or 0 if it should not expire.
        :return: The expiration datetime or else None if it should not expire.
        """
        if expires_in == 0:
            return _NO_EXPIRATION_DATETIME
        return datetime.datetime.now() + datetime.timedelta(seconds=expires_in)
