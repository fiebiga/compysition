#!/usr/bin/env python
#
# -*- coding: utf-8 -*-
#
#  consumer.py
#
#  Copyright 2013 Jelle Smet <development@smetj.net>
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
from gevent import spawn, sleep, joinall
from gevent import Greenlet
from gevent.event import Event
from gevent.lock import Semaphore
from compysition.errors import QueueLocked, SetupError, QueueFull
import traceback

class Consumer():

    def __init__(self, setupbasic=True):
        self.__doConsumes = []
        self.__block = Event()
        self.__block.clear()

        self.destination_queues = {}

        if setupbasic == True:
            self.__setupBasic()

        self.__greenlet = []
        self.metrics = {}

        self.__enable_consuming = Event()
        self.__enable_consuming.set()

    def start(self):
        '''Starts to execute all the modules registered <self.consume> functions.'''

        self.logging.info("Started")

        for c in self.__doConsumes:
            self.__greenlet.append(spawn(self.__doConsume, c[0], c[1]))
            self.logging.info('Function %s started to consume queue %s.'%(str(c[0]),str(c[1])))

    def shutdown(self):
        '''Stops each module by making <self.loop> return False and which unblocks <self.block>'''

        if self.__block.isSet():
            self.logging.warn('Already shutdown.')
        else:
            self.logging.info('Shutdown')
            self.__block.set()
            self.queuepool.shutdown()
    stop=shutdown

    def block(self):
        '''Convenience function which blocks untill the actor is in stopped state.'''

        self.__block.wait()

    def register_destination(self, queue):
        """ Registers the queue as a destination queue for the module, and adding it
        to the list of queues to send outbox events to"""
        print("Registered {0} as a destination".format(queue.name))
        self.destination_queues[queue.name] = queue

    def registerConsumer(self, fc, queue):
        '''Registers <fc> as a consuming function for the given queue <q>.'''

        self.__doConsumes.append((fc, queue))

    def loop(self):
        '''Convenience function which returns True until stop() has be been
        called.  A word of caution.  Since we're dealing with eventloops,
        if you use a loop which doesn't have any gevent aware code in it
        then you'll block the event loop.'''

        return not self.__block.isSet()

    def send_event(self, event, destination="ALL"):
        """ Funtion to wrap the functionality of sending to all connected outboxes.
        This functionality can be altered by specifying a destination queue name instead with the
        'destination' arg
        """

        all_queues = self.queuepool.getQueueInstances()

        #for queue in self.queuepool.getQueueInstances().values():
        for queue in self.destination_queues.keys():
            print("Trying to put in {0}".format(queue))
            self.putEvent(event, all_queues[queue])

    def putEvent(self, event, destination):
        '''Convenience function submits <event> into <destination> queue.
        When this fails due to QueueFull or QueueLocked, the function will
        block untill the error state disappeard and will resubmit the event
        after which it will exit.

        Should ideally be used by input modules.
        '''

        while self.loop():
            try:
                destination.put(event)
                print("Putting on {0}".format(destination.name))
                break
            except QueueLocked:
                destination.waitUntilPutAllowed()
            except QueueFull:
                destination.waitUntilFreePlace()

    def enableConsuming(self):
        '''Sets a flag which makes the router start executing consume().

        The module will starts/continues to excete the consume() function.'''

        self.__enable_consuming.set()
        self.logging.debug("enableConsuming called. Started consuming.")

    def disableConsuming(self):
        '''Sets a flag which makes the router stop executing consume().

        The module will not process further any events at this point until enableConsuming() is called.'''

        self.__enable_consuming.clear()
        self.logging.debug("disableConsuming called. Stopped consuming.")


    def __doConsume(self, fc, q):
        '''Executes <fc> against each element popped from <q>.
        '''


        while self.loop():
            self.__enable_consuming.wait()
            try:
                event = q.get()
                try:
                    event["header"]
                    event["data"]
                except:
                    self.logging.warn("Invalid event format received from parent. Purged")
                    continue
            except QueueLocked:
                self.logging.debug("Queue %s locked."%(str(q)))
                q.waitUntilGetAllowed()
            else:
                try:
                    fc(event, origin=q.name)
                except TypeError:
                    self.logging.warn("You must define a consume function as consume(self, event, *args, **kwargs)")
                except Exception as err:
                    self.logging.warn("Problem executing %s. Sleeping for a second. Reason: %s"%(str(fc),err))
                    traceback.print_exc()
                    q.rescue(event)
                    sleep(1)

        self.logging.info('Function %s has stopped consuming queue %s'%(str(fc),str(q)))

    def __setupBasic(self):
        '''Create in- and outbox and a consumer consuming inbox.'''
        self.createQueue('inbox')
        self.createQueue('outbox')
        self.registerConsumer(self.consume, self.queuepool.inbox)

    def consume(self, event, *args, **kwargs):
        """Raises error when user didn't define this function in his module.
        Due to the nature of *args and **kwargs in determining method definition, another check is put in place
        in 'router/default.py' to ensure that *args and **kwargs is defined"""

        raise SetupError("You must define a consume function as consume(self, event, *args, **kwargs)")