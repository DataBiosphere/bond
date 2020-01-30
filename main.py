import flask
import routes
from json_exception_handler import JsonExceptionHandler
from google.cloud import ndb

client = ndb.Client()


def ndb_wsgi_middleware(wsgi_app):
    """Wrap an app so that each request gets its own NDB client context."""

    def middleware(environ, start_response):
        with client.context():
            return wsgi_app(environ, start_response)

    return middleware


def create_app():
    """Initializes app."""
    flask_app = flask.Flask(__name__)
    flask_app.register_blueprint(routes.routes)
    return flask_app


app = create_app()
app.wsgi_app = ndb_wsgi_middleware(app.wsgi_app)  # Wrap the app in middleware.
handler = JsonExceptionHandler(app)
