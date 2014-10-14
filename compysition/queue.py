#!/usr/bin/env python
#
# -*- coding: utf-8 -*-
#
#  Copyright 2014 Adam Fiebig <fiebig.adam@gmail.com>
#  Originally based on "wishbone" project by smetj
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

from uuid import uuid4
from collections import deque
from compysition.errors import QueueEmpty, QueueFull, ReservedName, QueueMissing
from gevent import sleep
from gevent.event import Event
import gevent.queue as gqueue
from time import time


class Container():
    pass


class QueuePool(object):

    def __init__(self, size):
        self.__size = size
        self.queues = Container()
        self.queues.metrics = Queue("metrics", maxsize=size)
        self.queues.logs = Queue("logs", maxsize=size, fallthrough=False)
        self.queues.failed = Queue("failed", maxsize=size)
        self.inbound_queues = Container()
        self.outbound_queues = Container()
        self.error_queues = Container()

    def listOutboundQueues(self, names=False, default=True):
        '''returns the list of queue names from the queuepool.
        '''

        if default:
            blacklist = []
        else:
            blacklist = ['failed', 'logs', 'metrics']

        for m in self.outbound_queues.__dict__.keys():
            if m not in blacklist:
                if not names:
                    yield getattr(self.outbound_queues, m)
                else:
                    yield m

    def listQueues(self, names=False, default=True):
        '''returns the list of queue names from the queuepool.
        '''

        if default:
            blacklist = []
        else:
            blacklist = ['failed', 'logs', 'metrics']

        for m in self.queues.__dict__.keys():
            if m not in blacklist:
                if not names:
                    yield getattr(self.queues, m)
                else:
                    yield m

    def listInboundQueues(self, names=False):
        '''returns the list of queue names from the queuepool.
        '''
        for m in self.inbound_queues.__dict__.keys():
            if not names:
                yield getattr(self.inbound_queues, m)
            else:
                yield m

    def listErrorQueues(self, names=False):
        for m in self.error_queues.__dict__.keys():
            if not names:
                yield getattr(self.error_queues, m)
            else:
                yield m

    def createErrorQueue(self, name):
        '''Creates an error Queue.'''
        if name in ["metrics", "logs", "failed"]:
            raise ReservedName

        queue = Queue(name, maxsize=self.__size)
        setattr(self.queues, name, queue)
        setattr(self.error_queues, name, queue)

    def createInboundQueue(self, name):
        '''Creates an inbound Queue.'''
        if name in ["metrics", "logs", "failed"]:
            raise ReservedName

        queue = Queue(name, maxsize=self.__size)
        setattr(self.queues, name, queue)
        setattr(self.inbound_queues, name, queue)

    def addOutboundQueue(self, queue, name=None):
        '''Adds an existing outbound Queue.'''


        if name is None:
            name = queue.name

        if queue.name in ["metrics", "logs", "failed"]:
            raise ReservedName

        setattr(self.queues, name, queue)
        setattr(self.outbound_queues, name, queue)

    def addErrorQueue(self, queue, name=None):
        '''Adds an existing outbound Queue.'''


        if name is None:
            name = queue.name

        if queue.name in ["metrics", "logs", "failed"]:
            raise ReservedName



        setattr(self.queues, name, queue)
        setattr(self.error_queues, name, queue)

    def addInboundQueue(self, queue, name=None):
        '''Adds an existing outbound Queue.'''
        #if queue.name in ["metrics", "logs", "failed"]:
        #    raise ReservedName
        if name is None:
            name = queue.name

        setattr(self.queues, name, queue)
        setattr(self.inbound_queues, name, queue)

    def createOutboundQueue(self, name):
        '''Creates an outbound Queue.'''
        if name in ["metrics", "logs", "failed"]:
            raise ReservedName

        queue = Queue(name, maxsize=self.__size)
        setattr(self.queues, queue.name, queue)
        setattr(self.outbound_queues, queue.name, queue)

    def hasQueue(self, name):
        '''Returns true when queue with <name> exists.'''

        try:
            getattr(self.queues, name)
            return True
        except:
            return False

    def moveQueue(self, old_queue, new_queue):
        try:
            if old_queue.qsize() > 0:
                while True:
                    try:
                        event = old_queue.next()
                        new_queue.put(event)
                    except StopIteration:
                        break
            setattr(self.queues, old_queue.name, new_queue)
        except Exception as err:
            raise Exception("Error moving queue {0} <{1}> to {2} <{3}>: {4}".format(old_queue.name, 
                                                                          old_queue,
                                                                          new_queue.name, 
                                                                          new_queue,
                                                                          err))


    def getQueue(self, name):
        '''Convenience funtion which returns the queue instance.'''

        try:
            return getattr(self.queues, name)
        except:
            raise QueueMissing("Queue {0} does not exist".format(name))

    def createQueue(self, name):
        '''Creates a non specific Queue for the pool. Usually these are queues used for administration of an actor.'''

        queue = Queue(name, maxsize=self.__size)
        setattr(self.queues, name, queue)

    def join(self):
        '''Blocks until all queues in the pool are empty.'''
        for queue in self.listQueues():
            queue.waitUntilEmpty()
            # while True:
            #     if queue.size() > 0:
            #         sleep(0.1)
            #     else:
            #         break


class Queue(gqueue.Queue):
        
    '''A queue used to organize communication messaging between Compysition Actors.

    Parameters:

        - maxsize (int):   The max number of elements in the queue.
                            Default: 1

    When a queue is created, it will drop all messages. This is by design.
    When <disableFallThrough()> is called, the queue will keep submitted
    messages.  The motivation for this is that when is queue is not connected
    to any consumer it would just sit there filled and possibly blocking the
    chain.

    The <stats()> function will reveal whether any events have disappeared via
    this queue.

    '''

    def __init__(self, name, fallthrough=True, *args, **kwargs):
        super(Queue, self).__init__(*args, **kwargs)

        self.name = name

        self.__in = 0
        self.__out = 0
        self.__cache = {}
        self.__content = Event()

    def get(self, *args, **kwargs):
        '''Gets an element from the queue.'''

        try:
            element = super(Queue, self).get(block=False, *args, **kwargs)
        except gqueue.Empty:
            raise QueueEmpty("Queue {0} has no waiting events".format(self.name))

        self.__out += 1
        self.__content.clear()
        return element

    def rescue(self, element):
        self.put(event)

    def stats(self):
        '''Returns statistics of the queue.'''

        return {"size": self.qsize(),
                "in_total": self.__in,
                "out_total": self.__out,
                "in_rate": self.__rate("in_rate", self.__in),
                "out_rate": self.__rate("out_rate", self.__out)
                }


    def put(self, element, *args, **kwargs):
        '''Puts element in queue.'''

        try:
            super(Queue, self).put(element, *args, **kwargs)
        except gqueue.Full:
            raise QueueFull("Queue {0} is full".format(self.name))
        self.__content.set()
        self.__in += 1

    def __rate(self, name, value):

        if name not in self.__cache:
            self.__cache[name] = {"value": (time(), value), "rate": 0}
            return 0

        (time_then, amount_then) = self.__cache[name]["value"]
        (time_now, amount_now) = time(), value

        if time_now - time_then >= 1:
            self.__cache[name]["value"] = (time_now, amount_now)
            self.__cache[name]["rate"] = (amount_now - amount_then) / (time_now - time_then)

        return self.__cache[name]["rate"]

    
    def waitUntilContent(self):
        '''Blocks until at least 1 slot is taken.'''

        try:
            self.__content.wait(timeout=0.1)
        except:
            pass
    
    def disableFallThrough(self):
        pass
