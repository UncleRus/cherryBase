#!/usr/bin/env python
# -*- coding: utf-8 -*-

from xmlrpclib import ServerProxy
c = ServerProxy ('http://127.0.0.1:8080/rpc')

print c.testlib.add (10, 2)
methods = c.system.listMethods ()
print methods
for method in methods:
	print c.system.methodHelp (method)


#print c.hello ('World');

#import types
#
#class UniversalDecorator (object):
#
#    def __init__ (self, *args, **kwargs):
#        print 'init', args, kwargs
#        self.obj = None
#        if len (args) > 0 and isinstance (args [0], (types.FunctionType, types.MethodType)):
#            self._func = args [0]
#            _args = []
#            _kwargs = {}
#        else:
#            self._func = None
#            _args = args
#            _kwargs = kwargs
#        self.set_args (*_args, **_kwargs)
#
#    def __get__ (self, obj, type = None):
#        print '__get__', obj, type
#        self.obj = obj
#        return self
#
#    def set_args (self, *args, **kwargs):
#        raise NotImplementedError ('set_args() must be implemented')
#
#    def wrapped (self, *args, **kwargs):
#        raise NotImplementedError ('wrapped() must be implemented')
#
#    def __call__ (self, *args, **kwargs):
#        print '__call__', args, kwargs, self.obj
#        if self._func:
#            if self.obj:
#                args = list (args)
#                args.insert (0, self.obj)
#            print '__without__', args, kwargs, self.obj
#            return self.wrapped (*args, **kwargs)
#        self._func = args [0]
#        return self.wrapped
#
#
#class TestDecorator (UniversalDecorator):
#
#    def set_args (self, autocommit = True, pos = 1):
#        self.autocommit = autocommit
#        self.pos = pos
#
#    def wrapped (self, *args, **kwargs):
#        print '>>> before func', args, kwargs, self.autocommit, self.pos
#        if self.obj:
#            args = list (args)
#            args.insert (0, self.obj)
#        result = self._func (*args, **kwargs)
#        print '<<< after func', result
#        return result
#
#
##@TestDecorator
##def func1 (param1, param2):
##    print 'func1', param1, param2
##
##func1 ('param1', 'param2')
##
##@TestDecorator()
##def func2 (param1, param2):
##    print 'func2', param1, param2
##
##func2 ('param1', 'param2')
#
#class TestClass (object):
#
#    @TestDecorator (autocommit = False)
#    def method (self, param1, param2):
#        print 'method', param1, param2, self
#
#
#obj = TestClass ()
#obj.method ('method_param1', 'method_param2')

