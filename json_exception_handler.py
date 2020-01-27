from flask import jsonify
from werkzeug import exceptions


class JsonExceptionHandler(object):
    def __init__(self, app=None):
        if app:
            self.init_app(app)

    def json_dict(self, status_code, message):
        exception_reasons = {400: "badRequest", 401: "required", 404: "notFound"}
        return {"code": status_code,
                "errors": [{
                    "domain": "global",
                    "message": message,
                    "reason": exception_reasons[status_code]
                }],
                "message": message}

    def std_handler(self, error):
        if isinstance(error, exceptions.HTTPException):
            response = jsonify(error=self.json_dict(error.code, error.description))
            response.status_code = error.code
        else:
            response = jsonify(error=str(error))
            response.status_code = 500
        return response

    def init_app(self, app):
        self.app = app
        self.register(exceptions.HTTPException)
        for code, v in exceptions.default_exceptions.iteritems():
            self.register(code)

    def register(self, exception_or_code, handler=None):
        self.app.errorhandler(exception_or_code)(handler or self.std_handler)
