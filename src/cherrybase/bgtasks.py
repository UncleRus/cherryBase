# -*- coding: utf-8 -*-

from cherrypy.process.plugins import SimplePlugin
import threading
import Queue
import logging
from threading import Timer


class TasksQueue (SimplePlugin):
    '''
    Фоновая очередь задач (callables), работающих последовательно.
    Используется для постановки длительных задач в фон из обработчиков.
    Поскольку задачи выполняются последовательно одна за одной,
    они являются потокобезопасными друг относительно друга и могут
    использовать какие-либо общие ресурсы.
    В задачах могут быть использованы декораторы func:`cherrybase.db.use_db`
    и func:`cherrybase.orm.use_orm`.
    
    Плагин подключается к шине автоматически и доступен под именем
    ``cherrypy.engine.bg_tasks_queue``

    *Пример:*
    
    .. code-block:: python
    
        class MyController (object):
        
            def __init__ (self):
                self.count = 0
        
            @cherrypy.expose
            def index (self):
                cherrypy.engine.bg_tasks_queue.queue.put (self.task)
                return 'Task was executed {} times'.format (self.count)
            
            @cherrybase.db.use_db ()
            def task (self, db):
                cherrypy.engine.log ('Starting task execution')
                db.cursor ().execute ('insert into tbl values (%s)', (self.count,))
                time.sleep (10)
                self.count += 1
                cherrypy.engine.log ('Stopped task execution')
        
    '''

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
    start.priority = 76

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
    '''
    Менеджер асинхронных фоновых задач, исполняющихся через
    определенные интервалы. В задачах могут быть использованы декораторы func:`cherrybase.db.use_db`
    и func:`cherrybase.orm.use_orm`.
    Менеджер пытается соблюдать интервал между запусками задачи, однако, если задача выполняется
    дольше установленного для нее интервала, менеджер будет запсукать ее с фактической
    частотой.

    Плагин подключается к шине автоматически и доступен под именем
    ``cherrypy.engine.task_manager``
    '''

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
    start.priority = 77

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

    def add (self, code, task, interval, args = (), kwargs = {}):
        '''
        Добавить задачу в расписание
        
        :param code: Уникальный ID задачи
        :param task: Callable задачи
        :param interval: Интервал между запусками задачи.
        :param args: Аргументы, с котрыми будет вызываться callable задачи
        :param kwargs: Имнованные аргументы, с котрыми будет вызываться callable задачи
        '''
        timer = Timer (interval, self._run_task, [code, interval] + list (args), kwargs)
        self._tasks [code] = [task, timer]
        if self.started:
            timer.start ()

    def remove (self, code):
        '''
        Удалить задачу из расписания

        :param code: Уникальный ID задачи
        '''
        self._tasks [code][1].cancel ()
        del self._tasks [code]

    def clear (self):
        '''
        Удалить все задачи из расписания
        '''
        for task in self._tasks.values ():
            if task [1]:
                task [1].cancel ()
        self._tasks.clear ()
