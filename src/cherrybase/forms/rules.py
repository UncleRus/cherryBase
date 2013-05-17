# -*- coding: utf-8 -*-

from .base import Rule
from cherrybase.utils import to_int, to_type
import re

email_pattern = r'^[a-z0-9_.-]{1,40}@(([a-z0-9-]+\.)+([a-z]{2,})|[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})$'
phone_pattern = r'^((\+\d{1,3})|8)[\s\-]*(\(\d{3}\)|\d{3})[\s\-]*(\d{3}[\s\-]*\d{2}[\s\-]*\d{2})|(\d{2}[\s\-]*\d{2}[\s\-]*\d{3})|(\d{2}[\s\-]*\d{3}[\s\-]*\d{2})$'
numeric_pattern = r'^(\-|\+)?\d+(\.\d+)?$'
int_pattern = r'^(\-|\+)?\d+$'

class Required (Rule):
    '''
    Признак необходимости ввода значения
    '''
    def __init__ (self, control, message = u'Value required'):
        super (Required, self).__init__ (control, message)
        control.is_required = True

    def __call__ (self):
        return to_type (bool, self.control.value, False)


class Regexp (Rule):
    '''
    Проверка значения на соответствие регулярному выражению
    '''
    def __init__ (self, control, pattern = email_pattern, flags = re.UNICODE + re.IGNORECASE, message = u'Invalid value'):
        super (Regexp, self).__init__ (control, message)
        if pattern == int_pattern:
            self.control.converters.append (to_int)
        elif pattern == numeric_pattern:
            self.control.converters.append (lambda x: to_type (float, x, 0.0))
        self._regexp = re.compile (pattern, flags)

    def __call__ (self):
        return unicode (self.control.value) == '' or self._regexp.search (unicode (self.control.value))


class Equal (Rule):
    '''
    Проверка идентичности значений
    '''
    def __init__ (self, control, original_control, message = u'Values must be equal'):
        super (Equal, self).__init__ (control, message)
        self.original_control = original_control

    def __call__ (self):
        return self.control.value == self.original_control.value


class Wrapper (Rule):
    '''
    Универсальная обертка для своих собственных проверок
    '''
    def __init__ (self, control, callable_, message = u'Invalid value'):
        super (Wrapper, self).__init__ (control, message)
        self._callable = callable_

    def __call__ (self):
        return self._callable (self.control.value)


class _HasItem (Rule):
    '''
    Внутреннее правило для списков
    '''
    def __call__ (self):
        return self.control.value in [item [0] for item in self.control.items]


class _Captcha (Rule):
    '''
    Внутреннее правило для капчи
    '''
    def __call__ (self):
        _secure_text = self.control.captcha_text
        if not self.control.strict:
            _secure_text = _secure_text.lower ()
            value = self.control.value.lower ()
        return _secure_text == value
