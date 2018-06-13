import ConfigParser
from datetime import datetime

import endpoints
from protorpc import message_types
from protorpc import messages
from protorpc import remote

import authentication
from oauth_adapter import OauthAdapter
from token_store import TokenStore
from jwt_token import JwtToken


class JsonField(messages.StringField):
    type = dict


class LinkInfoResponse(messages.Message):
    expires = message_types.DateTimeField(1)
    username = messages.StringField(2)


class AccessTokenResponse(messages.Message):
    token = messages.StringField(1)


class ServiceAccountKeyResponse(messages.Message):
    data = JsonField(1)  # not quite right as it drops the json under a data element


class ServiceAccountAccessTokenResponse(messages.Message):
    token = messages.StringField(1)


class SubSystemStatusResponse(messages.Message):
    ok = messages.BooleanField(1)
    message = messages.StringField(2)


class StatusResponse(messages.Message):
    ok = messages.BooleanField(1)
    memcache = messages.MessageField(SubSystemStatusResponse, 2)
    datastore = messages.MessageField(SubSystemStatusResponse, 3)
    fence = messages.MessageField(SubSystemStatusResponse, 4)


OAUTH_CODE_RESOURCE = endpoints.ResourceContainer(oauthcode=messages.StringField(1, required=True))

SCOPES_RESOURCE = endpoints.ResourceContainer(scopes=messages.StringField(1, repeated=True))

config = ConfigParser.ConfigParser()
config.read("config.ini")

client_id = config.get('fence', 'CLIENT_ID')
client_secret = config.get('fence', 'CLIENT_SECRET')
redirect_uri = config.get('fence', 'REDIRECT_URI')
token_url = config.get('fence', 'TOKEN_URL')

REFRESH_TOKEN_KEY = 'refresh_token'
EXPIRES_AT_KEY = 'expires_at'
ACCESS_TOKEN_KEY = 'access_token'
ID_TOKEN = 'id_token'


@endpoints.api(name='link', version='v1', base_path="/api/")
class BondApi(remote.Service):
    def __init__(self):
        self.auth = authentication.Authentication(authentication.default_config())
        self.oauth_adapter = OauthAdapter(client_id, client_secret, redirect_uri, token_url)

    @endpoints.method(
        OAUTH_CODE_RESOURCE,
        LinkInfoResponse,
        path='fence/oauthcode',
        http_method='POST',
        name='fence/oauthcode')
    def oauthcode(self, request):
        user_info = self.auth.require_user_info(self.request_state)
        token_response = self.oauth_adapter.exchange_authz_code(request.oauthcode)
        TokenStore.save(user_info.id, token_response.get(REFRESH_TOKEN_KEY), datetime.now())
        expiration_datetime = datetime.fromtimestamp(token_response.get(EXPIRES_AT_KEY))
        jwt_token = JwtToken(token_response.get(ID_TOKEN))
        return LinkInfoResponse(expires=expiration_datetime, username=jwt_token.username)

    @endpoints.method(
        message_types.VoidMessage,
        LinkInfoResponse,
        path='fence',
        http_method='GET',
        name='fence link info')
    def link_info(self, request):
        user_info = self.auth.require_user_info(self.request_state)
        return LinkInfoResponse(expires=datetime.now(), username="foo")

    @endpoints.method(
        message_types.VoidMessage,
        message_types.VoidMessage,
        path='fence',
        http_method='DELETE',
        name='delete fence link')
    def delete_link(self, request):
        user_info = self.auth.require_user_info(self.request_state)
        return message_types.VoidMessage()

    @endpoints.method(
        message_types.VoidMessage,
        AccessTokenResponse,
        path='fence/accesstoken',
        http_method='GET',
        name='get fence accesstoken')
    def accesstoken(self, request):
        user_info = self.auth.require_user_info(self.request_state)
        refresh_token = TokenStore.lookup(user_info.id)
        if refresh_token is not None:
            token_response = self.oauth_adapter.refresh_access_token(refresh_token.token)
            return AccessTokenResponse(token=token_response.get("access_token"))
        else:
            raise endpoints.BadRequestException("Could not find refresh token for user")

    @endpoints.method(
        message_types.VoidMessage,
        ServiceAccountKeyResponse,
        path='fence/serviceaccount/key',
        http_method='GET',
        name='get fence service account key')
    def service_account_key(self, request):
        user_info = self.auth.require_user_info(self.request_state)
        return ServiceAccountKeyResponse(data={"foo": "bar"})

    @endpoints.method(
        SCOPES_RESOURCE,
        ServiceAccountAccessTokenResponse,
        path='fence/serviceaccount/accesstoken',
        http_method='GET',
        name='get fence service account access token')
    def service_account_accesstoken(self, request):
        user_info = self.auth.require_user_info(self.request_state)
        return ServiceAccountAccessTokenResponse(token="fake SA token " + str(request.scopes))


@endpoints.api(name='status', version='v1', base_path="/api/")
class BondStatusApi(remote.Service):

    @endpoints.method(
        message_types.VoidMessage,
        StatusResponse,
        path='/',
        http_method='GET',
        name='status')
    def status(self, request):
        return StatusResponse(ok=True, memcache=SubSystemStatusResponse(ok=True), datastore=SubSystemStatusResponse(ok=True), fence=SubSystemStatusResponse(ok=True))

api = endpoints.api_server([BondApi, BondStatusApi])
