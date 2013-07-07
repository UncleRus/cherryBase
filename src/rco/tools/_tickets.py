# -*- coding: utf-8 -*-

from rco import BaseError
import time


class AuthError (BaseError):
    pass


class Ticket (object):

    def __init__ (self, tid, data = {}):
        self.tid = tid
        self.login = data.get ('login')
        self.expire = data.get ('expire')
        self.data = data.get ('data', {})
        self._valid = True

    @property
    def valid (self):
        return self._valid and self.expire - int (time.time ()) > 0

    @valid.setter
    def valid (self, value):
        self._valid = value
