# -*- coding: utf-8 -*-

import sqlalchemy.schema as sas
import sqlalchemy.types as sat
from sqlalchemy.ext.declarative import declarative_base
import gnupg
from cherrybase import orm
from cherrybase.utils import to_int
from . import BaseError
import cherrypy


BaseMdl = declarative_base ()


class _RightsMdl (BaseMdl):

    __tablename__ = 'rights'

    fingerprint = sas.Column (sat.String (50), primary_key = True, nullable = False)
    method = sas.Column (sat.Text, primary_key = True, nullable = False)

    def __init__ (self, fingerprint, method):
        self.fingerprint = fingerprint
        self.method = method


class SecurityError (BaseError):
    pass


class Manager (object):

    _algos = {
        '0': None,
        '1': 'RSA',
        '2': 'RSA_E',
        '3': 'RSA_S',
        '16': 'ELGAMAL_E',
        '17': 'DSA',
        '16': 'ELGAMAL'
    }

    pool_name_format = '__{}__security_manager__'

    def __init__ (self, service, gpg_homedir, gpg_key, gpg_password):
        self.service = service
        self.gpg = gnupg.GPG (gnupghome = gpg_homedir)
        self.homedir = gpg_homedir
        self.key = gpg_key
        self.password = gpg_password
        self.ifaces = {}
        self._update_keys ()

        # Готовим хранилище
        self.pool_name = self.pool_name_format.format (service.code)

        from cherrybase import db
        import cherrybase.db.drivers.sqlite as sqlite
        import cherrybase.orm.drivers.alchemy as alchemy

        min_conn = service.service_config ('security_manager.db_min_connections', 5)
        max_conn = service.service_config ('security_manager.db_max_connections', 30)

        # Создаем пул подключений к специальной БД
        db.catalog [self.pool_name] = sqlite.Sqlite (
            min_connections = min_conn,
            max_connections = max_conn,
            database = service.service_config ('security_manager.db_filename', ':memory:')
        )
        # Обертываем подключения в ORM
        alchemy.auto_wrapper (self.pool_name)
        # Достаем сессию алхимии из пула и создаем структуру БД
        session = orm.catalog.get (self.pool_name)
        BaseMdl.metadata.create_all (session.bind)
        # Синхронизируем БД и содержимое ключницы (удаляем из БД упоминания о несуществующих ключах)
        session.query (_RightsMdl).filter (~_RightsMdl.fingerprint.in_ (self.keys.keys ())).delete (synchronize_session = False)
        session.commit ()

    def _update_keys (self):
        self.keys = {}
        for key in self.gpg.list_keys ():
            if not key ['fingerprint'].endswith (self.key):
                self.keys [key ['fingerprint']] = {
                    'info': key ['uids'][0] if len (key ['uids']) > 0 else None,
                    'length': to_int (key ['length']),
                    'algo': self._algos.get (key ['algo'], key ['algo'])
                }

    def _prepare_keys (self, keys):
        if isinstance (keys, basestring):
            keys = [keys]
        for k in keys:
            if len (k) < 8:
                raise SecurityError ('Key id too short: {}'.format (k))
            if k.endswith (self.key) or self.key.endswith (k):
                raise SecurityError ('Cannot manipulate my own key: {}'.format (self.key), -2000)
        return keys

    def _prepare_methods (self, methods):
        return [methods] if isinstance (methods, basestring) else methods

    def connect_interface (self, iface):
        from .base import CryptoInterface
        if not isinstance (iface, CryptoInterface):
            raise ValueError ('Interface is not instance of rco.CryptoInterface')
        self.ifaces [iface._mount_point] = iface.system.methods.keys ()

    def grant (self, methods, keys):
        '''
        session = orm.catalog.get (self.pool_name)
        keys = self._prepare_keys (keys)
        for method in self._prepare_methods (methods):
            for key in keys:
                if session.query (_RightsMdl).filter (
                        sas.and_ (
                            _RightsMdl.fingerprint == key,
                            sas.or_ (
                                sas.and_ (~_RightsMdl.method.endswith ('.'), _RightsMdl.method == method),
                                sas.and_ (_RightsMdl.method.endswith ('.'), sas.literal (method).startswith (_RightsMdl.method))
                            )
                        )
                    ).count () == 0:
                    session.add (_RightsMdl (key, method))
        '''
        # FIXME: Убрать заглушку
        pass

    def revoke (self, methods, keys):
        # FIXME: Убрать заглушку
        pass

    def rights (self, methods = None, keys = None):
        # FIXME: Убрать заглушку
        return {}

    def delete_keys (self, keys):
        keys = self._prepare_keys (keys)
        if not keys:
            return
        self._check_result (self.gpg.delete_keys (keys))
        session = orm.catalog.get (self.pool_name)
        session.query (_RightsMdl).filter (_RightsMdl.fingerprint.in_ (keys)).delete (synchronize_session = False)
        session.commit ()
        orm.catalog.put (self.pool_name, session)
        self._update_keys ()
        return

    def _check_result (self, result):
        if getattr (result, 'ok', False) or result:
            return
        raise SecurityError (
            '\n'.join ([line for line in getattr (result, 'stderr', 'gpg: {}'.format (getattr (result, 'status', 'Unknown error'))).splitlines () \
                if line.startswith ('gpg: ')]),
            - 2100
        )

    def import_keys (self, armored):
        result = self.gpg.import_keys (armored)
        self._update_keys ()
        return {res ['fingerprint']: (bool (to_int (res ['ok'])), res ['text'].strip ('\n')) for res in result.results}

    def export_keys (self, keys):
        return self.gpg.export_keys (self._prepare_keys (keys))

    def can_execute (self, iface, method):
        request = cherrypy.request
        if request.app.find_config ('/', 'full_access'):
            return True
        # FIXME: Сделать нормальную проверку
        return True

    def public_key_exists (self, key):
        if len (key) < 8:
            return False
        key = key.upper ()
        for item in self.gpg.list_keys ():
            if item.get ('fingerprint', '').upper ().endswith (key):
                return True
        return False

    def encrypt (self, data, recipient_key):
        result = self.gpg.encrypt (
            data,
            recipient_key,
            sign = self.key,
            passphrase = self.password,
            always_trust = True
        );
        self._check_result (result);
        return unicode (result)

    def decrypt (self, encoded, correspondent_key):
        result = self.gpg.decrypt_verify (
            encoded,
            correspondent_key,
            passphrase = self.password,
            always_trust = True
        )
        self._check_result (result)
        return unicode (result)

