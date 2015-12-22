
from datetime import datetime
from django.conf import settings
from django.db import connection
import pstats
from cStringIO import StringIO
from random import random
import logging

try:
    import cProfile as profile
except ImportError:
    import profile

class PerformanceMiddleware(object):
    _process_data = {}
    profiling = False
    logger = logging.getLogger(__name__)

    def process_view(self, request, callback, callback_args, callback_kwargs):
        # self is reused :(
        self._process_data = {}
        self.profiling = False
        self.profiler = None
        self._process_data['start_time'] = datetime.now()

        profile_per = getattr(settings, "PERFORMANCE_MIDDLEWARE_PROFILE_EVERY", 10)

        random_less_than = 1.0 / profile_per

        rand_val = random()

        if rand_val < random_less_than:
            self.profiling = True
            self.profiler = profile.Profile()
            args = (request,) + callback_args
            try:
                return self.profiler.runcall(callback, *args, **callback_kwargs)
            except:
                # we want the process_exception middleware to fire
                # https://code.djangoproject.com/ticket/12250
                return


    def process_response(self, request, response):
        now = datetime.now()

        start = self._process_data['start_time']
        td = (now - start)
        seconds_taken = (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10.0**6

        warning_threshold = getattr(settings, "PERFORMANCE_MIDDLEWARE_WARNING_THRESHOLD", 1.0)
        error_threshold = getattr(settings, "PERFORMANCE_MIDDLEWARE_ERROR_THRESHOLD", 2.0)
        critical_threshold = getattr(settings, "PERFORMANCE_MIDDLEWARE_CRITICAL_THRESHOLD", 5.0)

        if (seconds_taken < warning_threshold) and (seconds_taken < error_threshold) and (seconds_taken < critical_threshold):
            return response

        io = StringIO()
        io.write("Time taken: %f seconds\n" % seconds_taken)
        io.write("Request: \n%s\n" % request.__str__())
        io.write("Profile: \n")

        if self.profiling:
            self.profiler.create_stats()
            stats = pstats.Stats(self.profiler, stream=io)
            stats.sort_stats('cumulative')
            stats.print_stats(100)
        else:
            io.write("No profile for this request, sorry")

        io.write("SQL:\n")

        for query in connection.queries:
            io.write("Time: %s, Query: %s\n" % (query['time'], query['sql']))

        if seconds_taken > critical_threshold:
            self.logger.critical(io.getvalue())

        elif seconds_taken > error_threshold:
            self.logger.error(io.getvalue())

        elif seconds_taken > warning_threshold:
            self.logger.warning(io.getvalue())

        return response
