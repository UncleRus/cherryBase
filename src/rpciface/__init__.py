# -*- coding: utf-8 -*-

from . import controllers
import rco

def get_applications (mode, basename):

    return rco.Service (
        package = __package__,
        basename = basename,
        mode = mode,
        vhosts = ('rpc.',),
        root = controllers.Root
    )