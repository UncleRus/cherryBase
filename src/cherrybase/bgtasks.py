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
        self.bus.publish ('acquire_thread')
        while self.running:
            try:
                func, args, kwargs = self.queue.get (block = True, timeout = self.timeout)
                func (*args, **kwargs)
            except Queue.Empty:
                if self.running == 'stopping':
                    self.bus.publish ('release_thread')
                    return
                continue
            except:
                self.bus.log ('Error in task {}'.format (func), level = logging.ERROR, traceback = True)

    def put (self, task, *args, **kwargs):
        self.queue.put ((task, args, kwargs))


class TaskManager (SimplePlugin):

    def __init__ (self, bus):
        SimplePlugin.__init__ (self, bus)
        self._tasks = {}
        self.started = False

    def start (self):
        self.started = True
        for task in self._tasks.values ():
            if task [1] and task [1].finished:
                task [1].start ()
        self.bus.log ('Started TaskManager')

    def stop (self):
        self.clear ()
        self.bus.log ('Stopped TaskManager')
        self.started = False

    def _run_task (self, code, interval, *args, **kwargs):
        if code not in self._tasks:
            return
        self.bus.publish ('acquire_thread')
        task = self._tasks [code]
        task [1] = Timer (interval, self._run_task, [code, interval] + list (args), kwargs)
        task [1].start ()
        task [0] (*args, **kwargs)
        self.bus.publish ('release_thread')

    def add (self, code, task, interval, *args, **kwargs):
        timer = Timer (interval, self._run_task, [code, interval] + list (args), kwargs)
        self._tasks [code] = [task, timer]
        if self.started:
            timer.start ()

    def remove (self, code):
        self._tasks [code][1].cancel ()
        del self._tasks [code]

    def clear (self):
        for task in self._tasks.values ():
            if task [1]:
                task [1].cancel ()
        self._tasks.clear ()
