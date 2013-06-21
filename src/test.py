#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xmlrpclib
from rco import gpgxmlrpc

server = xmlrpclib.Server (
    'http://rpc.cherrybase:8080/',
    allow_none = True,
    transport = gpgxmlrpc.GpgTransport (
        gpg_homedir = '/home/rus/work/home/cherryBase/src/rpciface/keyring',
        gpg_key = '55A6F35DC05A3728FB45AA0277EA551D7EAC9ABD',
        gpg_password = '123321',
        gpg_server_key = '55A6F35DC05A3728FB45AA0277EA551D7EAC9ABD',
    )
)

print server.system.listMethods ()

print server.control.keyring.keys ()

print server.test.hello (u'Миииир!')
