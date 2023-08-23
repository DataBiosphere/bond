import jwt
from datetime import datetime
import dpath.util
import dpath.options
from base64 import b64encode


class JwtToken:
    def __init__(self, encoded_str, user_name_path_expr):
        """
        Parsed JWT
        :param encoded_str: encoded JWT
        :param user_name_path_expr: forward slash delimited path to user name within JWT
        """
        self.raw_dict = jwt.decode(b64decode(encoded_str), verify=False, algorithms=['HS256'])
        # See https://broadworkbench.atlassian.net/browse/CA-1341, needed for dpath to work when dict has "" keys
        dpath.options.ALLOW_EMPTY_STRING_KEYS = True
        self.username = dpath.util.get(self.raw_dict, user_name_path_expr)
        self.issued_at = datetime.fromtimestamp(self.raw_dict.get('iat'))
