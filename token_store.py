from google.appengine.ext import ndb
from refresh_token import RefreshToken


class TokenStore:

    @staticmethod
    def save(user_id, refresh_token_str, issued_at, username, provider_name):
        """
        Persists a RefreshToken by creating a new entity or updating an existing entity with the same id
        :param provider_name:
        :param user_id: identifier for the Google Datastore entity
        :param refresh_token_str: a refresh token string
        :param issued_at: datetime at which the token was issued
        :param username: username for whom the token was issued
        :return: The datastore Key of the persisted entity
        """
        refresh_token = RefreshToken(key=TokenStore._token_store_key(user_id, provider_name),
                                     token=refresh_token_str,
                                     issued_at=issued_at,
                                     username=username)
        return refresh_token.put()

    @staticmethod
    def lookup(user_id, provider_name):
        """
        Retrieves an entity out of Google Datastore of the "RefreshToken" type with the specified user_id
        :param provider_name:
        :param user_id: unique identifier for the RefreshToken entity
        :return: A RefreshToken entity
        """
        return TokenStore._token_store_key(user_id, provider_name).get()

    @staticmethod
    def delete(user_id, provider_name):
        TokenStore._token_store_key(user_id, provider_name).delete()

    @staticmethod
    def _token_store_key(user_id, provider_name):
        return ndb.Key("User", user_id, RefreshToken, provider_name)