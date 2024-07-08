from rest_framework.throttling import SimpleRateThrottle


class ConfirmationRegisterThrottle(SimpleRateThrottle):
    scope = "confirmation_register"

    def get_cache_key(self, request, view) -> str | None:
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }
