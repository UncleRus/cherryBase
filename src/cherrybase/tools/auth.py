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
            login_cookie = 'login', hash_cookie = 'hash'
        ):
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
        Создание хеша пароля для пользователя. Должен быть перекрыт в наследнике.
        
        Args:
            login (unicode): Логин пользователя
            password (unicode): Пароль пользователя
        '''
        return hashlib.sha1 (password).hexdigest ()

    def _find_user (self, login, hash):
        '''
        Поиск профиля пользователя по логину и хешу пароля. Должен быть перекрыт в наследнике.
        
        Args:
            login (unicode): Логин пользователя
            hash (unicode): Хеш пароля
        
        Returns:
            (dict) Профиль пользователя
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
        
        Args:
            max_age (int): Срок хранения кук в секундах
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
        
        Args:
            login (unicode): Логин пользователя
            hash (unicode): Хеш пароля
        '''
        if not self.is_guest ():
            self.logoff ()

        profile = self._find_user (login, hash)
        if profile and isinstance (profile, dict):
            self.login = unicode (login)
            self.hash = unicode (hash)
            self.profile = profile
            self._load_rights ()
        self._store ()

    def logon_by_password (self, login, password):
        '''
        Вход пользователя в систему. Если пользователь уже авторизован,
        будет автоматически выполнен выход из системы. При неудачной попытке
        входа пользователь останется гостем.
        
        Args:
            login (str): логин пользователя
            password (str): пароль пользователя
        '''
        self._logon_by_hash (login, self.create_hash (login, password))
        cherrypy.session.regenerate ()

    def check_rights (self, url):
        '''
        Проверка наличия прав пользователя на указанный URL
        
        Args:
            url (str): URL
        
        Returns:
            True, если пользователь имеет право доступа к указанному URL
        '''
        return bool (match_list (self._rights, url))

    def __str__ (self):
        return '<User login: {0}, name: {1}>'.format (self.login, self.profile.get ('name'))


def current_user ():
    '''
    Получение текущего пользователя из request.
    
    Returns:
        :class:BaseUser текущий пользователь или None, если авторизация отключена
    '''
    try:
        return cherrypy.request._auth_user
    except AttributeError:
        return None


def _config (param, default = None):
    conf = cherrypy.request.toolmaps ['tools'].get ('auth', {})
    return conf.get (param, default)


from cherrybase.forms import controls, rules

class AuthController (object):
    '''
    Контроллер авторизации пользователей
    '''
    @cherrypy.expose
    @cherrypy.tools.jinja ()
    def logon (self, **kwargs):
        user = current_user ()
        if not user:
            raise cherrypy.HTTPError (500, 'Current user is not defined')

        after_logon = _config ('after_logon', '/')
        if not user.is_guest ():
            raise cherrypy.HTTPRedirect (after_logon)

        form = controls.Form ('logon_form', submit = 'Login')
        group_box = controls.GroupBox ('group_box', form, caption = 'Logon')
        e_login = controls.Edit ('login', group_box, caption = 'Login')
        rules.Required (e_login, 'Enter your login')
        e_password = controls.Edit ('password', group_box, caption = 'Password', is_password = True)
        e_remember = controls.CheckBox ('remember', group_box, caption = 'Remember me')

        if form.is_submitted () and form.check ():
            user.logon_by_password (e_login.value, e_password.value)
            if e_remember.value:
                user.set_cookies (_config ('cookie_age', 259200))

        if user.is_guest ():
            return {
                'form': form,
                'message': 'Invalid login or password' if form.is_submitted () else '',
                '__template__': _config ('controller_logon_template', 'auth/logon.tpl')
            }
        raise cherrypy.HTTPRedirect (after_logon)

    @cherrypy.expose
    def logoff (self, **kwargs):
        user = current_user ()
        if user:
            user.logoff ()
        raise cherrypy.HTTPRedirect (_config ('after_logoff', '/'))

    @cherrypy.expose
    @cherrypy.tools.jinja ()
    def denied (self, path = None):
        return {
            'path': path,
            '__template__': _config ('controller_logon_template', 'auth/denied.tpl')
        }


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

        if cherrypy.request.user.is_guest ():
            raise cherrypy.HTTPRedirect (mount_point + '/logon')

        raise cherrypy.InternalRedirect (mount_point + '/denied', urlencode ({'path': path}))
    check.priority = 9

