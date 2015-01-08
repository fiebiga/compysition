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
#

from compysition.queue import QueuePool
from compysition.qlogger import QLogger
from compysition.errors import QueueEmpty, QueueFull, QueueConnected, SetupError, NoConnectedQueues
from gevent.pool import Group, Pool
from gevent import spawn, Greenlet
from gevent import sleep, socket
from gevent.event import Event
from time import time
from copy import copy, deepcopy
import traceback
import gevent.pool


class Actor(object):
    """
    The actor class is the abstract base class for all implementing compysition modules. 
    In order to be a valid 'module' and connectable with the compysition event flow, a module must be an extension of this class.

    The Actor is responsible for putting events on outbox queues, and consuming incoming events on inbound queues.
    """

    def __init__(self, name, size=0, frequency=1, generate_metrics=True, blocking_consume=False, *args, **kwargs):
        """
        **Base class for all compysition modules**

        Parameters:

        - name (str):               The instance name
        - size (int):               The max amount of events any outbound queue connected to this actor may contain. A value of 0 represents an infinite qsize  (Default: 100)
        - frequency (int):          The frequency that metrics are generated and broadcasted to the 'metrics' queue                                             (Default: 1)
        - generate_metrics (bool):  Whether or not to generate and broadcast metrics for this actor                                                             (Default: True)
        - blocking_consume (bool):  Define if this module should spawn a greenlet for every single 'consume' execution, or if
                                        it should execute 'consume' and block until that 'consume' is complete. This is usually
                                        only necessary if executing work on an event in the order that it was received is critical.                             (Default: False) 

        """
        
        self.name = name
        self.size = size
        self.frequency = frequency

        self.pool = QueuePool(size)
        
        self.logger = QLogger(name)

        self.__loop = True

        self.threads = Group()

        if generate_metrics:
            spawn(self.__metricEmitter)

        self.__run = Event()
        self.__run.clear()

        self.__connections = {}

        self.__children = {}
        self.__parents = {}

        self.__block = Event()
        self.__block.clear()

        self.__blocking_consume = blocking_consume

        self.__consumers = []

    def block(self):
        self.__block.wait()

    def connect_error(self, source_queue, destination, destination_queue, *args, **kwargs):
        self.connect(source_queue, destination, destination_queue, error_queue=True, *args, **kwargs)

    def connect(self, source_queue, destination, destination_queue, error_queue=False, check_existing=True):
        '''Connects the <source> queue to the <destination> queue.
        In fact, the source queue overwrites the destination queue.'''

        if check_existing:
            if source_queue in self.__children:
                raise QueueConnected("Queue %s is already connected to %s." % (source_queue, self.__children[source_queue]))
            else:
                self.__children[source_queue] = "%s.%s" % (destination.name, destination_queue)

            if destination_queue in destination.__parents:
                raise QueueConnected("Queue %s.%s is already connected to %s" % (destination.name, destination_queue, destination.__parents[destination_queue]))
            else:
                destination.__parents[destination_queue] = "%s.%s" % (self.name, source_queue)

        if not self.pool.hasQueue(source_queue):
            if not destination.pool.hasQueue(destination_queue):
                if not error_queue:
                    self.pool.createOutboundQueue(source_queue)
                else:
                    self.pool.createErrorQueue(source_queue)

                destination.registerConsumer(destination.consume, destination_queue)
                destination.pool.addInboundQueue(self.pool.getQueue(source_queue), name=destination_queue)
            else:
                if destination.is_consuming(destination_queue):
                    if not error_queue:
                        self.pool.addOutboundQueue(destination.pool.getQueue(destination_queue), name=source_queue)
                    else:
                        self.pool.addErrorQueue(destination.pool.getQueue(destination_queue), name=source_queue)

        elif source_queue in ["logs", "metrics", "failed"]:
            if not destination.pool.hasQueue(destination_queue):
                destination.registerConsumer(destination.consume, destination_queue)
                destination.pool.addInboundQueue(self.pool.getQueue(source_queue), name=destination_queue)
            else:
                if destination.is_consuming(destination_queue):
                    self.pool.moveQueue(self.pool.getQueue(source_queue), destination.pool.getQueue(destination_queue))

        self.pool.getQueue(source_queue).disableFallThrough()
        self.logger.info("Connected queue {0}.{1} <{2}> to {3}.{4} <{5}>".format(self.name, 
                                                                      source_queue,
                                                                      self.pool.getQueue(source_queue),
                                                                      destination.name,
                                                                      destination_queue,
                                                                      destination.pool.getQueue(destination_queue)))

        """
        if not destination.pool.hasQueue(destination_queue):
            #destination.pool.createQueue(destination_queue)
            destination.registerConsumer(destination.consume, destination_queue)

        if not self.pool.hasQueue(source_queue):
            if not error_queue:
                self.pool.createOutboundQueue(source_queue)
            else:
                self.pool.createErrorQueue(source_queue)

        destination.pool.addInboundQueue(self.pool.getQueue(source_queue), name=destination_queue)
        #setattr(destination.pool.queues, destination_queue, self.pool.getQueue(source_queue))
        self.pool.getQueue(source_queue).disableFallThrough()
        """

    def flushQueuesToDisk(self):
        '''Writes whatever event in the queue to disk for later retrieval.'''

        # for queue in self.pool.listQueues(names=True):
        #     size = self.pool.getQueue(queue).size()
        #     print "%s %s %s" % (self.name, queue, size)

        self.logger.debug("Writing queues to disk.")

    def getChildren(self, queue=None):
        '''Returns the queue name <queue> is connected to.'''

        if queue is None:
            return [self.__children[q] for q in self.__children.keys()]
        else:
            return self.__children[queue]

    def loop(self):
        '''The global lock for this module'''

        return self.__loop

    def readQueuesFromDisk(self):
        '''Reads events from disk into the queue.'''

        self.logger.debug("Reading queues from disk.")

    def registerConsumer(self, function, queue):
        '''Registers <function> to process all events in <queue>

        Do not trap errors.  When <function> fails then the event will be
        submitted to the "failed" queue,  If <function> succeeds to the
        success queue.'''
        self.__consumers.append(queue)
        consumer = self.threads.spawn(self.__consumer, function, queue)
        #consumer.function = function.__name__
        #consumer.queue = queue

    def is_consuming(self, queue_name):
        return queue_name in self.__consumers

    def start(self):
        '''Starts the module.'''

        # self.readQueuesFromDisk()
        #self.logger.logs = self.pool.queues.logs
        self.logger.connect_logs_queue(self.pool.queues.logs)

        if hasattr(self, "preHook"):
            self.logger.debug("preHook() found, executing")
            self.preHook()

        self.__run.set()
        self.logger.debug("Started with max queue size of %s events and metrics interval of %s seconds." % (self.size, self.frequency))

    def stop(self):
        '''Stops the loop lock and waits until all registered consumers have exit.'''

        self.__loop = False
        
        self.__block.set()
        self.threads.join()

        if hasattr(self, "postHook"):
            self.logger.debug("postHook() found, executing")
            self.postHook()

    def send_event(self, event, queue=None):
        """
        Sends event to all registered outbox queues. If multiple queues are consuming the event,
        a deepcopy of the event is sent instead of raw event
        """
        if queue is not None: 
            self.__submit(event, queue)
        else:
            try:
                queues = self.pool.listOutboundQueues(default=False)
                self.__loopSubmit(event, queues)
            except NoConnectedQueues:
                event_id = event["header"].get("event_id", None)
                self.logger.warn("Attempted to send event to outbox queues, but no outbox queues were connected", event_id=event_id)

    def send_error(self, event, queue=None):
        """
        Sends event to all registered error queues. If multiple queues are consuming the event,
        a deepcopy of the event is sent instead of raw event
        """
        if queue is not None: 
            self.__submit(event, queue)
        else:
            try:
                queues = self.pool.listErrorQueues()
                self.__loopSubmit(event, queues)
            except NoConnectedQueues:
                event_id = event["header"].get("event_id", None)
                self.logger.warn("Attempted to send event on error queue, but no error queues were connected", event_id=event_id)

    def __loopSubmit(self, event, queues):
        try:
            queue = queues.next()
            self.__submit(event, queue)
            for queue in queues:
                self.__submit(deepcopy(event), queue)
        except StopIteration:
            raise NoConnectedQueues("No outgoing queues connected to send to")

    def __submit(self, event, queue):
        '''A convenience function which submits <event> to <queue>
        and deals with QueueFull and the module lock set to False.'''
        while self.loop():
            try:
                queue.put(event)
                break
            except QueueFull as err:
                err.waitUntilEmpty()

    def __consumer(self, function, queue):
        '''Greenthread which applies <function> to each element from <queue>
        '''

        self.__run.wait()
        while self.loop():
            queue_object = self.pool.getQueue(queue)
            if queue_object.qsize() > 0:
                try:
                    event = self.pool.getQueue(queue).get(timeout=10)
                    original_data = deepcopy(event["data"])
                except QueueEmpty as err:
                    queue_object.waitUntilContent()
                else:
                    if self.__blocking_consume:
                        self.__doConsume(function, event, queue, original_data)
                    else:
                        self.threads.spawn(self.__doConsume, function, event, queue, original_data)
            else:
                queue_object.waitUntilContent()

        while True:
            if self.pool.getQueue(queue).qsize() > 0:
                try:
                    event = self.pool.getQueue(queue).get()
                    original_data = deepcopy(event["data"])
                except QueueEmpty as err:
                    break
                else:
                    self.threads.spawn(self.__doConsume, function, event, queue, original_data)
            else:
                break

    def __doConsume(self, function, event, queue, original_data):
        """
        A function designed to be spun up in a greenlet to maximize concurrency for the __consumer method
        This function actually calls the consume function for the actor
        """
        try:
            function(event, origin=queue)
        except QueueFull as err:
            event["data"] = original_data
            self.pool.getQueue(queue).rescue(event)
            err.waitUntilFree()
        except Exception as err:
            print traceback.format_exc() # This is an unhappy path to get an exception at this point, so we want to print to STDOUT
                                            # In case this is a problem with the log_module itself. At least for now
            self.logger.error(traceback.format_exc())

    def __metricEmitter(self):
        '''A greenthread which collects the queue metrics at the defined interval.'''

        self.__run.wait()
        while self.loop():
            for queue in self.pool.listQueues():
                stats = queue.stats()
                for item in stats:
                    while self.loop():
                        try:
                            self.pool.queues.metrics.put({"header": {}, "data": (time(), "compysition", socket.gethostname(), "queue.%s.%s.%s" % (self.name, queue.name, item), stats[item], '', ())})
                            break
                        except QueueFull:
                            self.pool.queues.metrics.waitUntilEmpty()
            sleep(self.frequency)

    def consume(self, event, *args, **kwargs):
        """Raises error when user didn't define this function in his module.
        Due to the nature of *args and **kwargs in determining method definition, another check is put in place
        in 'router/default.py' to ensure that *args and **kwargs is defined"""

        raise SetupError("You must define a consume function as consume(self, event, *args, **kwargs)")
