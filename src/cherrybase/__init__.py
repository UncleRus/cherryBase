# -*- coding: utf-8 -*-

__version__ = '0.1.0'

import cherrypy

toolbox = cherrypy.tools

import cherrybase.tools as tools
from tools.gpg import GpgIn, GpgOut
toolbox.gpg_in = GpgIn ()
toolbox.gpg_out = GpgOut ()

from tools.jinja import JinjaTool
toolbox.jinja = JinjaTool ()

from tools.auth import AuthTool
toolbox.auth = AuthTool ()

from cherrybase import utils, engine, rpc, conf
from cherrybase.app import ControllersTree
