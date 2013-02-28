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


def create_rotating_log (log = cherrypy.log, debug = True):
    log.screen = debug
    if log.f_error:
        log.error_file = ''
        log.error_log.addHandler (_create_handler (log.f_error, debug))
    if log.f_access:
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
