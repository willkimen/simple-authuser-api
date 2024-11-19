from rest_framework.throttling import SimpleRateThrottle


class FivePerMinuteRateLimit(SimpleRateThrottle):
    """
    Custom throttle class that allows 5 requests per minute.
    """

    rate = "5/min"

    def get_cache_key(self, request, view) -> str:
        return self.get_ident(request)
