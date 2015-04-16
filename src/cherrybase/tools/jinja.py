# -*- coding: utf-8 -*-

import cherrypy
from cherrypy._cptools import Tool
import jinja2
import sys


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

        response ['__template__'] = response.get ('__template__', getattr (cherrypy.serving.response, '__template__', self.template))
        return self.env.get_template (response ['__template__']).render (response)


if sys.version_info [0] >= 3:
    def _finalize (x):
        return '' if x is None else x
else:
    def _finalize (x):
        if x is None:
            return ''
        if type (x) == str:
            return unicode (x, 'utf-8')
        return x


class JinjaTool (Tool):
    '''
    Инструмент шаблонизации. Доступен под именем `cherrypy.tools.jinja`.
    Контроллеры, использующие инструмент, должны возвращать dict. 
    Результат контроллера с индексом `'__globals__'` передается в шаблон
    как глобальное окружение.
    Порядок поиска имени шаблона:
        
        - индекс результата контроллера `'__template__'`
        - атрибут `cherrypy.response.__template__`
        - параметр `'tools.jinja.template'` (параметр template декоратора)
        - если ни один из предыдущих способов не определил имя шаблона, оно 
            по умолчанию равно `'{url}.tpl'`, например при URL '/some/web/page/'
            имя шаблона будет равно 'some/web/page.tpl'
    
     В шаблон его имя (прочитанное или установленное по умолчанию)
        передается в переменной `__template__`
    
    Параметры инструмента:
        
        :template: Имя шаблона, при отсутствии имя шаблона будет построено автоматически.
        :loader: Объект класса-загрузчика шаблонов, например jinja2.FileSystemLoader.
        :newline_sequence: Последовательность символов, завершающая строку. Должна принимать
            одно из трех допустимых значений: `'\r'`, `'\n'` или `'\r\n'`.
        
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
            finalize = _finalize
        )
        self.default_loader = jinja2.FileSystemLoader ('')

    def run (self, template = None, loader = None, newline_sequence = '\n', gettext_translations = None):
        request = cherrypy.serving.request
        if not template:
            path = unicode (request.path_info).strip ('/')
            template = '{0}.tpl'.format (path) if path else 'index.tpl'

        self.env.loader = loader or self.default_loader
        self.env.newline_sequence = newline_sequence
        self.env.uninstall_gettext_translations (None)
        if gettext_translations:
            self.env.install_gettext_translations (gettext_translations, True)
        else:
            self.env.install_null_translations (True)

        request.jinja_env = self.env
        request.handler = JinjaHandler (cherrypy.request.handler, self.env, template)
