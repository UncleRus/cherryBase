# -*- coding: utf-8 -*-

from cherrypy.process.plugins import SimplePlugin
import threading
import Queue
import logging
from cherrypy.process.wspbus import states


class ExitThread (Exception):
    pass


class IterativePlugin (SimplePlugin):

    def __init__ (self, bus, name = None):
        super (IterativePlugin, self).__init__ (bus)
        self.name = name or type (self).__name__
        self.running = False
        self.thread = None

    def start (self):
        self.running = True
        if not self.thread:
            self.thread = threading.Thread (target = self.run)
            self.thread.start ()
        self.bus.log ('Started %s' % self.name)

    def stop (self):
        self.bus.log ('Stopping %s...' % self.name)
        self.running = False
        if self.thread:
            self.thread.join ()
            self.thread = None
        self.bus.log ('Stopped %s' % self.name)

    def run (self):
        self.bus.publish ('acquire_thread')
        while self.running:
            try:
                self.iterate ()
            except ExitThread:
                break
        self.bus.publish ('release_thread')


class TasksQueue (IterativePlugin):
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
        self.timeout = timeout

    def start (self):
        super (TasksQueue, self).start ()
    start.priority = 76

    def iterate (self):
        try:
            func, args, kwargs = self.queue.get (block = True, timeout = self.timeout)
            func (*args, **kwargs)
        except Queue.Empty:
            if self.running == 'stopping':
                raise ExitThread ()
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
        super (TaskManager, self).__init__ (bus)
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
        task [1] = threading.Timer (interval, self._run_task, [code, interval] + list (args), kwargs)
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
        timer = threading.Timer (interval, self._run_task, [code, interval] + list (args), kwargs)
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


class StarterStopper (SimplePlugin):
    '''
    Плагин, имеющий два списка callable: on_start и on_stop.
    Функции из on_start выполняются в отдельном потоке сразу после запуска шины.
    Функции из on_stop выполняются в основном потоке в процессе остановки шины.

    Плагин подключается к шине автоматически и доступен под именем
    ``cherrypy.engine.starter_stopper``
    '''

    def __init__ (self, bus):
        super (StarterStopper, self).__init__ (bus)
        self.thread = None
        self.on_start = []
        self.on_stop = []

    def start (self):
        if not self.thread:
            self.thread = threading.Thread (target = self.run)
            self.thread.start ()
    start.priority = 75

    def stop (self):
        if self.thread:
            self.thread.join ()
            self.thread = None
        for task in self.on_stop:
            task ()
        self.bus.log ('Stopper succesfully worked')

    def run (self):
        self.bus.publish ('acquire_thread')

        self.bus.wait ((states.STARTED, states.STOPPING, states.EXITING))

        if self.bus.state == states.STARTED:
            for task in self.on_start:
                try:
                    task ()
                except:
                    self.bus.log ('An exception occured in on_start task {}'.format (task), logging.ERROR, traceback = True)
            self.bus.log ('Starter succesfully worked')
        else:
            self.bus.log ('Wrong bus state, starter tasks are ignored', logging.WARNING)

        self.bus.publish ('release_thread')
