#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cherrybase, cherrypy
import argparse
import logging
import sys, os

def parse_args ():
    result = argparse.ArgumentParser (description = 'CherryPy based server')
    result.add_argument ('--config', '-c', metavar = '<config file>', type = file, default = 'server.conf', help = 'Path to server configuration file')
    result.add_argument ('--mode', '-m', type = str, choices = ('production', 'debug'), default = 'debug', help = 'Server mode')
    result.add_argument ('--pid', '-p', metavar = '<PID file>', type = str, default = None, help = 'PID file')
    return result.parse_args ()

if __name__ == '__main__':
    cherrypy.config.update ({
        'log.f_access': None,
        'log.f_error': None
    })
    get_conf = cherrypy.config.get

    args = parse_args ()
    debug = args.mode == 'debug'

    server = cherrybase.Server (config = args.config, debug = debug)

    cherrybase.utils.setup_log (debug = debug)

    pkg_path = get_conf ('server.pkg_path', os.path.dirname (__file__))
    if not os.path.exists (pkg_path):
        raise RuntimeError ('Invalid server packages path (server.pkg_path): {}'.format (pkg_path))
    if pkg_path not in sys.path:
        sys.path.append (pkg_path)

    basename = get_conf ('server.basename', get_conf ('server.socket_host', '127.0.0.1'))
    port = get_conf ('server.socket_port', 8080)
    if port != 80:
        basename = '{}:{}'.format (basename, port)

    if args.pid != None:
        cherrypy.config.update ({
            'daemon.on': True,
            'daemon.pid_file': args.pid
        })

    for pkg_name in get_conf ('server.packages', []):
        cherrypy.log.error ('Importing package "{}"'.format (pkg_name), 'SERVER')
        module = __import__ (pkg_name)
        applications = module.get_applications (args.mode, basename)
        if isinstance (applications, cherrybase.Application):
            applications = [applications]
        cherrypy.log.error ('Applications found: {}'.format ([app.name for app in applications]), 'SERVER')
        server.applications += applications

    if not server.applications:
        cherrypy.log.error ('No app packages were found', 'SERVER', logging.FATAL)
    else:
        server.start ()
