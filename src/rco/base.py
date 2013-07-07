# -*- coding: utf-8 -*-

from cherrybase import rpc, orm
from cherrybase.utils import to_int
import gnupg
import cherrypy
import cherrybase
import pkg_resources
from cherrypy import _cpconfig
from . import stdlib
from . import _secmodel as mdl


class SecurityError (Exception):
    pass


class Namespace (object):
    pass


class SecurityManager (object):

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

    use_orm = None

    def __init__ (self, service, gpg_homedir, gpg_key, gpg_password):
        self.service = service
        self.gpg = gnupg.GPG (gnupghome = gpg_homedir)
        self.key = gpg_key
        self.password = gpg_password
        self.ifaces = {}

        self.own_key = service.raw_conf_val ('tools.gpg_in.key')
        if not self.own_key:
            raise KeyError ('tools.gpg_in.key is not defined for root interface')
        self._update_keys ()

        # Готовим хранилище
        self.pool_name = self.pool_name_format.format (service.code)

        from cherrybase import db
        import cherrybase.db.drivers.sqlite as sqlite
        import cherrybase.orm.drivers.alchemy as alchemy

        min_conn = service.raw_conf_val ('security_manager.db_min_connections', 5)
        max_conn = service.raw_conf_val ('security_manager.db_max_connections', 30)

        # Создаем пул подключений к специальной БД
        db.catalog [self.pool_name] = sqlite.Sqlite (
            min_connections = min_conn,
            max_connections = max_conn,
            database = service.raw_conf_val ('security_manager.db_filename', ':memory:')
        )
        # Обертываем подключения в ORM
        orm.catalog [self.pool_name] = alchemy.SqlAlchemy (
            db_pool_name = self.pool_name,
            engine_url = 'sqlite://',
            pool_size = min_conn,
            pool_max_overflow = max_conn
        )
        # Достаем сессию алхимии из пула и создаем структуру БД
        session = orm.catalog.get (self.pool_name)
        mdl.Base.metadata.create_all (session.bind)
        # Синхронизируем БД и содержимое ключницы (удаляем из БД упоминания о несуществующих ключах)
        session.query (mdl.Rights).filter (~mdl.Rights.fingerprint.in_ (self.keys.keys ())).delete (synchronize_session = False)
        session.commit ()

    def _update_keys (self):
        self.keys = {}
        for key in self.gpg.list_keys ():
            if not key ['fingerprint'].endswith (self.own_key):
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
            if k.endswith (self.own_key) or self.own_key.endswith (k):
                raise SecurityError ('Cannot manipulate my own key: {}'.format (self.own_key), -2000)
        return keys

    def connect_interface (self, iface):
        if not isinstance (iface, CryptoInterface):
            raise ValueError ('Interface is not instance of rco.CryptoInterface')
        self.ifaces [iface._mount_point] = iface.system.methods.keys ()

    def grant (self, methods, keys):
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
        result = self.gpg.delete_keys (keys)
        if getattr (result, 'ok', False) or result:
            session = orm.catalog.get (self.pool_name)
            session.query (mdl.Rights).filter (mdl.Rights.fingerprint.in_ (keys)).delete (synchronize_session = False)
            session.commit ()
            orm.catalog.put (self.pool_name, session)
            self._update_keys ()
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

    def can_execute (self, iface, client_key, method):
        request = cherrypy.request
        if request.app.find_config ('/', 'full_access'):
            return True
        # FIXME: Сделать нормальную проверку
        return True


class CryptoInterface (rpc.Controller):
    '''
    Базовый класс для всех шифрованных RPC-интерфейсов
    '''

    _cp_config = {
        'tools.xmlrpc.on': True,
        'tools.xmlrpc.allow_none': True,
        'tools.gpg_in.on': True,
        'tools.gpg_in.force': True,
        'tools.gpg_in.target_ct': 'text/xml',
        'tools.gpg_out.on': True,
    }

    def __init__ (self, security_manager, mount_point = '/'):
        self._mount_point = mount_point
        self._security = security_manager
        if mount_point == '/':
            self.control = Namespace ()
            self.control.keyring = stdlib.Keyring (self._security)
            self.control.access = stdlib.Access (self._security)
            self.callbacks = Namespace ()
        super (CryptoInterface, self).__init__ ()
        self._security.connect_interface (self)

    def _call_method (self, method, name, args, vpath, parameters):
        if not self._security.can_execute (self, cherrypy.request._gpg_client_key, name):
            raise SecurityError ('Access denied', -1000)
        return super (CryptoInterface, self)._call_method (method, name, args, vpath, parameters)


class MetaInterface (rpc.Controller):

    _cp_config = {
        'tools.xmlrpc.on': True,
        'tools.xmlrpc.allow_none': True,
        'tools.gpg_in.on': False,
        'tools.gpg_out.on': False,
    }

    def __init__ (self, security_manager, code = None, version = None, title = None):
        self.meta = stdlib.Meta (security_manager, code, version, title)
        super (MetaInterface, self).__init__ ()


class Service (cherrybase.Application):

    def __init__ (self, package, basename, mode, vhosts, root = CryptoInterface, config = None):
        self.package = package

        # Готовим конфигурацию
        self.raw_config = {}
        _cpconfig.merge (
            self.raw_config,
            config or pkg_resources.resource_filename (package, '__config__/{}.conf'.format (mode))
        )

        self.code = self.raw_conf_val ('service.code', package)

        gpg_homedir = self.raw_conf_val ('tools.gpg_in.homedir')
        gpg_key = self.raw_conf_val ('tools.gpg_in.key')
        gpg_password = self.raw_conf_val ('tools.gpg_in.password')

        # Создаем менеджер безопасности
        self.security_manager = SecurityManager (self, gpg_homedir, gpg_key, gpg_password)

        # Создаем постоянный клиент для роутинга
        routing_data = self.raw_conf_val ('routing_service')
        if routing_data:
            import client
            self.routing = client.Server (
                routing_data [0],
                routing_data [1],
                gpg_homedir,
                gpg_key,
                gpg_password
            )

        _vhosts = [vhost + basename if vhost.endswith ('.') else vhost for vhost in vhosts]
        # Родительский конструктор
        super (Service, self).__init__ (
            name = self.code,
            vhosts = _vhosts,
            config = self.raw_config,
            routes = (
                ('/', root (self.security_manager), None),
                (
                    '/meta',
                    MetaInterface (
                        self.security_manager,
                        code = self.code,
                        version = self.raw_conf_val ('service.version', '1.0.0'),
                        title = self.raw_conf_val ('service.title', self.code)
                    ),
                    None
                ),
            )
        )
        self.main_name = _vhosts [0] + '/'
        self.app.service = self

    def raw_conf_val (self, entry, default = None, path = '/'):
        return self.raw_config.get (path, {}).get (entry, default)

    def url (self, method_name):
        return 'http://{}:{}'.format (self.main_name, method_name)

