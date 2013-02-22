# -*- coding: utf-8 -*-

from cherrypy.process.plugins import SimplePlugin
import threading
import Queue

class TasksQueue (SimplePlugin):

    thread = None

    def __init__ (self, bus, queue_size = 100, timeout = 2):
        super (TasksQueue, self).__init__ (bus)
        self.queue = Queue.Queue (queue_size)
        self.running = False
        self.timeout = timeout

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
                self.bus.log ('Error in task {}'.format (func), level = 40, traceback = True)

    def put (self, task, *args, **kwargs):
        self.queue.put ((task, args, kwargs))
