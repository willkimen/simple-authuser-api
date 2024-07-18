from rest_framework.throttling import SimpleRateThrottle


class AccountActivationRequestRateLimit(SimpleRateThrottle):
    scope = "account_activation"

    def get_cache_key(self, request, view) -> str | None:
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }


class SendEmailActivateAccountRequestRateLimit(SimpleRateThrottle):
    scope = "send_email_to_activate_account"

    def get_cache_key(self, request, view) -> str | None:
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }
