from django.utils.deprecation import MiddlewareMixin

class XFrameOptionsMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if request.path.startswith('/admin'):
            response['X-Frame-Options'] = 'ALLOWALL'
        else:
            response['X-Frame-Options'] = 'DENY'
        return response
