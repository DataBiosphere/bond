import jwt
from datetime import datetime
import dpath.util


class JwtToken:
    def __init__(self, encoded_str, user_name_path_expr):
        """
        Parsed JWT
        :param encoded_str: encoded JWT
        :param user_name_path_expr: forward slash delimited path to user name within JWT
        """
        self.raw_dict = jwt.decode(encoded_str, verify=False)
        self.username = dpath.util.get(self.raw_dict, user_name_path_expr)
        self.issued_at = datetime.fromtimestamp(self.raw_dict.get('iat'))
