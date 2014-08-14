#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       testevent.py
#
#       Copyright 2014 Adam Fiebig fiebig.adam@gmail.com
#
#       Original testevent.py created by Jelle Smet <development@smetj.net>
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 3 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.
#

from compysition import Actor
from uuid import uuid4 as uuid
from compysition.errors import QueueLocked, QueueFull, SetupError
from gevent import sleep, spawn
from gevent.event import Event

class TestEvent(Actor):

    '''**Generates a test event at the chosen interval.**

    This module is only available for testing purposes and has further hardly any use.

    Events have following format:

        { "header":header_value, "data":data_value }

    Parameters:

        - name (str):               The instance name when initiated.

        - interval (float):         The interval in seconds between each generated event.
                                    Should have a value > 0.
                                    default: 1
        - data_value (str):         Allows specification of test event data content
                                    default: "test"
        - header_value (str):       Allows specification of test event header content
                                    default: Empty Dict {}
        - delay (float):            The interval in seconds to wait after preHook is called
                                    to generate the first event. Should have a value of >= 0
                                    default: 0

    Queues:

        - outbox:    Contains the generated events.
    '''

    def __init__(self, name, data_value="test", header_value={}, interval=1, delay=0, *args, **kwargs):
        Actor.__init__(self, name, *args, **kwargs)
        self.name = name
        self.interval = interval
        self.delay = delay
        self.data_value = data_value or "test"
        self.header_value = header_value or {}
        if interval == 0:
            self.sleep = self.doNoSleep
        else:
            self.sleep = self.doSleep

        self.throttle=Event()
        self.throttle.set()

    def consume(self, event, *args, **kwargs):
        self.logging.error("THIS SHOULDNT HAVE BEEN CALLED")

    def preHook(self):
        spawn(self.go)

    def go(self):
        switcher = self.getContextSwitcher(100)

        if self.delay > 0:
            self.doSleep(self.delay)

        while switcher():
            self.throttle.wait()
            try:
                event = {"header":self.header_value,"data":self.data_value}
                event['header']['event_id'] = uuid()
                self.send_event({"header":self.header_value,"data":self.data_value})
            except (QueueFull, QueueLocked):
                self.queuepool.outbox.waitUntilPutAllowed()
            self.sleep(self.interval)

    def doSleep(self, interval):
        sleep(interval)

    def doNoSleep(self, interval):
        pass

    def enableThrottling(self):
        self.throttle.clear()

    def disableThrottling(self):
        self.throttle.set()
