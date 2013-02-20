# -*- coding: utf-8 -*-

import cherrypy
import os
import logging

def daemonize (self, user, group, pid_file):
    from cherrypy.process.plugins import PIDFile, Daemonizer, DropPrivileges
    if os.name == 'posix':
        import grp, pwd
        try:
            uid = pwd.getpwnam (user)[2]
            gid = grp.getgrnam (group)[2]
        except KeyError:
            self.log ('Cannot find user "{0}" or group "{1}"'.format (user, group), logging.FATAL)
            raise
    else:
        uid = None
        gid = None

    DropPrivileges (cherrypy.engine, uid = uid, gid = gid).subscribe ()
    PIDFile (cherrypy.engine, pid_file).subscribe ()
    Daemonizer (cherrypy.engine).subscribe ()

def start_engine (block_interval = 0.1):
    if hasattr (cherrypy.engine, 'signal_handler'):
        cherrypy.engine.signal_handler.subscribe ()
    cherrypy.engine.start ()
    cherrypy.engine.block (block_interval)
