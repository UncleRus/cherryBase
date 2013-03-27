# -*- coding: utf-8 -*-

import cherrypy
from cherrypy._cptools import Tool
import jinja2

class JinjaHandler (cherrypy.dispatch.LateParamPageHandler):
    '''
    Рендерер шаблонов
    '''
    def __init__ (self, next_handler, env, template):
        self.next_handler = next_handler
        self.template = template
        self.env = env

    def __call__ (self):
        response = self.next_handler ()
        if not isinstance (response, dict):
            return response

        tpl_globals = response.get ('__globals__', {})
        if not isinstance (tpl_globals, dict):
            tpl_globals = {}
        tpl_globals.update ({'cherrypy': cherrypy})
        self.env.globals.update (tpl_globals)

        response ['__template__'] = response.get ('__template__', getattr (cherrypy.serving.request, '_jinja_template', self.template))
        return self.env.get_template (response ['__template__']).render (response)


class JinjaTool (Tool):
    '''
    Инструмент шаблонизации. Контроллеры, использующие инструмент,
    должны возвращать dict. 
    Результат контроллера с индексом '__globals__' передается в шаблон
    как глобальное окружение.
    Результат контроллера может содержать строку с индексом '__template__',
    в которой перекрывается имя шаблона.
    Также имя шаблона может быть перекрыто путем установки атрибута
    cherrypy.request._jinja_template
    '''
    def __init__ (self):
        super (JinjaTool, self).__init__ (
            point = 'on_start_resource',
            callable = self.run,
            name = 'jinja',
            priority = 70
        )
        self.env = jinja2.Environment (
            extensions = ['jinja2.ext.i18n'],
            finalize = lambda x: '' if x is None else x
        )

    def run (self, template = None, loader = None, **kwargs):
        request = cherrypy.serving.request
        if not template:
            path = unicode (request.path_info).strip ('/')
            template = '{0}.tpl'.format (path) if path else 'index.tpl'
        self.env.loader = loader if loader else jinja2.FileSystemLoader ('')
        request.jinja_env = self.env
        request.handler = JinjaHandler (cherrypy.request.handler, self.env, template)
