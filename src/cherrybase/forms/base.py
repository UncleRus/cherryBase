# -*- coding: utf-8 -*-

import cherrypy

class Element (object):
    '''
    Базовый класс элемента формы
    '''
    def __init__ (self, name, owner = None):
        self.name = name
        self.children = set ()
        self.owner = owner
        self.valid = True

    @property
    def owner (self):
        return self._owner

    @owner.setter
    def owner (self, value):
        if getattr (self, '_owner', None):
            self._owner.children.discard (self)
        self._owner = value
        if self._owner:
            self._owner.children.add (self)

    def check (self):
        self.valid = True
        for element in self.children:
            self.valid = element.check () and self.valid
        return self.valid


class Control (Element):
    '''
    Базовый класс элемента ввода на форме
    '''
    def __init__ (self, name, owner = None, default = None):
        super (Control, self).__init__ (name, owner)
        self.default = default
        self.rules = []
        self.errors = []
        self._load_value ()

    def _load_value (self):
        self.value = cherrypy.request.params.get (self.name, self.default)

    def check (self):
        super (Control, self).check ()
        for rule in self.rules:
            res = rule ()
            if not res:
                self.errors.append (rule.message)
            self.valid = res and self.valid
        return self.valid


class Rule (object):

    def __init__ (self, control, message):
        self.message = message
        self.control = control

    def __call__ (self):
        return True
