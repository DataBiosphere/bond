# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START gae_python37_render_template]
import datetime
from . import authentication

from flask import Flask, jsonify, abort, make_response, request

app = Flask(__name__)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.errorhandler(401)
def unauthorized(error):
    return make_response(jsonify({'error': 'Unauthorized'}, 401))


@app.route('/')
def root():
    auth_config = authentication.default_config()
    auth = authentication.Authentication(auth_config)
    bearer_token = request.headers.get('Authorization')
    user_info = auth.require_user_info(request)
    if not bearer_token or not user_info:
        abort(401)
    else:
        # For the sake of example, use static information to inflate the template.
        # This will be replaced with real information in later steps.
        dummy_times = {"times": [datetime.datetime(2018, 1, 1, 10, 0, 0),
                                 datetime.datetime(2018, 1, 2, 10, 30, 0),
                                 datetime.datetime(2018, 1, 3, 11, 0, 0),
                                 ],
                       "bearer": bearer_token}
        return jsonify(dummy_times)


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
# [START gae_python37_render_template]
