# -*- coding: utf-8 -*-

import time
from pkg_resources import parse_version
from . import BaseError, client
import cherrypy


class LookupError (BaseError):
    pass


class NamingEntry (object):

    def __init__ (self, code, security_manager, raw_entry):
        self.code = code
        self.security_manager = security_manager
        self.url, self.version, self.fingerprint = raw_entry
        self.timestamp = time.time ()
        self.parsed_version = parse_version (self.version or '0.0.0')


    def valid (self, cache_time):
        return time.time () - self.timestamp < cache_time

    def suitable (self, code, parsed_version):
        return self.code == code \
            and self.parsed_version >= parsed_version \
            and self.security_manager.public_key_exists (self.fingerprint)

    def dump (self):
        return (self.url, self.version, self.fingerprint)


class NamingProxy (object):

    def __init__ (self, service):
        self.own_url = service.url ()
        self.cache = []
        self.cache_time = service.service_config ('naming.cache_time', 600)
        self.security_manager = service.security_manager
        self.routing_entry = NamingEntry (
            'routing',
            self.security_manager,
            [
                service.service_config ('naming.routing_url', strict = True),
                None,
                service.service_config ('naming.routing_fingerprint', strict = True),
            ]
        )
        self.router = client.Server (
            uri = self.routing_entry.url,
            key = self.routing_entry.fingerprint,
            gpg_homedir = service.service_config ('security.homedir', strict = True),
            gpg_key = service.service_config ('security.key', strict = True),
            gpg_password = service.service_config ('security.password', strict = True)
        )
        if service.service_config ('naming.autoregister', False):
            engine = cherrypy.engine
            engine.starter_stopper.on_start.append (self.register)
            engine.starter_stopper.on_stop.append (self.unregister)

            interval = service.service_config ('naming.autoregister_interval', 0)
            if interval > 0:
                engine.task_manager.add (
                    '__{}_naming_autoregister__'.format (service.code),
                    self.register,
                    interval
                )

    def cleanup (self):
        self.cache = [entry for entry in self.cache if entry.valid (self.cache_time)]

    def find (self, code, version):
        return [entry for entry in self.cache if entry.suitable (code, version)]

    def lookup (self, code, version = None):
        if code == 'routing':
            return self.routing_entry.dump ()

        version = parse_version (version or '0.0.0')

        self.cleanup ()

        result = self.find (code, version)
        if not result:
            self.cache.extend (
                [NamingEntry (code, self.security_manager, raw) for raw in self.router.routing.naming.lookup (code, version)]
            )
        result = self.find (code, version)
        if not result:
            raise LookupError ('Service "{}, {}" not found'.format (code, version), -4001)
        return result [0].dump ()

    def register (self):
        self.router.routing.naming.register (self.own_url)

    def unregister (self):
        self.router.routing.naming.unregister (self.owm_url)
