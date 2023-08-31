import base64
import json
import secrets
from google.cloud import ndb
from dataclasses import dataclass


# Information associated with a tokens for refreshing service account credentials.
@dataclass
class OAuth2StateInfo:
    nonce: str


class OAuth2State(ndb.Model):
    """
    Model used to store entries in Datastore.

    This is not used as the return type for OAuth2StateStore because it depends on ndb, which we want to stub out for unit
    tests.
    """
    nonce = ndb.TextProperty(indexed=False)

    @classmethod
    def kind_name(cls):
        return cls.__name__


class OAuth2StateStore:
    """
    Stores OAuth2 State nonces for csrf protection.
    """

    def save(self, user_id, provider, nonce):
        """
        Persists a OAuth2State by creating a new entity or updating an existing entity with the same id
        :param user_id
        :param provider:
        :param nonce: random value for csrf protection
        """
        oauth2_nonce = OAuth2State(key=OAuth2StateStore._oauth2_state_store_key(user_id, provider), nonce=nonce)
        oauth2_nonce.put()

    def validate_and_delete(self, user_id, provider_name, nonce) -> bool:
        key = OAuth2StateStore._oauth2_state_store_key(user_id, provider_name)
        oauth2_state = key.get()
        if oauth2_state is None:
            return False
        else:
            key.delete()
            return oauth2_state.nonce == nonce

    def state_with_nonce(self, state):
        if not state:
            decoded_state = {}
        else:
            decoded_raw = base64.b64decode(state)
            decoded_state = json.loads(decoded_raw)
        nonce = secrets.token_urlsafe()
        decoded_state_with_nonce = {**decoded_state, 'nonce': nonce}
        dumped_state = json.dumps(decoded_state_with_nonce)
        utf8_dumped_state = dumped_state.encode('utf-8')
        return base64.b64encode(utf8_dumped_state), nonce

    @staticmethod
    def _oauth2_state_store_key(user_id, provider_name):
        return ndb.Key("OAuth2State", user_id, OAuth2State, provider_name)


