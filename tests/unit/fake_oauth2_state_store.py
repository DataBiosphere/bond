import base64
import json
from dataclasses import dataclass
from bond_app.oauth2_state_store import OAuth2StateInfo


# Internal key class for a user_id and provider_name.
@dataclass(unsafe_hash=True)
class _UserKey:
    user_id: str
    provider_name: str


class FakeOAuth2StateStore:
    """A fake in memory implementation of TokenStore for unit tests."""

    test_nonce = "iamasecretnonce"

    def __init__(self):
        # Map from OAuth2Store keys to OAuth2State.
        self.oauth2_states = {}

    def save(self, user_id, provider_name, nonce):
        """
        Persists an OAuth2State by creating a new entity or updating an existing entity with the same id
        :param provider_name:
        :param user_id: identifier for the Google Datastore entity
        :param nonce: random nonce for
        """
        key = _UserKey(user_id, provider_name)
        state = OAuth2StateInfo(nonce=nonce)
        self.oauth2_states[key] = state

    def validate_and_delete(self, user_id, provider_name, nonce) -> bool:
        key = _UserKey(user_id, provider_name)
        if key not in self.oauth2_states:
            return False
        else:
            oauth2_state = self.oauth2_states.pop(key)
            return oauth2_state.nonce == nonce

    def state_with_nonce(self, state):
        if not state:
            decoded_state = {}
        else:
            decoded_raw = base64.b64decode(state)
            decoded_state = json.loads(decoded_raw)
        nonce = self.test_nonce
        decoded_state_with_nonce = {**decoded_state, 'nonce': nonce}
        dumped_state = json.dumps(decoded_state_with_nonce)
        utf8_state = dumped_state.encode('utf-8')
        return base64.b64encode(utf8_state), nonce

