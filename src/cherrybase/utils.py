# -*- coding: utf-8 -*-

import cherrypy
import re
import logging


def to_type (type_, value, default):
    try:
        return type_ (value)
    except (ValueError, TypeError):
        return default


def to_int (value, default = 0):
    return to_type (int, value, default)


def to_bool (value, default = False):
    return value is not None and str (value).lower () in ('yes', 'true', '1')


def escape (s):
    if s is None:
        return s
    return s.replace ('&', '&amp;') \
        .replace ('<', '&lt;') \
        .replace ('>', '&gt;') \
        .replace ('"', '&quot;')


def get_cookie (name, default = None):
    cookie = cherrypy.request.cookie.get (name)
    return cookie.value if cookie else default


def set_cookie (name, value, path = '/', max_age_seconds = 2592000):
    from datetime import datetime, timedelta
    cookie = cherrypy.response.cookie
    cookie [name] = value
    cookie [name]['path'] = path
    cookie [name]['expires'] = (datetime.now () + timedelta (seconds = max_age_seconds)).strftime ('%a, %d %b %Y %H:%M:%S') \
        if max_age_seconds > 0 else 0


def match_list (patterns, string, flags = re.UNICODE):
    return [pattern for pattern in patterns if re.match (pattern, string, flags)]


class AttributeDict (dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


def _create_handler (filename, debug = True):
    import logging.handlers
    result = logging.handlers.TimedRotatingFileHandler (filename, 'midnight')
    if debug:
        result.setLevel (logging.DEBUG)
    result.setFormatter (cherrypy._cplogging.logfmt)
    return result


def setup_log (log = cherrypy.log, debug = True):
    if hasattr (log, 'f_error') and log.f_error:
        log.error_file = ''
        log.error_log.addHandler (_create_handler (log.f_error, debug))
    if hasattr (log, 'f_access') and log.f_access:
        log.access_file = ''
        log.access_log.addHandler (_create_handler (log.f_access, debug))


class Log (object):

    def __init__ (self, name, filename, debug = True):
        level = logging.DEBUG if debug else logging.WARNING
        self._logger = logging.getLogger (name)
        self._logger.setLevel (level)
        self._logger.addHandler (_create_handler (filename, debug))
        if debug:
            handler = logging.StreamHandler ()
            handler.setLevel (level)
            self._logger.addHandler (handler)

    def error (self, msg = '', context = '', severity = logging.INFO, traceback = False):
        if traceback:
            msg += cherrypy._cperror.format_exc ()
        self._logger.log (severity, ' '.join ((cherrypy.log.time (), context, msg)))


class PoolsCatalog (object):

    def __init__ (self, log_context):
        self.pools = {}
        self.objects = {}
        self.log_context = log_context
        cherrypy.engine.subscribe ('start_thread', self._start_thread)
        cherrypy.engine.subscribe ('stop_thread', self._stop_thread)
        self._start_thread (-1)

    def _start_thread (self, thread_index):
        cherrypy.thread_data.index = thread_index
        self.objects [thread_index] = {}

    def _stop_thread (self, thread_index):
        if thread_index not in self.objects:
            return
        for name, object in self.objects [thread_index].items ():
            try:
                self.pools [name].put (object)
            except:
                cherrypy.log.error (
                    'An error occured when freeing {}.{} object'.format (thread_index, name),
                    context = self.log_context,
                    severity = logging.WARNING,
                    traceback = True
                )
        del self.objects [thread_index]

    def __iter__ (self):
        return iter (self.pools)

    def __contains__ (self, name):
        return name in self.pools

    def __setitem__ (self, name, pool):
        if name in self.pools:
            if self.pools [name] == pool:
                return
            raise ValueError ('Pool {} alredy defined'.format (name))
        self.pools [name] = pool

    def __getitem__ (self, name):
        return self.pools [name]

    def get (self, name):
        if name not in self.pools:
            raise ValueError ('Unknown pool {}'.format (name))
        objects = self.objects [getattr (cherrypy.thread_data, 'index', -1)]
        if name not in objects:
            objects [name] = self.pools [name].get ()
        return objects [name]

    def put (self, name, obj):
        self.pools [name].put (obj)

