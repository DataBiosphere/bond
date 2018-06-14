import jwt
from datetime import datetime


class JwtToken:
    def __init__(self, encoded_str):
        self.raw_dict = jwt.decode(encoded_str, verify=False)
        self.username = self.raw_dict.get('context').get('user').get('name')
        self.issued_at = datetime.fromtimestamp(self.raw_dict.get('iat'))
