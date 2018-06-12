from google.appengine.ext import ndb
import json


class RefreshToken(ndb.Model):
    token_dict_str = ndb.TextProperty()

    REQUIRED_KEYS = ["access_token", "refresh_token", "token_type"]

    @classmethod
    def kind_name(cls):
        return cls.__name__

    # @classmethod
    # def new(cls, email, token_dict):
    #     """
    #     Factory method is the preferred method for manually creating new BondTokens as it will ensure that the
    #     token_dict property is valid.  Will either return a new BondToken instance on success or throw a KeyError if the
    #     token_dict is invalid.
    #     :param email: unique identifier for the BondToken
    #     :param token_dict: A dictionary containing keys for "access_token", "refresh_token", and "token_type"
    #     :return: a new BondToken instance
    #     """
    #     BondToken.__validate_token_dict(token_dict)
    #     BondToken(token_dict_str=json.dumps(token_dict), id=email)

    def token_dict(self):
        return json.loads(self.token_dict_str)

    def validate(self):
        RefreshToken.__validate_token_dict(self.token_dict_str)

    @staticmethod
    def __validate_token_dict(token_dict):
        [RefreshToken.__check_for_key(k, token_dict) for k in RefreshToken.REQUIRED_KEYS]

    @staticmethod
    def __check_for_key(key, my_dict):
        if key not in my_dict:
            # NOTE: Do not print the token_dict values to the logs because we do not want to expose tokens
            raise KeyError("Token dict must contain an entry with key: {}. "
                           "Keys in provided dict are: {}".format(key, list(my_dict.keys())))
