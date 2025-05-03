from drf_spectacular.extensions import OpenApiAuthenticationExtension


class CustomJWTAuthenticationScheme(OpenApiAuthenticationExtension):
    """
    This class extends `OpenApiAuthenticationExtension` from `drf-spectacular` to
    define custom authentication using JWT (JSON Web Token). It is used to configure
    Bearer authentication in OpenAPI documentation schemas, allowing the JWT standard
    to be specified in the generated documentation.

    The class defines the authentication scheme as `Bearer` and configures the format
    as `JWT` for authentication in the API.
    """

    target_class = "account_auth.authentication.authentication_classes.JWTAuthentication"
    name = "Bearer"

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
