#!/usr/bin/env python
# -*- coding: utf-8 -*-
import cherrybase, cherrypy
import argparse

def parse_args ():
    result = argparse.ArgumentParser (description = 'CherryPy based server')
    result.add_argument ('--config', '-c', metavar = '<config file>', type = file, default = 'server.conf', help = 'Path to server configuration file')
    result.add_argument ('--mode', '-m', type = str, choices = ('production', 'debug'), default = 'debug', help = 'Server mode')
    return result.parse_args ()

if __name__ == '__main__':
    args = parse_args ()
    server = cherrybase.Server (config = args.config)

    basename = cherrypy.config.get ('server.basename', '127.0.0.1')
    port = cherrypy.config.get ('server.socket_port', 8080)
    if port != 80:
        basename = '{}:{}'.format (basename, port)

    module = __import__ ('app')
    applications = module.get_applications (args.mode, basename)
    if isinstance (applications, cherrybase.Application):
        applications = [applications]

    server.applications += applications
    server.start ()
