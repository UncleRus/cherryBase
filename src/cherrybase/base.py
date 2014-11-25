# -*- coding: utf-8 -*-

import cherrypy
import os, logging
from uuid import uuid1
from cherrybase.conf import ConfigNamespace
from cherrypy import _cptree, _cpconfig, _cpwsgi
from . import utils


class _Stub (object):
    pass


class ApplicationTree (object):

    def __init__ (self, owner, stub_factory = _Stub):
        self.owner = owner
        self.stub_factory = stub_factory
        self.clear ()

    def clear (self):
        self.root = None

    def handler_exists (self, path_list):
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
            self.root = self.stub_factory ()
        result = self.root
        for element in path_list:
            if not hasattr (result, element):
                setattr (result, element, self.stub_factory ())
            result = getattr (result, element)
        return result

    def add (self, path, handler, config = None):
        stripped_path = path.strip ('/')
        path_list = stripped_path.split ('/') if stripped_path else []

        if self.handler_exists (path_list):
            raise AttributeError ('Path "{0}" is busy in "{1}"'.format (path, self.owner.name))

        if config:
            if not hasattr (handler, '_cp_config'):
                handler._cp_config = {}
            _cpconfig.merge (handler._cp_config, config)

        handler._cp_mount_path = '/' + stripped_path
        if not path_list:
            self.root = handler
        else:
            setattr (self.find_owner (path_list [0:-1]), path_list [-1], handler)
        cherrypy.log.error ('{} mounted on "{}" in "{}"'.format (type (handler).__name__, path, self.owner.name), 'TREE')


class Application (object):

    def __init__ (self, name = None, config = None, vhosts = None, routes = None):
        self.name = name or uuid1 ()
        self.vhosts = vhosts or [self.name]
        if isinstance (self.vhosts, basestring):
            self.vhosts = [self.vhosts]
        self.tree = ApplicationTree (self)
        self.config = config
        self.app = _cptree.Application (None, '', self.config)
        if routes:
            for path, handler, cfg in routes:
                self.tree.add (path, handler, cfg)

    def _log_name (self, log_type = 'access'):
        name = 'log.f_' + log_type
        cfg = self.app.find_config ('/', name, None)
        if cfg:
            return cfg
        cfg = cherrypy.config.get (name, None)
        return '{}/{}.{}.log'.format (os.path.dirname (cfg), self.name, log_type) if cfg else None

    def prepare (self, debug = True):
        self.app.root = self.tree.root
        if not debug:
            self.app.merge ({
                '/': {
                    'log.f_access': self._log_name ('access'),
                    'log.f_error': self._log_name ('error')
                }
            })
        utils.setup_log (self.app.log, debug)


_daemon_conf = ConfigNamespace (
    'daemon',
    {
        'on': False,
        'user': 'www-data',
        'group': 'www-data',
        'pid_file': '/var/run/cherrybase.pid'
    }
)
_server_conf = ConfigNamespace (
    'cherrybase',
    {
        'pkg_path': os.getcwd (),
        'packages': [],
        'main_handler': _Stub (),
        'block_interval': 0.1,
    }
)


class Server (object):

    def __init__ (self, applications = None, config = None, debug = True):
        self.applications = applications or []
        self.debug = debug
        if config:
            cherrypy.config.update (config)
        cherrypy.config.update ({'debug': debug})
        # настраиваем логи
        utils.setup_log (debug = self.debug)
        cherrypy.log.screen = self.debug
        if debug:
            cherrypy.log._get_builtin_handler (cherrypy.log.error_log, 'screen').setLevel (logging.DEBUG)
            cherrypy.log._get_builtin_handler (cherrypy.log.access_log, 'screen').setLevel (logging.DEBUG)

    def scan_applications (self):
        import sys

        if not _server_conf.pkg_path or not os.path.exists (_server_conf.pkg_path):
            cherrypy.log.error ('Invalid server packages path (cherrybase.pkg_path): {}'.format (_server_conf.pkg_path), 'SERVER', logging.FATAL)
            raise ValueError ('Undefined cherrybase.pkg_path')
        if _server_conf.pkg_path not in sys.path:
            sys.path.append (_server_conf.pkg_path)

        basename = cherrypy.config.get ('server.basename', cherrypy.config.get ('server.socket_host', '127.0.0.1'))
        port = cherrypy.config.get ('server.socket_port', 8080)
        if port != 80:
            basename = '{}:{}'.format (basename, port)

        for pkg_name in [_server_conf.packages] if isinstance (_server_conf.packages, basestring) else _server_conf.packages:
            cherrypy.log.error ('Importing package "{}"'.format (pkg_name), 'SERVER')
            module = __import__ (pkg_name)
            applications = module.get_applications ('debug' if self.debug else 'production', basename)
            if isinstance (applications, Application):
                applications = [applications]
            cherrypy.log.error ('Applications found: {}'.format ([app.name for app in applications]), 'SERVER')
            self.applications += applications

    def start (self):
        vhosts = {}
        for app in self.applications:
            app.prepare (self.debug)
            vhosts.update ({host: app.app for host in app.vhosts})
            cherrypy.log.error ('Application {} virtual hosts: {}'.format (app.name, app.vhosts), 'SERVER')

        self.daemonize ()

        cherrypy.tree.graft (
            _cpwsgi.VirtualHost (
                _cptree.Application (_server_conf.main_handler),
                domains = vhosts
            )
        )

        if hasattr (cherrypy.engine, 'signal_handler'):
            cherrypy.engine.signal_handler.subscribe ()
        cherrypy.engine.start ()
        cherrypy.engine.block (interval = _server_conf.block_interval)

    def stop (self):
        cherrypy.engine.stop ()

    def daemonize (self):
        if not _daemon_conf.on:
            return

        if os.name == 'posix' and os.getuid () == 0:
            from cherrypy.process.plugins import DropPrivileges
            import grp, pwd
            try:
                uid = pwd.getpwnam (_daemon_conf.user)[2]
                gid = grp.getgrnam (_daemon_conf.group)[2]
            except KeyError:
                cherrypy.log.error (
                    'Cannot find user "{0}" or group "{1}"'.format (_daemon_conf.user, _daemon_conf.group),
                    'SERVER',
                    logging.FATAL
                )
                raise
            cherrypy.drop_privileges = DropPrivileges (cherrypy.engine, uid = uid, gid = gid).subscribe ()

        from cherrypy.process.plugins import PIDFile, Daemonizer
        if _daemon_conf.pid_file:
            PIDFile (cherrypy.engine, _daemon_conf.pid_file).subscribe ()
        Daemonizer (cherrypy.engine).subscribe ()
