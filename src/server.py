#!/usr/bin/env python
# -*- coding: utf-8 -*-
import cherrybase, cherrypy
import argparse

def parse_args ():
    result = argparse.ArgumentParser (description = 'CherryPy based server')
    result.add_argument ('--config', '-c', metavar = '<config file>', type = file, default = 'server.conf', help = 'Path to server configuration file')
    result.add_argument ('--mode', '-m', type = str, choices = ('production', 'debug'), default = 'debug', help = 'Server mode')
    result.add_argument ('--pid', '-p', metavar = '<PID file>', type = str, default = None, help = 'PID file')
    return result.parse_args ()

if __name__ == '__main__':
    args = parse_args ()
    server = cherrybase.Server (config = args.config)
    get_conf = cherrypy.config.get

    basename = get_conf ('server.basename', get_conf ('server.socket_host', '127.0.0.1'))
    port = get_conf ('server.socket_port', 8080)
    if port != 80:
        basename = '{}:{}'.format (basename, port)

    # FIXME Повторять в цикле :)
    # FIXME PID-файл в конфиге или аргументах?
    module = __import__ ('app')
    applications = module.get_applications (args.mode, basename)
    if isinstance (applications, cherrybase.Application):
        applications = [applications]

    server.applications += applications
    server.start ()
