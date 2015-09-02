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

class QueuePool(object):

    def __init__(self, size):
        self.__size = size
        self.default_outbound_queues = {}
        self.default_outbound_queues['metrics'] = Queue("metrics", maxsize=size)
        self.default_outbound_queues['logs'] = Queue("logs", maxsize=size)
        self.inbound_queues = {}
        self.outbound_queues = {}
        self.error_queues = {}

    def _add_queue(self, name, queue_scope, queue=None):
        if not queue:
            queue = Queue(name, maxsize=self.__size)

        queue_scope[name] = queue
        return queue

    def list_all_queues(self, default_queues=True):
        """
        Returns an aggregate list of all Queue objects in this pool
        """
        queue_list = self.inbound_queues.values() + self.outbound_queues.values() + self.error_queues.values()
        if default_queues:
            queue_list += self.default_queues

        return queue_list

    def add_outbound_queue(self, name, queue=None):
        '''Creates an outbound queue or adds the queue reference specified'''
        return self._add_queue(name, self.outbound_queues, queue=queue)

    def add_error_queue(self, name, queue=None):
        '''Creates an error queue or adds the queue reference specified'''
        return self._add_queue(name, self.error_queues, queue=queue)

    def add_inbound_queue(self, name, queue=None):
        '''Creates an inbound queue or adds the queue reference specified'''
        return self._add_queue(name, self.inbound_queues, queue=queue)

    def move_queue(self, old_queue, new_queue, queue_scope=None):
        """
        Move the contents from one queue object to another, then replace that queue reference
        with the new queue. 
        Kwarg 'queue_scope' is which type of queue the new queue will be on this pool. Defaults to outbound_queue
        """
        queue_scope = queue_scope or self.outbound_queues
        try:
            if old_queue.qsize() > 0:
                while True:
                    try:
                        event = old_queue.next()
                        new_queue.put(event)
                    except StopIteration:
                        break
            return self._add_queue(new_queue.name, queue_scope, queue=new_queue)
        except Exception as err:
            raise Exception("Error moving queue {0} <{1}> to {2} <{3}>: {4}".format(old_queue.name, 
                                                                          old_queue,
                                                                          new_queue.name, 
                                                                          new_queue,
                                                                          err))

    def join(self):
        '''Blocks until all queues in the pool are empty.'''
        for queue in self.list_all_queues():
            queue.wait_until_empty()


class Queue(gqueue.Queue):
        
    '''A queue used to organize communication messaging between Compysition Actors.

    Parameters:

        - maxsize (int):   The max number of elements in the queue.
                            Default: 1

    '''

    def __init__(self, name, *args, **kwargs):
        super(Queue, self).__init__(*args, **kwargs)

        self.name = name
        self.__in = 0
        self.__out = 0
        self.__cache = {}
        self.__has_content = Event()
        self.__has_content.clear()

    def get(self, *args, **kwargs):
        '''Gets an element from the queue.'''

        try:
            element = super(Queue, self).get(block=False, *args, **kwargs)
        except gqueue.Empty:
            self.__has_content.clear()
            raise QueueEmpty("Queue {0} has no waiting events".format(self.name))

        self.__out += 1
        return element

    def rescue(self, element):
        self.put(element)

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
            self.__has_content.set()
        except gqueue.Full:
            raise QueueFull("Queue {0} is full".format(self.name))
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

    def wait_until_content(self):
        '''Blocks until at least 1 slot is taken.'''
        self.__has_content.wait()


    def wait_until_empty(self):
        '''Blocks until the queue is completely empty.'''

        while not self.__has_content.is_set():
            sleep(0)
