# -*- coding: utf-8 -*-

import cherrypy
from cherrypy._cptools import HandlerTool
from urllib import urlencode
from cherrybase.utils import set_cookie, get_cookie, match_list
import hashlib


class BaseUser (object):
    '''
    Базовый класс пользователя системы. Все конкретные реализации должны
    наследовать от него.
    '''
    _session_key = '_cb_auth_data'

    def __init__ (self, guest_login = 'guest', guest_profile = {'name': 'Guest'},
            login_cookie = 'login', hash_cookie = 'hash'):
        self._guest_login = guest_login
        self._guest_profile = guest_profile
        self._login_cookie = login_cookie
        self._hash_cookie = hash_cookie
        self._rights = []
        self._set_guest ()
        self._restore ()

    def _set_guest (self):
        self.login = self._guest_login
        self.hash = None
        self.profile = self._guest_profile
        self._load_rights ()

    def is_guest (self):
        return self.login == self._guest_login

    def _restore (self):
        '''
        Вычитывание данных пользователя из сессии/кук и авторизация
        '''
        data = cherrypy.session.get (self._session_key)
        if data and isinstance (data, dict):
            login = data.get ('login')
            hash = data.get ('hash')
        else:
            login = get_cookie (self._login_cookie)
            hash = get_cookie (self._hash_cookie)
        if not login:
            if not self.is_guest ():
                self._set_guest ()
            return
        self._logon_by_hash (login, hash)

    def _store (self):
        '''
        Сохранение данных текущего пользователя в сессии. Если 
        текущий пользователь - гость, то очистка кук
        '''
        if self.is_guest ():
            if self._session_key in cherrypy.session:
                del cherrypy.session [self._session_key]
            self.set_cookies (0)
            return
        cherrypy.session [self._session_key] = {
            'login': self.login,
            'hash': self.hash
        }

    def create_hash (self, login, password):
        '''
        Создание хеша пароля для пользователя. Может быть перекрыт в наследнике.
        
        :param login: Логин пользователя
        :param password: Пароль пользователя
        '''
        return hashlib.sha256 (password).hexdigest ()

    def _find_user (self, login, hash):
        '''
        Поиск профиля пользователя по логину и хешу пароля. Должен быть перекрыт в наследнике.
        
        :param login: Логин пользователя
        :param hash: Хеш пароля
        :rtype: dict
        :return: Профиль пользователя
        '''
        return {'name': 'Basic User'}

    def _load_rights (self):
        '''
        Загрузка списка URL, к которым пользователь имеет доступ.
        '''
        self._rights = ['.*']

    def set_cookies (self, max_age):
        '''
        Установка кук с данными пользователя.
        
        :param max_age: Срок хранения кук в секундах
        '''
        set_cookie (self._login_cookie, self.login, max_age_seconds = max_age)
        set_cookie (self._hash_cookie, self.hash, max_age_seconds = max_age)

    def logoff (self):
        '''
        Выход пользователя из системы. После выхода пользователь становится гостем,
        а все ранее сохраненные данные о нем (в сессии и куках) удаляются.
        '''
        if self.is_guest ():
            return
        self._set_guest ()
        self._store ()

    def _logon_by_hash (self, login, hash):
        '''
        Вход в систему по имени пользователя/хешу
        
        :param login: Логин пользователя
        :param hash: Хеш пароля
        '''
        if not self.is_guest ():
            self.logoff ()

        profile = self._find_user (login, hash)
        if profile and isinstance (profile, dict):
            self.login = login
            self.hash = hash
            self.profile = profile
            self._load_rights ()
        self._store ()

    def logon_by_password (self, login, password):
        '''
        Вход пользователя в систему. Если пользователь уже авторизован,
        будет автоматически выполнен выход из системы. При неудачной попытке
        входа пользователь останется гостем.
        
        :param login: Логин пользователя
        :param password: Пароль пользователя
        '''
        self._logon_by_hash (login, self.create_hash (login, password))
        cherrypy.session.regenerate ()

    def check_rights (self, url):
        '''
        Проверка наличия прав пользователя на указанный URL
        
        :param url: URL
        
        Returns:
            True, если пользователь имеет право доступа к указанному URL
        '''
        return bool (match_list (self._rights, url))

    def __str__ (self):
        return '<User login: {0}, name: {1}>'.format (self.login, self.profile.get ('name'))


def current_user ():
    '''
    Получение текущего пользователя из request.
    
    :rtype: BaseUser
    :return: Текущий пользователь или None, если авторизация отключена
    '''
    try:
        return cherrypy.request._auth_user
    except AttributeError:
        return None


def _config (param, default = None):
    conf = cherrypy.request.toolmaps ['tools'].get ('auth', {})
    return conf.get (param, default)


class AuthTool (HandlerTool):
    '''
    Инструмент авторизации пользователей.
    '''

    def __init__ (self):
        super (AuthTool, self).__init__ (self.check, name = 'auth')

    def check (self, **kwargs):
        request = cherrypy.serving.request
        path = request.path_info if request.path_info == '/' else request.path_info.rstrip ('/')
        mount_point = _config ('controller_path', '/auth')
        request._auth_user = _config ('user_class', BaseUser) ()
        if path.startswith (mount_point) or request._auth_user.check_rights (path):
            return False

        if request._auth_user.is_guest ():
            raise cherrypy.HTTPRedirect (mount_point + '/logon')

        raise cherrypy.InternalRedirect (mount_point + '/denied', urlencode ({'path': path}))
    check.priority = 9

