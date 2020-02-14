from flask_swagger_ui import get_swaggerui_blueprint
from yaml import Loader, load

SWAGGER_URL = '/api/docs'  # URL for exposing Swagger UI (without trailing '/')

swagger_yml = load(open('./swagger/api-docs.yaml', 'r'), Loader=Loader)

# Call factory function to create our blueprint
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
    None,
    config={'spec': swagger_yml},
)