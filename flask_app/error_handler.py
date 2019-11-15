import flask, make_response, jsonify

blueprint = flask.Blueprint('error_handlers', __name__)


@blueprint.app_errorhandler(401)
def unauthorized(e):
    return make_response(jsonify({'error': 'Unauthorized'}, 401))


@blueprint.app_errorhandler(403)
def handle403(e):
    return '403 Forbidden: you absolutely cannot do this, also: ' + str(e.description)


@blueprint.app_errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)
