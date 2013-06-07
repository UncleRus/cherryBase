# -*- coding: utf-8 -*-

__version__ = '0.1.0'

import cherrypy

from . import base, rpc, bgtasks, utils, tools

cherrypy.engine.bg_tasks_queue = bgtasks.TasksQueue (cherrypy.engine)
cherrypy.engine.cron = bgtasks.Cron (cherrypy.engine)

toolbox = cherrypy.tools

from tools.gpg import GpgIn, GpgOut
toolbox.gpg_in = GpgIn ()
toolbox.gpg_out = GpgOut ()

from tools.jinja import JinjaTool
toolbox.jinja = JinjaTool ()

from tools.auth import AuthTool, BaseUser, AuthController
toolbox.auth = AuthTool ()

from base import Application, Server, _server_conf as server_conf

