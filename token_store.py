from google.appengine.ext import ndb
from refresh_token import RefreshToken
import json


class TokenStore:

    @staticmethod
    def save(email, token_dict):
        """
        Persists a BondToken by creating a new entity or updating an existing entity with the same id
        :param email: identifier for the Google Datastore entity, in our case an email address
        :param token_dict: a dict instance populated with token information
        :return: The datastore Key of the persisted entity
        """
        bond_token = RefreshToken(id=email, token_dict_str=json.dumps(token_dict))
        # TODO: See if we can't get this validation to happen when the BondToken is created
        bond_token.validate()
        return bond_token.put()

    @staticmethod
    def lookup(email):
        """
        Retrieves an entity out of Google Datastore of the "BondToken" type and id (email address)
        :param email: unique identifier (email address) for the BondToken entity
        :return: A BondToken entity
        """
        return ndb.Key(RefreshToken.kind_name(), email).get()
