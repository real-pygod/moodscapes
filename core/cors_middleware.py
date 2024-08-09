from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

# from django.utils.deprecation import MiddlewareMixin

class CustomCORSHeadersMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if request.path.startswith(settings.MEDIA_URL):
            response['Access-Control-Allow-Origin'] = '*'
        return response
