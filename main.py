import endpoints
from protorpc import message_types
from protorpc import messages
from protorpc import remote
from datetime import datetime
import json


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


@endpoints.api(name='link', version='v1', base_path="/api/")
class BondApi(remote.Service):

    @endpoints.method(
        OAUTH_CODE_RESOURCE,
        LinkInfoResponse,
        path='fence/oauthcode',
        http_method='POST',
        name='fence/oauthcode')
    def oauthcode(self, request):
        return LinkInfoResponse(expires=datetime.now(), username=request.oauthcode)

    @endpoints.method(
        message_types.VoidMessage,
        LinkInfoResponse,
        path='fence',
        http_method='GET',
        name='fence link info')
    def link_info(self, request):
        return LinkInfoResponse(expires=datetime.now(), username="foo")

    @endpoints.method(
        message_types.VoidMessage,
        message_types.VoidMessage,
        path='fence',
        http_method='DELETE',
        name='delete fence link')
    def delete_link(self, request):
        return message_types.VoidMessage()

    @endpoints.method(
        message_types.VoidMessage,
        AccessTokenResponse,
        path='fence/accesstoken',
        http_method='GET',
        name='get fence accesstoken')
    def accesstoken(self, request):
        return AccessTokenResponse(token="fake token")

    @endpoints.method(
        message_types.VoidMessage,
        ServiceAccountKeyResponse,
        path='fence/serviceaccount/key',
        http_method='GET',
        name='get fence service account key')
    def service_account_key(self, request):
        return ServiceAccountKeyResponse(data={"foo": "bar"})

    @endpoints.method(
        SCOPES_RESOURCE,
        ServiceAccountAccessTokenResponse,
        path='fence/serviceaccount/accesstoken',
        http_method='GET',
        name='get fence service account access token')
    def service_account_accesstoken(self, request):
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
