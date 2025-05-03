from rest_framework.request import Request
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView


class FivePerMinuteRateLimit(SimpleRateThrottle):
    """
    Custom throttle class that allows 5 requests per minute.
    """

    rate = "5/min"

    def get_cache_key(self, request: Request, view: APIView) -> str:
        return self.get_ident(request)
