# -*- coding: utf-8 -*-

from . import controllers
import rco
from cherrybase import orm, db
import cherrybase.db.drivers.sqlite as sqlite

def get_applications (mode, basename):

    service = rco.Service (
        package = __package__,
        basename = basename,
        mode = mode,
        vhosts = ('rpc.',),
        root = controllers.Root
    )
    return service
