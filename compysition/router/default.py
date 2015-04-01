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
from compysition.actor import Actor

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


    def connect(self, source, destinations, error_queue=False, *args, **kwargs):
        '''**Connects one queue to the other.**

        There are 2 accepted syntaxes. Consider the following scenario:
            router = Default()
            test_event  = router.registerModule(TestEvent,  "test_event")
            std_out     = router.registerModule(STDOUT,     "std_out")

        First accepted syntax
            Queue names will default to the name of the source for the destination module,
                and to the name of the destination for the source module
            router.connect(test_event, std_out)

        Second accepted syntax
            router.connect((test_event, "custom_outbox_name"), (stdout, "custom_inbox_name"))

        Both syntaxes may be used interchangeably, such as in:
            router.connect(test_event, (stdout, "custom_inbox_name"))
        '''

        if not isinstance(destinations, list):
            destinations = [destinations]

        (source_name, source_queue_name) = self._parse_connect_arg(source)
        source = self.pool.getModule(source_name)

        for destination in destinations:
            (destination_name, destination_queue_name) = self._parse_connect_arg(destination)
            destination = self.pool.getModule(destination_name)
            if destination_queue_name is None:
                destination_queue_name = source.name

            if source_queue_name is None:
                destination_source_queue_name = destination.name
            else:
                destination_source_queue_name = source_queue_name

            if not error_queue:
                source.connect(destination_source_queue_name, destination, destination_queue_name)
            else:
                source.connect_error(destination_source_queue_name, destination, destination_queue_name)

    def _parse_connect_arg(self, input):
        if isinstance(input, tuple):
            (module, queue_name) = input
            if isinstance(module, Actor):
                module_name = module.name
        elif isinstance(input, Actor):
            module_name = input.name
            queue_name = None                # Will have to be generated deterministically

        return (module_name, queue_name)

    def registerModule(self, module, name, *args, **kwargs):
        '''Initializes the mdoule using the provided <args> and <kwargs>
        arguments.'''

        try:
            setattr(self.pool.module, name, self.__createModule(module, name, *args, **kwargs))
            return getattr(self.pool.module, name)
        except Exception:
            raise ModuleInitFailure(traceback.format_exc())

    def registerLogModule(self, module, name, *args, **kwargs):
        """Initialize a log module for the router instance"""
        self.log_module = self.__createModule(module, name, *args, **kwargs)
        return self.log_module

    def registerMetricModule(self, module, name, *args, **kwargs):
        """Initialize a metric module for the router instance"""
        self.metric_module = self.__createModule(module, name, *args, **kwargs)
        return self.metric_module

    def registerFailedModule(self, module, name, *args, **kwargs):
        """Initialize a failed module for the router instance"""
        self.failed_module = self.__createModule(module, name, *args, **kwargs)
        return self.failed_module

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
