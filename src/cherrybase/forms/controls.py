# -*- coding: utf-8 -*-

import cherrypy
from cherrybase.utils import escape
from .base import Element, Control
from .rules import _HasItem, _Captcha
import datetime

class Form (Element):
    '''
    Собственно форма
    '''
    def __init__ (self, name, submit = 'OK', cancel = None, cancel_link = ''):
        '''
        Конструктор
        Args:
            name (str): Уникальный ID формы
            submit (str): Текст на кнопке отправки
            cancel (str): Текст на кнопке отмены, None, если кнопка отмены не нужна
            cancel_link (str): URL, на который будет совершен переход при отмене
        '''
        super (Form, self).__init__ (name, None)
        self.flag = '__form_{0}_submitted__'.format (name)
        self.submit = submit
        self.cancel = cancel
        self.cancel_link = cancel_link

    def is_submitted (self):
        '''
        Проверка на повтор формы
        
        Returns:
            True, если форма строится не в первый раз
        '''
        return cherrypy.request.params.get (self.flag, 'no') == 'yes'


class GroupBox (Element):
    '''
    Группа для элементов
    '''
    def __init__ (self, name, owner = None, caption = 'GroupBox'):
        super (GroupBox, self).__init__ (name, owner)
        self.caption = caption


class Hidden (Control):
    '''
    Невидимое пользователю поле
    '''
    pass


class Edit (Control):
    '''
    Базовое поле ввода
    '''
    def __init__ (self, name, owner = None, caption = '', default = '', is_password = False, max_length = 0, allow_html = False):
        self.caption = caption
        self.is_password = is_password
        self.max_length = max_length
        self.allow_html = allow_html
        super (Edit, self).__init__ (name, owner, default)

    def _load_value (self):
        super (Edit, self)._load_value ()
        self.value = cherrypy.request.params.get (self.name, self.default)
        if self.max_length > 0:
            self.value = self.value [:self.max_length]
        if not self.allow_html and isinstance (self.value, basestring):
            self.value = escape (self.value)


class Memo (Edit):
    '''
    Блок ввода
    '''
    pass


class CheckBox (Control):
    '''
    Флаг
    '''
    def __init__ (self, name, owner = None, caption = '', default = False):
        super (CheckBox, self).__init__ (name, owner, default)
        self.caption = caption

    def _load_value (self):
        self.value = self.name in cherrypy.request.params


class StaticText (Element):
    '''
    Статический текст
    '''
    def __init__ (self, name, owner = None, caption = '', default = ''):
        super (StaticText, self).__init__ (name, owner, default)
        self.caption = caption


class ComboBox (Control):
    '''
    Выпадающий список
    '''
    def __init__ (self, name, owner = None, caption = '', default = None, items = []):
        self.items = items
        super (ComboBox, self).__init__ (name, owner, default)
        self.caption = caption
        _HasItem (self, u'Value is not in list')


class Captcha (Control):
    '''
    Капча
    '''
    def __init__ (self, name, owner = None, caption = '', imageSrc = '/captcha', strict = True, message = None):
        super (Captcha, self).__init__ (name, owner, None)
        self.caption = caption
        self.imageSrc = imageSrc
        self.strict = strict
        self.captchaText = cherrypy.session.get ('captcha')
        _Captcha (self, message if message else u'Captcha is not valid')


class CheckList (Control):
    '''
    Список для мультивыбора
    '''
    def __init__ (self, name, owner = None, caption = '', default = [], listItems = []):
        self.listItems = listItems
        super (CheckList, self).__init__ (name, owner, default)
        self.caption = caption

    def _load_value (self):
        self.value = [item for item in self.listItems if item [0] in cherrypy.request.params]


class DatePicker (Control):
    '''
    Поле ввода даты
    '''
    def __init__ (self, name, owner = None, caption = '', default = None, python_format = '%d.%m.%Y',
            jquery_format = 'dd.mm.yy'):
        self.python_format = python_format
        self.jquery_format = jquery_format
        super (DatePicker, self).__init__ (name, owner, default)
        self.caption = caption

    def _load_value (self):
        self.display_value = cherrypy.request.params.get (self.name)
        if self.display_value is not None:
            self.value = datetime.datetime.strptime (self.display_value, self.python_format)
        else:
            self.value = self.default
            self.display_value = self.value.strftime (self.python_format)


class MaskedEdit (Control):
    '''
    Максированное поле ввода
    '''
    def __init__ (self, name, owner = None, caption = '', default = '', format = ''):
        if not format:
            raise ValueError ('Format is not defined')
        super (MaskedEdit, self).__init__ (name, owner, default)
        self.format = format
        self.caption = caption

