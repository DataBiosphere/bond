from google.oauth2 import service_account
import google.auth.transport.requests


class UserCredentials:
    default_scopes = ['profile',
                      'email',
                      'openid']

    def __init__(self, user_email, path_to_key_file, scopes=None):
        if scopes is None:
            scopes = UserCredentials.default_scopes

        self.user_email = user_email
        self.credentials = service_account.Credentials.from_service_account_file(path_to_key_file,
                                                                                 scopes=scopes,
                                                                                 subject=user_email)

    def get_access_token(self):
        # Ugly? Kinda. See: https://google-auth.readthedocs.io/en/latest/reference/google.auth.transport.requests.html
        self.credentials.refresh(google.auth.transport.requests.Request())
        return self.credentials.token
