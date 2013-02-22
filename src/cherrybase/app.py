# -*- coding: utf-8 -*-

import cherrypy
from cherrypy.process.plugins import SimplePlugin
import os, logging
from uuid import uuid1
from cherrybase.conf import ConfigNamespace

class HandlerStub (object):
    pass

class ControllersTree (object):

    def __init__ (self, name, stub_class = HandlerStub):
        self.name = name
        self.stub_class = stub_class
        self.clear ()

    def clear (self):
        self.root = None

    def controller_exists (self, path_list):
        if not path_list:
            return bool (self.root)
        current = self.root
        for element in path_list:
            try:
                current = getattr (current, element)
            except AttributeError:
                return False
        return True

    def find_owner (self, path_list):
        if not path_list and not self.root:
            self.root = self.stub_class ()
        result = self.root
        for element in path_list:
            if not hasattr (result, element):
                setattr (result, element, self.stub_class ())
            result = getattr (result, element)
        return result

    def add (self, path, controller, config = None):
        stripped_path = path.strip ('/')
        path_list = stripped_path.split ('/') if stripped_path else []

        if self.controller_exists (path_list):
            raise AttributeError ('Path "{0}" is busy in "{1}"'.format (path, self.name))

        if config:
            if hasattr (controller, '_cp_config') and isinstance (controller._cp_config, dict):
                controller._cp_config.update (config)
            else:
                controller._cp_config = config

        controller._mount_path = '/' + stripped_path
        if not path_list:
            self.root = controller
        else:
            setattr (self.find_owner (path_list [0:-1]), path_list [-1], controller)
        cherrypy.log.error ('{} is mounted on "{}" in "{}"'.format (type (controller).__name__, path, self.name), 'TREE')


class Application (object):

    def __init__ (self, name = None, config = {}, version = '1.0', routes = (), vhosts = None):
        '''
        Args:
            name (str): Уникальный идентификатор приложения (мнемокод)
            config (dict): Конфигурация приложения
            version (str): Версия приложения
            routes (iterable): Список маршрутов приложения, например:
                (
                    ('/', my_root_controller, None),
                    ('/captcha', captcha_generator, {'tools.my_tool.on': True})
                )
            vhosts (list): Список виртуальных хостов, например:
                ['supersite.ru', 'www.supersite.ru']
        '''

        self.name = name if name else uuid1 ()
        self.config = config
        self.version = version
        self.vhosts = vhosts if vhosts else [self.name]
        self.tree = ControllersTree (self.name)

        for path, controller, conf in routes:
            self.tree.add (path, controller, conf)


_system_conf = ConfigNamespace (
    'system',
    {
        'block_interval': 0.1
    }
)

_daemon_conf = ConfigNamespace (
    'daemon',
    {
        'on': False,
        'user': 'www-data',
        'group': 'www-data',
        'pid_file': '/var/run/cherrybase.pid'
    }
)


class Server (object):

    def __init__ (self, applications = [], config = None):
        self.applications = applications
        if config:
            cherrypy.config.update (config)
        self.tree = ControllersTree ('__main__')

    def start (self):
        vhosts = {}
        for app in self.applications:
            path = '/' + app.name
            self.tree.add (path, app.tree.root, app.config)
            vhosts.update ({host: path for host in app.vhosts})
        self.daemonize ()

        cherrypy.tree.mount (
            self.tree.root,
            '/',
            {'/': {'request.dispatch': cherrypy.dispatch.VirtualHost (**vhosts)}}
        )

        if hasattr (cherrypy.engine, 'signal_handler'):
            cherrypy.engine.signal_handler.subscribe ()
        cherrypy.engine.start ()
        cherrypy.engine.block (_system_conf.block_interval)

    def daemonize (self):
        if not _daemon_conf.on:
            return

        from cherrypy.process.plugins import PIDFile, Daemonizer, DropPrivileges
        if os.name == 'posix':
            import grp, pwd
            try:
                uid = pwd.getpwnam (_daemon_conf.user)[2]
                gid = grp.getgrnam (_daemon_conf.group)[2]
            except KeyError:
                self.log ('Cannot find user "{0}" or group "{1}"'.format (_daemon_conf.user, _daemon_conf.group), logging.FATAL)
                raise
        else:
            uid = None
            gid = None

        DropPrivileges (cherrypy.engine, uid = uid, gid = gid).subscribe ()
        if _daemon_conf.pid_file:
            PIDFile (cherrypy.engine, _daemon_conf.pid_file).subscribe ()
        Daemonizer (cherrypy.engine).subscribe ()



