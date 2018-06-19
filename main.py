import ConfigParser
from datetime import datetime

import endpoints
from protorpc import message_types
from protorpc import messages
from protorpc import remote

import authentication
from bond import Bond
from fence_token_vending import FenceTokenVendingMachine
from fence_api import FenceApi
from sam_api import SamApi
from oauth_adapter import OauthAdapter
import json


class JsonField(messages.StringField):
    type = dict


class LinkInfoResponse(messages.Message):
    issued_at = message_types.DateTimeField(1)
    username = messages.StringField(2)


class AccessTokenResponse(messages.Message):
    token = messages.StringField(1)
    expires_at = message_types.DateTimeField(2)


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
credentials_google_url = config.get('fence', 'CREDENTIALS_USER_URL')
sam_base_url = config.get('sam', 'BASE_URL')


@endpoints.api(name='link', version='v1', base_path="/api/")
class BondApi(remote.Service):
    def __init__(self):
        self.auth = authentication.Authentication(authentication.default_config())
        self.oauth_adapter = OauthAdapter(client_id, client_secret, redirect_uri, token_url)
        self.bond = Bond(self.oauth_adapter)
        self.fence_tvm = FenceTokenVendingMachine(FenceApi(credentials_google_url), SamApi(sam_base_url), self.oauth_adapter)

    @endpoints.method(
        OAUTH_CODE_RESOURCE,
        LinkInfoResponse,
        path='fence/oauthcode',
        http_method='POST',
        name='fence/oauthcode')
    def oauthcode(self, request):
        user_info = self.auth.require_user_info(self.request_state)
        issued_at, username = self.bond.exchange_authz_code(request.oauthcode, user_info.id)
        return LinkInfoResponse(issued_at=issued_at, username=username)

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
        try:
            access_token, expires_at = self.bond.generate_access_token(user_info.id)
            return AccessTokenResponse(token=access_token, expires_at=expires_at)
        except Bond.MissingTokenError as err:
            # TODO: I don't like throwing and rethrowing exceptions
            raise endpoints.BadRequestException(err.message)

    @endpoints.method(
        message_types.VoidMessage,
        ServiceAccountKeyResponse,
        path='fence/serviceaccount/key',
        http_method='GET',
        name='get fence service account key')
    def service_account_key(self, request):
        user_info = self.auth.require_user_info(self.request_state)
        return ServiceAccountKeyResponse(data=json.loads(self.fence_tvm.get_service_account_key_json(user_info)))

    @endpoints.method(
        SCOPES_RESOURCE,
        ServiceAccountAccessTokenResponse,
        path='fence/serviceaccount/accesstoken',
        http_method='GET',
        name='get fence service account access token')
    def service_account_accesstoken(self, request):
        user_info = self.auth.require_user_info(self.request_state)
        return ServiceAccountAccessTokenResponse(token=self.fence_tvm.get_service_account_access_token(user_info, request.scopes))


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
