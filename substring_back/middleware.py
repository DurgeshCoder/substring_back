import time

class GlobalAPIDelayMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Delay before processing view
        # time.sleep(2)

        response = self.get_response(request)
        return response