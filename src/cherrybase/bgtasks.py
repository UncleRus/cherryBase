# -*- coding: utf-8 -*-

from cherrypy.process.plugins import SimplePlugin
import threading
import Queue
import logging
from threading import Timer

class TasksQueue (SimplePlugin):

    def __init__ (self, bus, queue_size = 100, timeout = 2):
        super (TasksQueue, self).__init__ (bus)
        self.queue = Queue.Queue (queue_size)
        self.running = False
        self.timeout = timeout
        self.thread = None

    def start (self):
        self.running = True
        if not self.thread:
            self.thread = threading.Thread (target = self.run)
            self.thread.start ()
        self.bus.log ('Started TasksQueue')

    def stop (self):
        self.bus.log ('Stopping TasksQueue...')
        self.running = 'stopping'
        if self.thread:
            self.thread.join ()
            self.thread = None
        self.running = False
        self.bus.log ('Stopped TasksQueue')

    def run (self):
        while self.running:
            try:
                func, args, kwargs = self.queue.get (block = True, timeout = self.timeout)
                func (*args, **kwargs)
            except Queue.Empty:
                if self.running == 'stopping':
                    return
                continue
            except:
                self.bus.log ('Error in task {}'.format (func), level = logging.ERROR, traceback = True)

    def put (self, task, *args, **kwargs):
        self.queue.put ((task, args, kwargs))


class Cron (SimplePlugin):

    def __init__ (self, bus):
        SimplePlugin.__init__ (self, bus)
        self._tasks = {}
        self._timers = {}
        self.started = False

    def start (self):
        self.started = True
        for timer in [timer for timer in self._timers.values () if timer.finished]:
            timer.start ()
        self.bus.log ('Started Cron')

    def stop (self):
        self.clear ()
        self.bus.log ('Stopped Cron')
        self.started = False

    def _run_task (self, code, interval, *args, **kwargs):
        if code not in self._tasks:
            if code in self._timers:
                del self._timers [code]
            return
        self._timers [code] = Timer (interval, self._run_task, [code, interval] + list (args), kwargs)
        self._timers [code].start ()
        self._tasks [code] (*args, **kwargs)

    def add (self, code, task, interval, *args, **kwargs):
        self._tasks [code] = task
        self._timers [code] = Timer (interval, self._run_task, [code, interval] + list (args), kwargs)
        if self.started:
            self._timers [code].start ()

    def remove (self, code):
        self._timers [code].cancel ()
        del self._tasks [code]
        del self._timers [code]

    def clear (self):
        for timer in self._timers.values ():
            timer.cancel ()
        self._tasks.clear ()
        self._timers.clear ()
