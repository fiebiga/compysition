#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  testevent.py
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

from compysition import Actor
import gevent
from uuid import uuid4 as uuid
from gevent.pool import Pool


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
                                    default: {}
        - delay (float):            The interval in seconds to wait after pre_hook is called
                                    to generate the first event. Should have a value of >= 0
                                    default: 0
        - max_events (int):         The max number of events to produce

    '''

    def __init__(self, name, data_value="test", headers={}, producers=1, interval=1, delay=0, max_events=0, generate_error=True, *args, **kwargs):
        Actor.__init__(self, name, *args, **kwargs)
        self.blockdiag_config["shape"] = "flowchart.input"
        self.generate_error = generate_error
        self.name = name
        self.interval = interval
        self.delay = delay
        self.data_value = data_value or "test"
        self.headers = headers or {}
        self.interval = interval
        self.producers = producers
        self.max_events = max_events
        self.generated_events = 0
        self.producer_pool = Pool(self.producers)

    def pre_hook(self):
        for i in xrange(self.producers):
            self.producer_pool.spawn(self.produce)

    def produce(self):
        while self.loop():
            if self.max_events > 0:
                if self.generated_events == self.max_events:
                    break

            self.generated_events += 1
            event = self.create_event(data=self.data_value, **self.headers)
            self.send_event(event)
            if self.generate_error:
                self.generated_events += 1
                event = self.create_event(data=self.data_value, **self.headers)
                self.send_error(event)
            gevent.sleep(self.interval)

        self.logger.info("Stopped producing events.")
