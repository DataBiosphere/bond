import logging

from flask import Blueprint, request, redirect
import configparser
import os
from werkzeug import exceptions
from webargs import fields
from webargs.flaskparser import FlaskParser

from protorpc import message_types
from protorpc import messages
from protorpc import protojson

from . import authentication
from .bond import Bond
from .datastore_cache_api import DatastoreCacheApi
from .fence_token_vending import FenceTokenVendingMachine
from .fence_api import FenceApi
from . import fence_token_storage
from .open_id_config import OpenIdConfig
from .sam_api import SamApi
from .oauth_adapter import OauthAdapter
from .status import Status
from .token_store import TokenStore
from .oauth2_state_store import OAuth2StateStore
import json
import ast
from .util import get_provider_secrets


class Parser(FlaskParser):
    DEFAULT_VALIDATION_STATUS = 400


parser = Parser()
use_args = parser.use_args


class JsonField(messages.StringField):
    type = dict


class ListProvidersResponse(messages.Message):
    providers = messages.StringField(1, repeated=True)


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
    subsystem = messages.StringField(3)


class StatusResponse(messages.Message):
    ok = messages.BooleanField(1)
    subsystems = messages.MessageField(SubSystemStatusResponse, 2, repeated=True)


class AuthorizationUrlResponse(messages.Message):
    url = messages.StringField(1)

class LinkNotFoundResponse(messages.Message):
    message = messages.StringField(1)


def json_response(message):
    """Given a protorpc message, return a json response tuple understood by flask: (json, status code, headers)"""
    return protojson.encode_message(message), 200, {'Content-Type': 'application/json'}


config = configparser.ConfigParser()
config.read("config.ini")


def is_provider(section_name):
    return section_name != 'sam' and section_name != 'bond_accepted'


def create_provider(provider_name):
    client_id, client_secret = get_provider_secrets(config, provider_name)
    open_id_config_url = config.get(provider_name, 'OPEN_ID_CONFIG_URL')
    fence_base_url = config.get(provider_name, 'FENCE_BASE_URL')
    user_name_path_expr = config.get(provider_name, 'USER_NAME_PATH_EXPR')

    extra_authz_url_params = {}
    extra_params_key = 'EXTRA_AUTHZ_URL_PARAMS'
    if config.has_option(provider_name, extra_params_key):
        extra_params_raw = config.get(provider_name, extra_params_key)
        extra_authz_url_params = ast.literal_eval(extra_params_raw)

    open_id_config = OpenIdConfig(provider_name, open_id_config_url, cache_api)
    oauth_adapter = OauthAdapter(client_id, client_secret, open_id_config, provider_name)
    fence_api = FenceApi(fence_base_url)

    fence_tvm = FenceTokenVendingMachine(fence_api, cache_api, refresh_token_store, oauth_adapter,
                                         provider_name, fence_token_storage.FenceTokenStorage())
    return BondProvider(fence_tvm, Bond(oauth_adapter,
                                        fence_api,
                                        cache_api,
                                        refresh_token_store,
                                        oauth2_state_store,
                                        fence_tvm,
                                        provider_name,
                                        user_name_path_expr,
                                        extra_authz_url_params))


def _get_provider(provider_name):
    if provider_name in bond_providers:
        return bond_providers[provider_name]
    else:
        raise exceptions.NotFound("provider {} not found".format(provider_name))


class BondProvider:
    def __init__(self, fence_tvm, bond):
        self.fence_tvm = fence_tvm
        self.bond = bond


routes = Blueprint('bond', __name__)

cache_api = DatastoreCacheApi()
refresh_token_store = TokenStore()
oauth2_state_store = OAuth2StateStore()

bond_providers = {section_name: create_provider(section_name)
                  for section_name in config.sections() if is_provider(section_name)}

sam_base_url = config.get('sam', 'BASE_URL')
sam_api = SamApi(sam_base_url)
authentication_config = authentication.AuthenticationConfig(os.environ.get('BOND_MAX_TOKEN_LIFE', 600))
auth = authentication.Authentication(authentication_config, cache_api, sam_api)

api_version = 'v1'
link_api_routes_base = '/api/link/'
v1_link_route_base = link_api_routes_base + api_version


@routes.route(v1_link_route_base + '/providers', methods=["GET"], strict_slashes=False)
def list_providers():
    logging.debug("Listing providers")
    return json_response(ListProvidersResponse(providers=list(bond_providers.keys())))


@routes.route(v1_link_route_base + '/<provider>/oauthcode', methods=["POST"], strict_slashes=False)
@use_args({"oauthcode": fields.Str(required=True),
           "redirect_uri": fields.Str(required=True),
           "state": fields.Str(required=True)},
          locations=("querystring",))
def oauthcode(args, provider):
    sam_user_id = auth.auth_user(request)
    logging.info(f"Received OAuth Code for user {sam_user_id} from provider {provider}")
    issued_at, username = _get_provider(provider).bond.exchange_authz_code(args['oauthcode'], args['redirect_uri'],
                                                                           sam_user_id, args['state'], provider)
    return json_response(LinkInfoResponse(issued_at=issued_at, username=username))


@routes.route(v1_link_route_base + '/<provider>', methods=["GET"], strict_slashes=False)
def link_info(provider):
    sam_user_id = auth.auth_user(request)
    logging.debug(f"Retrieving link information for {sam_user_id} to provider {provider}")
    refresh_token = _get_provider(provider).bond.get_link_info(sam_user_id)
    if refresh_token:
        return json_response(LinkInfoResponse(issued_at=refresh_token.issued_at, username=refresh_token.username))
    else:
        return protojson.encode_message(
            LinkNotFoundResponse(message=f"{provider} link does not exist. Consider re-linking your account.")
        ), \
               404, \
               {'Content-Type': 'application/json'}


@routes.route(v1_link_route_base + '/<provider>', methods=["DELETE"], strict_slashes=False)
def delete_link(provider):
    sam_user_id = auth.auth_user(request)
    logging.info(f"Deleting link for user {sam_user_id} to provider {provider}")
    _get_provider(provider).bond.unlink_account(sam_user_id)
    return '', 204


@routes.route(v1_link_route_base + '/<provider>/accesstoken', methods=["GET"])
def accesstoken(provider):
    sam_user_id = auth.auth_user(request)
    access_token, expires_at = _get_provider(provider).bond.get_access_token(sam_user_id)
    logging.info(f"Retrieving access token for user {sam_user_id} for provider {provider}")
    return json_response(AccessTokenResponse(token=access_token, expires_at=expires_at))


@routes.route(v1_link_route_base + '/<provider>/serviceaccount/key', methods=["GET"], strict_slashes=False)
def service_account_key(provider):
    sam_user_id = auth.auth_user(request)
    logging.info(f"Retrieving service account key for user {sam_user_id} for provider {provider}")
    return json_response(ServiceAccountKeyResponse(data=json.loads(
        _get_provider(provider).fence_tvm.get_service_account_key_json(sam_user_id))))


@routes.route(v1_link_route_base + '/<provider>/serviceaccount/accesstoken', methods=["GET"], strict_slashes=False)
@use_args({"scopes": fields.List(fields.Str(), missing=None)},
          locations=("querystring",))
def service_account_accesstoken(args, provider):
    sam_user_id = auth.auth_user(request)
    logging.info(f"Retrieving service account access token for user {sam_user_id} for provider {provider}")
    return json_response(ServiceAccountAccessTokenResponse(
        token=_get_provider(provider).fence_tvm.get_service_account_access_token(sam_user_id, args['scopes'])))


@routes.route(v1_link_route_base + '/<provider>/authorization-url', methods=["GET"], strict_slashes=False)
@use_args({"scopes": fields.List(fields.Str(), missing=None),
           "redirect_uri": fields.Str(required=True),
           "state": fields.Str(missing=None)},
          locations=("querystring",))
def authorization_url(args, provider):
    sam_user_id = auth.auth_user(request)
    authz_url = _get_provider(provider).bond.build_authz_url(args['scopes'], args['redirect_uri'], sam_user_id,
                                                             provider, args['state'])
    logging.info(f"Retrieving authorization-url for user {sam_user_id} for provider {provider}")
    return json_response((AuthorizationUrlResponse(url=authz_url)))


@routes.route('/api/status/v1/status', methods=["GET"], strict_slashes=False)
def get_status():
    sam_base_url = config.get('sam', 'BASE_URL')

    subsystems_to_ignore = os.environ.get('SUBSYSTEMS_TO_IGNORE', '').split(',')
    providers = {section_name: FenceApi(config.get(section_name, 'FENCE_BASE_URL'))
                 for section_name in config.sections() if is_provider(section_name) and section_name not in subsystems_to_ignore}

    sam_api = SamApi(sam_base_url)
    status_service = Status(sam_api, providers, cache_api)

    subsystems = status_service.get()

    ok = all(subsystem["ok"] for subsystem in subsystems)
    response = json_response(StatusResponse(ok=ok,
                                            subsystems=[SubSystemStatusResponse(ok=subsystem["ok"],
                                                                                message=subsystem["message"],
                                                                                subsystem=subsystem["subsystem"])
                                                        for subsystem in subsystems]))
    if ok:
        return response
    else:
        logging.warning("Bond status NOT OK:\n%s" % response[0])
        raise exceptions.InternalServerError(response[0])


@routes.route('/', methods=["GET"], strict_slashes=False)
def redirect_to_swagger():
    return redirect('/api/docs')
