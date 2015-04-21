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

from compysition.actors import Null
from compysition.errors import ModuleInitFailure, NoSuchModule
from gevent import signal, event, sleep
import traceback
from compysition.actor import Actor

class Director():

    def __init__(self, size=500, frequency=1, generate_metrics=False):
        signal(2, self.stop)
        signal(15, self.stop)
        self.actors = {}
        self.size = size
        self.frequency = frequency
        self.generate_metrics=generate_metrics

        self.metric_actor = self.__create_actor(Null, "null_metrics")
        self.log_actor = self.__create_actor(Null, "null_logs")
        self.failed_actor = self.__create_actor(Null, "null_faileds")

        self.__running = False
        self.__block = event.Event()
        self.__block.clear()

    def get_actor(self, name):
        return self.actors.get(name, None)

    def connect_error_queue(self, source, destination, *args, **kwargs):
        self.connect_queue(source, destination, error_queue=True, *args, **kwargs)


    def connect_queue(self, source, destinations, error_queue=False, *args, **kwargs):
        '''**Connects one queue to the other.**

        There are 2 accepted syntaxes. Consider the following scenario:
            director    = Director()
            test_event  = director.register_actor(TestEvent,  "test_event")
            std_out     = director.register_actor(STDOUT,     "std_out")

        First accepted syntax
            Queue names will default to the name of the source for the destination actor,
                and to the name of the destination for the source actor
            director.connect_queue(test_event, std_out)

        Second accepted syntax
            director.connect_queue((test_event, "custom_outbox_name"), (stdout, "custom_inbox_name"))

        Both syntaxes may be used interchangeably, such as in:
            director.connect_queue(test_event, (stdout, "custom_inbox_name"))
        '''

        if not isinstance(destinations, list):
            destinations = [destinations]

        (source_name, source_queue_name) = self._parse_connect_arg(source)
        source = self.get_actor(source_name)

        for destination in destinations:
            (destination_name, destination_queue_name) = self._parse_connect_arg(destination)
            destination = self.get_actor(destination_name)
            if destination_queue_name is None:
                destination_queue_name = source.name

            if source_queue_name is None:
                destination_source_queue_name = destination.name
            else:
                destination_source_queue_name = source_queue_name

            if not error_queue:
                source.connect_queue(destination_source_queue_name, destination, destination_queue_name)
            else:
                source.connect_error_queue(destination_source_queue_name, destination, destination_queue_name)

    def _parse_connect_arg(self, input):
        if isinstance(input, tuple):
            (actor, queue_name) = input
            if isinstance(actor, Actor):
                actor_name = actor.name
        elif isinstance(input, Actor):
            actor_name = input.name
            queue_name = None                # Will have to be generated deterministically

        return (actor_name, queue_name)

    def register_actor(self, actor, name, *args, **kwargs):
        '''Initializes the mdoule using the provided <args> and <kwargs>
        arguments.'''

        try:
            new_actor = self.__create_actor(actor, name, *args, **kwargs)
            self.actors[name] = new_actor
            return new_actor
        except Exception:
            raise ModuleInitFailure(traceback.format_exc())

    def register_log_actor(self, actor, name, *args, **kwargs):
        """Initialize a log actor for the director instance"""
        self.log_actor = self.__create_actor(actor, name, *args, **kwargs)
        return self.log_actor

    def register_metric_actor(self, actor, name, *args, **kwargs):
        """Initialize a metric actor for the director instance"""
        self.metric_actor = self.__create_actor(actor, name, *args, **kwargs)
        return self.metric_actor

    def register_failed_actor(self, actor, name, *args, **kwargs):
        """Initialize a failed actor for the director instance"""
        self.failed_actor = self.__create_actor(actor, name, *args, **kwargs)
        return self.failed_actor

    def __create_actor(self, actor, name, *args, **kwargs):
        return actor(name, size=self.size, frequency=self.frequency, generate_metrics=self.generate_metrics, *args, **kwargs)

    def _setup_default_connections(self):
        '''Connect all log, metric, and failed queues to their respective actors
           If a log actor has been registered but a failed actor has not been, the failed actor
           will default to also using the log actor
        '''

        if isinstance(self.failed_actor, Null) and not isinstance(self.log_actor, Null):
            self.failed_actor = self.log_actor
        else:
            self.failed_actor.connect_queue("logs", self.log_actor, "inbox", check_existing=False)

        for actor in self.actors.values():
            actor.connect_queue("logs", self.log_actor, "inbox", check_existing=False) 
            actor.connect_queue("metrics", self.metric_actor, "inbox", check_existing=False)
            actor.connect_queue("failed", self.failed_actor, "inbox", check_existing=False)

        self.log_actor.connect_queue("logs", self.log_actor, "inbox", check_existing=False)
        self.metric_actor.connect_queue("logs", self.log_actor, "inbox", check_existing=False)

    def is_running(self):
        return self.__running

    def start(self, block=True):
        '''Starts all registered actors.'''
        self.__running = True
        self._setup_default_connections()

        for actor in self.actors.values():
            actor.start()

        self.log_actor.start()
        self.metric_actor.start()
        if self.failed_actor is not self.log_actor:
            self.failed_actor.start()

        if block:
            self.block()

    def block(self):
        '''Blocks until stop() is called.'''
        self.__block.wait()

    def stop(self):
        '''Stops all input actors.'''
        self.__block.set()
        for actor in self.actors.values():
            actor.stop()

        self.metric_actor.stop()
        self.failed_actor.stop()
        self.log_actor.stop()
        self.__running = False
        self.__block.set()
