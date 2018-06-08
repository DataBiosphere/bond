import ConfigParser
from requests_oauthlib import OAuth2Session

config = ConfigParser.ConfigParser()
config.read("config.ini")

client_id = config.get('fence', 'CLIENT_ID')
client_secret = config.get('fence', 'CLIENT_SECRET')
redirect_uri = config.get('fence', 'REDIRECT_URI')
token_url = config.get('fence', 'TOKEN_URL')
fence_authorize_url = config.get('fence', 'AUTHZ_URI')


def auth_code_with_basic_auth():
    oauth = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=['openid'])
    authorization_url, state = oauth.authorization_url(fence_authorize_url)
    return authorization_url


url = auth_code_with_basic_auth()
print('Please go to %s and authorize access.' % url)
