# -*- coding: utf-8 -*-

import wtforms as wtf
import cherrypy
from . import current_user
from .base import _config


class AuthController (object):

    class Form (wtf.Form):

        login = wtf.StringField (u'Login', maxlength = 50, validators = [wtf.validators.required ()])
        password = wtf.PasswordField (u'Password', maxlength = 50)
        remember = wtf.BooleanField (u'Remember me')

    @cherrypy.expose
    @cherrypy.tools.jinja ()
    def index (self, **kwargs):
        user = current_user ()
        if not user:
            raise cherrypy.HTTPError (500, 'Current user is not defined. Maybe cherrypy.tools.auth_tool is not enabled')
        after_logon = kwargs.get ('after', _config ('after_logon', '/'))
        if not user.is_guest ():
            raise cherrypy.HTTPRedirect (after_logon)

        form = self.Form (kwargs if cherrypy.request.method == 'POST' else None)
        if kwargs and form.validate ():
            user.logon_by_password (form.login.data, form.password.data)

        if user.is_guest ():
            user.set_cookies (0)
            return {
                'form': form,
                'message': 'Invalid login or password' if kwargs else None,
                '__template__': _config ('controller_logon_template', '__views__/auth/logon.tpl')
            }

        if form.remember.data:
            user.set_cookies (_config ('cookie_age', 259200))

        raise cherrypy.HTTPRedirect (after_logon)

    @cherrypy.expose
    def logoff (self, **kwargs):
        user = current_user ()
        if user:
            user.logoff ()
            user.set_cookies (0)
        raise cherrypy.HTTPRedirect (kwargs.get ('after', _config ('after_logoff', '/')))

    @cherrypy.expose
    @cherrypy.tools.jinja ()
    def denied (self, path = None):
        return {
            'path': path,
            '__template__': _config ('controller_denied_template', '__views__/auth/denied.tpl')
        }

