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
from gevent.pool import Pool
from compysition.event import *
from compysition.actors.util.udplib import UDPInterface

class EventGenerator(Actor):

    '''**Generates a test event at the chosen interval.**

    Parameters:

        name (str):
            | The instance name
        event_class (Optional[compysition.event.Event]):
            | The class that the generated event should be created as
            | Default: Event
        event_kwargs (Optional[int]):
            | Any additional kwargs to add to the event, including data
        producers (Optional[int]):
            | The number of greenthreads to spawn that each spawn events at the provided interval
            | Default: 1
        interval (Optional[float]):
            | The interval (in seconds) between each generated event.
            | Should have a value > 0.
            | default: 120
        delay (Optional[float]):
            | The time (in seconds) to wait before initial event generation.
            | Default: 0
        max_events (Optional[int]):
            | The max number of events to produce. A value of 0 will indicate infinite events
            | Default: 0
        generate_error (Optional[bool]):
            | Whether or not to also send the event via Actor.send_error
            | Default: False

    '''

    def __init__(self, name, event_class=Event, event_kwargs=None, producers=1, interval=120, delay=0, max_events=0, generate_error=False, *args, **kwargs):
        super(EventGenerator, self).__init__(name, *args, **kwargs)
        self.blockdiag_config["shape"] = "flowchart.input"
        self.generate_error = generate_error
        self.name = name
        self.interval = interval
        self.delay = delay
        self.event_kwargs = event_kwargs or {}
        self.event_class = event_class
        self.output = event_class
        self.interval = interval
        self.producers = producers
        self.max_events = max_events
        self.generated_events = 0
        self.producer_pool = Pool(self.producers)

    def pre_hook(self):
        for i in xrange(self.producers):
            self.producer_pool.spawn(self.produce)

    def produce(self):
        gevent.sleep(self.delay)
        while self.loop():
            if self.max_events > 0:
                if self.generated_events == self.max_events:
                    break
            self._do_produce()
            gevent.sleep(self.interval)

        self.logger.info("Stopped producing events.")

    def _do_produce(self):
        self.generated_events += 1
        event = self.event_class(**self.event_kwargs)
        self.send_event(event)
        if self.generate_error:
            self.generated_events += 1
            event = self.event_class(**self.event_kwargs)
            self.send_error(event)

    def consume(self, event, *args, **kwargs):
        self._do_produce()


class UDPEventGenerator(EventGenerator):
    """
    An actor that utilized a UDP interface to coordinate between other UDPEventGenerator actors
    running on its same subnet to coordinate a master/slave relationship of generating an event
    with the specified arguments and attributes. Only the master in the 'pool' of registered actors
    will generate an event at the specified interval
    """

    def __init__(self, name, service="default", environment_scope='default', *args, **kwargs):
        super(UDPEventGenerator, self).__init__(name, *args, **kwargs)
        self.peers_interface = UDPInterface("{0}-{1}".format(service, environment_scope), logger=self.logger)

    def pre_hook(self):
        self.peers_interface.start()
        super(UDPEventGenerator, self).pre_hook()

    def _do_produce(self):
        self.peers_interface.wait_until_master()
        super(UDPEventGenerator, self)._do_produce()

    def consume(self, event, *args, **kwargs):
        if self.peers_interface.is_master():
            self._do_produce()
        else:
            self.logger.warn("Received prompt to generate event, but actor is not the master in the pool", event=event)
