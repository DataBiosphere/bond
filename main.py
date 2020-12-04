import flask
import os
from bond_app import routes
from bond_app.swagger_ui import swaggerui_blueprint, SWAGGER_URL
from bond_app.json_exception_handler import JsonExceptionHandler
from google.cloud import ndb
import google.cloud.logging
from google.auth.credentials import AnonymousCredentials
from flask_cors import CORS

client = None
if os.environ.get('DATASTORE_EMULATOR_HOST'):
    # If we're running the datastore emulator, we should use anonymous credentials to connect to it.
    # The project should match the project given to the Datastore Emulator. See tests/datastore_emulator/run_emulator.sh
    client = ndb.Client(project="test", credentials=AnonymousCredentials())
else:
    # Otherwise, create a client grabbing credentials normally from cloud environment variables.
    client = ndb.Client()


def ndb_wsgi_middleware(wsgi_app):
    """Wrap an app so that each request gets its own NDB client context."""

    def middleware(environ, start_response):
        with client.context():
            return wsgi_app(environ, start_response)

    return middleware

def setup_stackdriver_logging():
    if not os.environ.get('GAE_APPLICATION'):
        # If we're not running as a GAE application, we do not need to set up Stackdriver logging.
        # Stackdriver logging will encounter errors if it doesn't have access to the right project credentials.
        return
    logging_client = google.cloud.logging.Client()
    # Connects the logger to the root logging handler; by default this captures
    # all logs at INFO level and higher
    logging_client.setup_logging()

def create_app():
    """Initializes app."""
    flask_app = flask.Flask(__name__)
    flask_app.register_blueprint(routes.routes)
    flask_app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
    CORS(flask_app)
    return flask_app


app = create_app()
app.wsgi_app = ndb_wsgi_middleware(app.wsgi_app)  # Wrap the app in middleware.
setup_stackdriver_logging()
handler = JsonExceptionHandler(app)


@app.after_request
def add_nosniff_content_type_header(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response
