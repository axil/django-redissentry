
try:
    from threading import local
except ImportError:
    from django.utils._threading_local import local             ##

_thread_locals = local()

def get_request():
    return getattr(_thread_locals, 'request', None)

class RequestMiddleware(object):
    """Provides access to the request object via thread locals"""
    def process_request(self, request):
        _thread_locals.request = request

    def process_response(self, request, response):
        if hasattr(_thread_locals, 'request'):
            delattr(_thread_locals, 'request')
        return response
