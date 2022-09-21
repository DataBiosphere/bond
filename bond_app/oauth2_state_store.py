import secrets
from collections import namedtuple
from google.cloud import ndb

# Information associated with a tokens for refreshing service account credentials.
OAuth2StateInfo = namedtuple('OAuth2StateInfo', ['nonce'])


class OAuth2State(ndb.Model):
    """
    Model used to store entries in Datastore.

    This is not used as the return type for OAuth2StateStore because it depends on ndb, which we want to stub out for unit
    tests.
    """
    nonce = ndb.StringProperty()

    @classmethod
    def kind_name(cls):
        return cls.__name__


class OAuth2StateStore:
    """
    Stores OAuth2 State nonces for csrf protection.
    """


    def save(self, user_id, provider, nonce):
        """
        Persists a RefreshToken by creating a new entity or updating an existing entity with the same id
        :param user_id
        :param provider:
        :param nonce: random value for csrf protection
        """
        ouath2_nonce = OAuth2State(key=OAuth2StateStore._oauth2_state_store_key(user_id, provider), nonce=nonce)
        ouath2_nonce.put()

    def delete_if_exists(self, user_id, provider_name) -> bool:
        key = OAuth2StateStore._oauth2_state_store_key(user_id, provider_name)
        if key.get():
            key.delete()
            return True
        else:
            return False

    # def build_oauth2_state(self, user_id, provider_name):

    @staticmethod
    def _oauth2_state_store_key(user_id, provider_name):
        return ndb.Key("OAuth2State", user_id, OAuth2State, provider_name)

    @staticmethod
    def random_nonce():
        return secrets.token_urlsafe()
