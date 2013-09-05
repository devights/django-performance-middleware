
from threading import currentThread
from datetime import datetime

class PerformanceMiddleware(object):
    _process_data = {}
    def process_request(self, request):
        thread_id = currentThread()
        _process_data[thread_id]['start_time'] = datetime.now()

    def process_response(self, response):
        now = datetime.now()
        thread_id = currentThread()

        start = _process_data[thread_id]['start_time']
        microseconds = (now - start).microseconds

        print "MS: %i" % (microseconds)
        return response
