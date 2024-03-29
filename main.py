import logging
import logging.config
import os

import flask
import google.cloud.logging
import sentry_sdk
import yaml
from flask_cors import CORS
from google.auth.credentials import AnonymousCredentials
from google.cloud import ndb
from sentry_sdk.integrations.flask import FlaskIntegration

from bond_app import routes
from bond_app.json_exception_handler import JsonExceptionHandler
from bond_app.swagger_ui import swaggerui_blueprint, SWAGGER_URL

SENTRY_DSN = os.environ.get("SENTRY_DSN")
SENTRY_ENVIRONMENT = os.environ.get("SENTRY_ENVIRONMENT")
if SENTRY_DSN is not None:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=SENTRY_ENVIRONMENT,
        integrations=[
            FlaskIntegration(),
        ],
        # By default the SDK will try to use the SENTRY_RELEASE
        # environment variable, or infer a git commit
        # SHA as release, however you may want to set
        # something more human-readable.
        # release="myapp@1.0.0",
    )

client = None
if os.environ.get('DATASTORE_EMULATOR_HOST'):
    # If we're running the datastore emulator, we should use anonymous credentials to connect to it.
    # The project should match the project given to the Datastore Emulator. See tests/datastore_emulator/run_emulator.sh
    client = ndb.Client(project="test", credentials=AnonymousCredentials())
elif os.environ.get('DATASTORE_GOOGLE_PROJECT'):
    project = os.environ.get('DATASTORE_GOOGLE_PROJECT')
    client = ndb.Client(project)
else:
    # Otherwise, create a client grabbing credentials normally from cloud environment variables.
    client = ndb.Client()


def ndb_wsgi_middleware(wsgi_app):
    """Wrap an app so that each request gets its own NDB client context."""

    def middleware(environ, start_response):
        with client.context():
            return wsgi_app(environ, start_response)

    return middleware


def setup_logging():
    """
    If we are running as a GAE application, we need to set up Stackdriver logging.
    Stackdriver logging will encounter errors if it doesn't have access to the right project credentials.

    Proceeds to load the custom logging configuration for the app.
    :return:
    """
    default_log_level = logging.DEBUG
    if os.environ.get('GAE_APPLICATION'):
        # Connects the logger to the root logging handler; by default this captures
        # all logs at INFO level and higher
        logging_client = google.cloud.logging.Client()
        logging_client.setup_logging(log_level=default_log_level)

    # Default logging config to be used if we fail reading from the file
    logging_config = {"version": 1,
                      "disable_existing_loggers": False,
                      "root": {
                          "level": default_log_level
                      }
                      }

    log_config_file_path = 'log_config.yaml'
    try:
        with open(log_config_file_path, 'rt') as f:
            logging_config = yaml.safe_load(f.read())
            logging.debug("Successfully read Logging Config from: {}".format(log_config_file_path))
    except Exception:
        # TODO: How do we determine what specific exception types to handle here?
        logging.basicConfig(level=default_log_level)
        logging.exception("Error trying to configure logging with file: {}.  Using default settings."
                          .format(log_config_file_path))

    logging.config.dictConfig(logging_config)
    logging.info("Logging configured")


def create_app():
    """Initializes app."""
    logging.info("Creating Flask app")
    flask_app = flask.Flask(__name__)
    flask_app.register_blueprint(routes.routes)
    flask_app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
    CORS(flask_app)
    logging.info("Flask app created")
    return flask_app


# Logging setup/config should happen as early as possible so that we can log using our desired settings.  If you want to
# log anything in this file, make sure you call `setup_logging()` first and then get the right logger as follows:
# logger = logging.getLogger(__name__)
setup_logging()
app = create_app()
app.wsgi_app = ndb_wsgi_middleware(app.wsgi_app)  # Wrap the app in middleware.
handler = JsonExceptionHandler(app)


@app.after_request
def add_nosniff_content_type_header(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "deny"
    return response

@app.after_request
def add_strict_transport_security_header(response):
    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Strict-Transport-Security
    # recommended settings by mozilla, max-age is 2 years in seconds
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    return response

@app.after_request
def add_cache_control_header(response):
    # https://grayduck.mn/2021/09/13/cache-control-recommendations/
    response.headers["Cache-Control"] = "max-age=0, must-revalidate, no-cache, no-store, private"
    return response
