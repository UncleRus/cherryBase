# -*- coding: utf-8 -*-

__version__ = '0.4.5'

import cherrypy

from . import base, rpc, plugins, utils, tools

cherrypy.engine.bg_tasks_queue = plugins.TasksQueue (cherrypy.engine)
cherrypy.engine.task_manager = plugins.TaskManager (cherrypy.engine)
cherrypy.engine.starter_stopper = plugins.StarterStopper (cherrypy.engine)

toolbox = cherrypy.tools

from tools.jinja import JinjaTool
toolbox.jinja = JinjaTool ()

from tools.auth import AuthTool, BaseUser
toolbox.auth = AuthTool ()

from base import Application, Server, _server_conf as server_conf

