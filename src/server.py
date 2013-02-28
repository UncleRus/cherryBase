#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cherrybase, cherrypy
import argparse
import logging

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

    args = parse_args ()
    server = cherrybase.Server (config = args.config)
    get_conf = cherrypy.config.get

    cherrybase.utils.create_rotating_log (debug = args.mode == 'debug')

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
        cherrypy.log.error ('No packages was found', 'SERVER', logging.FATAL)
    else:
        server.start ()
