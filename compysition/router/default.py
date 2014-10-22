#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  default.py
#
#  Copyright 2014 Adam Fiebig <fiebig.adam@gmail.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#

from compysition.module import Null
from compysition.errors import ModuleInitFailure, NoSuchModule
from gevent import signal, event, sleep
import traceback

class Container():
    pass


class ModulePool():

    def __init__(self):

        self.module = Container()

    def list(self):
        '''Returns a generator returning all module instances.'''

        for m in self.module.__dict__.keys():
            yield self.module.__dict__[m]

    def getModule(self, name):
        '''Returns a module instance'''

        try:
            return getattr(self.module, name)
        except AttributeError:
            raise NoSuchModule("Could not find module %s" % name)


class Default():

    def __init__(self, size=500, frequency=1, generate_metrics=False):
        signal(2, self.stop)
        signal(15, self.stop)
        self.pool = ModulePool()
        self.admin_pool = ModulePool()
        self.size = size
        self.frequency = frequency
        self.generate_metrics=generate_metrics

        self.metric_module = self.__createModule(Null, "null_metrics")
        self.log_module = self.__createModule(Null, "null_logs")
        self.failed_module = self.__createModule(Null, "null_faileds")

        self.__running = False
        self.__block = event.Event()
        self.__block.clear()

    def block(self):
        '''Blocks until stop() is called.'''
        self.__block.wait()

    def connect_error(self, source, destination, *args, **kwargs):
        self.connect(source, destination, error_queue=True, *args, **kwargs)


    def connect(self, source, destination, error_queue=False, *args, **kwargs):
        '''Connects one queue to the other.

        For convenience, the syntax of the queues is <modulename>.<queuename>
        For example:

            stdout.inbox
        '''

        (source_module, source_queue) = source.split('.')
        (destination_module, destination_queue) = destination.split('.')

        source = self.pool.getModule(source_module)
        destination = self.pool.getModule(destination_module)

        if not error_queue:
            source.connect(source_queue, destination, destination_queue)
        else:
            source.connect_error(source_queue, destination, destination_queue)

    def getChildren(self, module):
        children = []

        def lookupChildren(module, children):
            for module in self.pool.getModule(module).getChildren():
                name = module.split(".")[0]
                if name not in children:
                    children.append(name)
                    lookupChildren(name, children)

        lookupChildren(module, children)
        return children

    def registerModule(self, module, name, *args, **kwargs):
        '''Initializes the mdoule using the provided <args> and <kwargs>
        arguments.'''

        try:
            setattr(self.pool.module, name, self.__createModule(module, name, *args, **kwargs))
        except Exception:
            raise ModuleInitFailure(traceback.format_exc())

    def registerLogModule(self, module, name, *args, **kwargs):
        """Initialize a log module for the router instance"""
        self.log_module = self.__createModule(module, name, *args, **kwargs)

    def registerMetricModule(self, module, name, *args, **kwargs):
        """Initialize a metric module for the router instance"""
        self.metric_module = self.__createModule(module, name, *args, **kwargs)

    def registerFailedModule(self, module, name, *args, **kwargs):
        """Initialize a failed module for the router instance"""
        self.failed_module = self.__createModule(module, name, *args, **kwargs)

    def __createModule(self, module, name, *args, **kwargs):
        return module(name, size=self.size, frequency=self.frequency, generate_metrics=self.generate_metrics, *args, **kwargs)

    def setupDefaultConnections(self):
        '''Connect all log, metric, and failed queues to their respective modules
           If a log module has been registered but a failed module has not been, the failed module
           will default to also using the log module
        '''

        if isinstance(self.failed_module, Null) and not isinstance(self.log_module, Null):
            self.failed_module = self.log_module
        else:
            self.failed_module.connect("logs", self.log_module, "inbox", check_existing=False)

        for module in self.pool.list():
            module.connect("logs", self.log_module, "inbox", check_existing=False) 
            module.connect("metrics", self.metric_module, "inbox", check_existing=False)
            module.connect("failed", self.failed_module, "inbox", check_existing=False)

        self.log_module.connect("logs", self.log_module, "inbox", check_existing=False)
        self.metric_module.connect("logs", self.log_module, "inbox", check_existing=False)


        """
        if isinstance(self.failed_module, Null) and not isinstance(self.log_module, Null):
            self.failed_module = self.log_module
        else:
            self.failed_module.connect("logs", self.log_module, "{0}_failed".format(self.failed_module.name))

        for module in self.pool.list():
            module.connect("logs", self.log_module, "{0}_logs".format(module.name), check_existing=False) 
            module.connect("metrics", self.metric_module, "{0}_metrics".format(module.name), check_existing=False)
            module.connect("failed", self.failed_module, "{0}_failed".format(module.name), check_existing=False)

        self.log_module.connect("logs", self.log_module, "{0}_logs".format(self.log_module.name))
        self.metric_module.connect("logs", self.log_module, "{0}_metrics".format(self.metric_module.name))
        """

    def isRunning(self):
        return self.__running

    def start(self):
        '''Starts all registered modules.'''
        self.__running = True
        self.setupDefaultConnections()

        for module in self.pool.list():
            module.start()

        self.log_module.start()
        self.metric_module.start()
        if self.failed_module is not self.log_module:
            self.failed_module.start()

    def stop(self):
        '''Stops all input modules.'''

        for module in self.pool.list():
            module.stop()
        self.metric_module.stop()
        self.failed_module.stop()
        self.log_module.stop()
        self.__running = False
        self.__block.set()
