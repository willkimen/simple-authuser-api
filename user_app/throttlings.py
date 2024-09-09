from rest_framework.throttling import SimpleRateThrottle


class AccountActivationRequestRateLimit(SimpleRateThrottle):
    """
    Limits the rate of requests for account activation.

    This class uses rate limiting to control the number of requests made for
    account activation. It helps prevent abuse and protects the account
    activation endpoint from brute-force attacks.

    Attributes:
        scope (str): Defines the rate limit scope as "account_activation".

    Methods:
        get_cache_key(request, view): Generates a unique cache key for the request
                                      based on the scope and client identification.
    """

    scope = "account_activation"

    def get_cache_key(self, request, view) -> str | None:
        """
        Generates a unique cache key for the request.

        The key is based on the scope and client identification obtained through
        the `get_ident` method. The cache key is used to store and check the
        number of requests made.

        Args:
            request (Request): The incoming HTTP request.
            view (View): The view handling the request.

        Returns:
            str | None: The formatted cache key or None if the key cannot be generated.
        """
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }


class SendEmailActivateAccountRequestRateLimit(SimpleRateThrottle):
    """
    Limits the rate of requests for sending account activation emails.

    This class controls the frequency of requests for sending emails used to
    activate accounts. It helps prevent excessive email sending and potential
    abuse of the activation system.

    Attributes:
        scope (str): Defines the rate limit scope as "send_code_to_activate_account".

    Methods:
        get_cache_key(request, view): Generates a unique cache key for the request
                                      based on the scope and client identification.
    """

    scope = "send_code_to_activate_account"

    def get_cache_key(self, request, view) -> str | None:
        """
        Generates a unique cache key for the request.

        The key is based on the scope and client identification obtained through
        the `get_ident` method. The cache key is used to store and check the
        number of requests made.

        Args:
            request (Request): The incoming HTTP request.
            view (View): The view handling the request.

        Returns:
            str | None: The formatted cache key or None if the key cannot be generated.
        """
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }
