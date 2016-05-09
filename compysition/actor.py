#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  setup.py
#
#  Copyright 2014 Adam Fiebig <fiebig.adam@gmail.com>
#  Originally based on 'wishbone' project by smetj
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

from compysition.queue import QueuePool
from compysition.logger import Logger
from compysition.errors import *
from restartlet import RestartPool
from compysition.event import Event
from gevent import sleep
from gevent.event import Event as GEvent
from gevent.local import local
from copy import deepcopy
import traceback
import functools
import abc

class Actor(object):
    """
    The actor class is the abstract base class for all implementing compysition actors.
    In order to be a valid 'module' and connectable with the compysition event flow, a module must be an extension of this class.

    The Actor is responsible for putting events on outbox queues, and consuming incoming events on inbound queues.
    """

    __metaclass__ = abc.ABCMeta

    DEFAULT_EVENT_SERVICE = "default"
    input = Event
    output = Event

    def __init__(self, name, size=0, blocking_consume=False, rescue=False, max_rescue=5, *args, **kwargs):
        """
        **Base class for all compysition actors**

        Parameters:

            name (str):
                | The instance name
            size (Optional[int]):
                | The max amount of events any outbound queue connected to this actor may contain. A value of 0 represents an infinite qsize
                | (Default: 0)
            blocking_consume (Optional[bool]):
                | Define if this module should spawn a greenlet for every single 'consume' execution, or if
                | it should execute 'consume' and block until that 'consume' is complete. This is usually
                | only necessary if executing work on an event in the order that it was received is critical.
                | (Default: False)

        """
        self.blockdiag_config = {"shape": "box"}
        self.name = name
        self.size = size
        self.pool = QueuePool(size)
        self.logger = Logger(name, self.pool.logs)
        self.__loop = True
        self.threads = RestartPool(logger=self.logger, sleep_interval=1)

        self.__run = GEvent()
        self.__run.clear()
        self.__block = GEvent()
        self.__block.clear()
        self.__blocking_consume = blocking_consume
        self.rescue = rescue
        self.max_rescue = max_rescue

    def block(self):
        self.__block.wait()

    def connect_error_queue(self, destination_queue_name="inbox", *args, **kwargs):
        self.__connect_queue(pool_scope=self.pool.error, destination_queue_name="error_{0}".format(destination_queue_name), *args, **kwargs)

    def connect_log_queue(self, destination_queue_name="inbox", *args, **kwargs):
        self.__connect_queue(pool_scope=self.pool.logs, destination_queue_name="log_{0}".format(destination_queue_name), *args, **kwargs)

    def connect_queue(self, *args, **kwargs):
        self.__connect_queue(pool_scope=self.pool.outbound, *args, **kwargs)

    def __connect_queue(self, source_queue_name="outbox", destination=None, destination_queue_name="inbox", pool_scope=None, check_existing=True):
        """Connects the <source_queue_name> queue to the <destination> queue.
        If the destination queue already exists, the source queue is changed to be a reference to that queue, as Many to One connections
        are supported, but One to Many is not"""

        source_queue = pool_scope.get(source_queue_name, None)
        destination_queue = destination.pool.inbound.get(destination_queue_name, None)

        if check_existing:
            if source_queue:
                raise QueueConnected("Outbound queue {queue_name} on {source_name} is already connected".format(queue_name=source_queue_name,
                                                                                                                source_name=self.name))

            if destination_queue:
                raise QueueConnected("Inbound queue {queue_name} on {destination_name} is already connected".format(queue_name=destination_queue_name,
                                                                                                                    destination_name=destination.name))

        if not source_queue:
            if not destination_queue:
                source_queue = pool_scope.add(source_queue_name)
                destination.register_consumer(destination_queue_name, source_queue)
            elif destination_queue:
                pool_scope.add(source_queue_name, queue=destination_queue)

        else:
            if not destination_queue:
                destination.register_consumer(destination_queue_name, source_queue)
            else:
                source_queue.dump(destination_queue)
                pool_scope.add(destination_queue.name, queue=destination_queue)

        self.logger.info("Connected queue '{0}' to '{1}.{2}'".format(source_queue_name, destination.name, destination_queue_name))

    def loop(self):
        '''The global lock for this module'''

        return self.__loop

    def is_running(self):
        return self.__run.is_set()

    def register_consumer(self, queue_name, queue):
        '''
        Add the passed queue and queue name to
        '''
        self.pool.inbound.add(queue_name, queue=queue)
        self.threads.spawn(self.__consumer, self.consume, queue)

    def start(self):
        '''Starts the module.'''

        if not isinstance(self.input, tuple):
            if isinstance(self.input, list):
                self.input = tuple(self.input)
            else:
                self.input = (self.input, )

        if not isinstance(self.output, tuple):
            if isinstance(self.output, list):
                self.output = tuple(self.output)
            else:
                self.output = (self.output, )

        if hasattr(self, "pre_hook"):
            self.logger.debug("pre_hook() found, executing")
            self.pre_hook()

        self.__run.set()
        self.logger.debug("Started with max queue size of {size} events".format(size=self.size))

    def stop(self):
        '''Stops the loop lock and waits until all registered consumers have exit.'''

        self.__loop = False
        self.__block.set()

        # This should do a self.threads.join() but currently it is blocking. This issue needs to be resolved
        # But in the meantime post_hook will execute

        if hasattr(self, "post_hook"):
            self.logger.debug("post_hook() found, executing")
            self.post_hook()

    def send_event(self, event, queue=None, queues=None, check_output=True):
        """
        Sends event to all registered outbox queues. If multiple queues are consuming the event,
        a deepcopy of the event is sent instead of raw event.

        If 'queue' is provided, it supercedes all others and submits ONLY to that queue
        """
        if check_output and not isinstance(event, self.output):
            raise InvalidActorOutput("Event was of type '{_type}', expected '{output}'".format(_type=type(event), output=self.output))

        if queue is not None:
            self._submit(queue, event=event)
        else:
            if queues:
                send_queues = queues
            else:
                send_queues = self.pool.outbound.values()
            self._loop_submit(event, send_queues)

    def send_error(self, event, queue=None, queues=None):
        """
        Calls 'send_event' with all error queues as the 'queues' parameter
        """
        if not queues:
            queues = self.pool.error.values()

        if queues or queue:
            self.send_event(event, queue=queue, queues=queues, check_output=False)

    def _loop_submit(self, event, queues):
        """
        :param event:
        :param queues:
        :return:
        """
        if len(queues) > 0:
            event_queue_pairs = [(queues[0], event)] + [(queue, deepcopy(event)) for queue in queues[1:]]

            if queues:
                map(lambda event_queue_pair: self._submit(event_queue_pair[0], event=event_queue_pair[1]), event_queue_pairs)

    def _submit(self, queue, event=None):
        if event is not None:
            queue.put(event)
            sleep(0)

    def __consumer(self, function, queue):
        '''Greenthread which applies <function> to each element from <queue>
        '''

        self.__run.wait()

        while self.loop():
            queue.wait_until_content()
            try:
                event = queue.get(timeout=10)
            except QueueEmpty:
                pass
            else:
                if self.__blocking_consume:
                    self.__do_consume(function, event, queue)
                else:
                    self.threads.spawn(self.__do_consume, function, event, queue, restart=False)

        while True:
            if queue.qsize() > 0:
                try:
                    event = queue.get()
                except QueueEmpty as err:
                    break
                else:
                    self.threads.spawn(self.__do_consume, function, event, queue, restart=False)
            else:
                break

    def __do_consume(self, function, event, queue):
        """
        A function designed to be spun up in a greenlet to maximize concurrency for the __consumer method
        This function actually calls the consume function for the actor
        """
        try:

            #TODO: Determine if this is what you want
            if not isinstance(event, self.input):
                #raise InvalidActorInput("Event was of type '{_type}', expected '{input}'".format(_type=type(event), input=self.input))
                new_event = event.convert(self.input[0])
                self.logger.warning("Incoming event was of type '{_type}' when type {input} was expected. Converted to {converted}".format(
                    _type=type(event), input=self.input, converted=type(new_event)), event=event)
                event = new_event

            function(event, origin=queue.name, origin_queue=queue)
        except QueueFull as err:
            err.wait_until_free()
            queue.put(event)
        except InvalidActorInput as error:
            self.logger.error("Invalid input detected: {0}".format(error))
        except InvalidEventConversion:
            self.logger.error("Event was of type '{_type}', expected '{input}'".format(_type=type(event), input=self.input))
        except Exception as err:
            self.logger.warning("Event exception caught: {traceback}".format(traceback=traceback.format_exc()), event=event)
            rescue_tracker = "{actor}_rescue_num".format(actor=self.name)
            if self.rescue and event.get(rescue_tracker, 0) < self.max_rescue:
                setattr(event, rescue_tracker, event.get(rescue_tracker, 0) + 1)
                sleep(1)
                queue.put(event)
            else:
                event.error = err
                self.send_error(event)

    def create_event(self, *args, **kwargs):
        if len(self.output) == 1:
            return self.output[0](**kwargs)
        raise ValueError("Unable to call create_event function with multiple output types defined")

    @abc.abstractmethod
    def consume(self, event, *args, **kwargs):
        """
        Args:
            event:  The implementation of event.Event this actor is consuming
            *args:
            **kwargs:
        """
        pass