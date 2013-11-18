# -*- coding: utf-8 -*-

from ..base import ThreadedPool, ShortcutsMixin
from mysql_rco import Connection


class _Connection (Connection, ShortcutsMixin):
    pass


class MySql (ThreadedPool):

    def __init__ (self, min_connections = 0, max_connections = 40, *args, **kwargs):
        super (MySql, self).__init__ (_Connection, min_connections, max_connections, **kwargs)

