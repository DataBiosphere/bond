import flask
import routes
from json_exception_handler import JsonExceptionHandler


def create_app():
    """Initializes app."""
    flask_app = flask.Flask(__name__)
    flask_app.register_blueprint(routes.routes)
    return flask_app


app = create_app()
handler = JsonExceptionHandler(app)
