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
from compysition.event import Event
from compysition.actors.util.udplib import UDPInterface
from apscheduler.schedulers.gevent import GeventScheduler


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
        interval (Optional[float] OR dict):
            | The interval (in seconds) between each generated event.
            | Should have a value > 0.
            | Can also be a dict, supporting values of weeks, days, hours, minutes, and seconds
            | default: 5
        delay (Optional[float]):
            | The time (in seconds) to wait before initial event generation.
            | Default: 0
        generate_error (Optional[bool]):
            | Whether or not to also send the event via Actor.send_error
            | Default: False

    '''

    DEFAULT_INTERVAL = {'weeks': 0,
                         'days': 0,
                         'hours': 0,
                         'minutes': 0,
                         'seconds': 5}

    def __init__(self, name, event_class=Event, event_kwargs=None, producers=1, interval=5, delay=0, generate_error=False, *args, **kwargs):
        super(EventGenerator, self).__init__(name, *args, **kwargs)
        self.blockdiag_config["shape"] = "flowchart.input"
        self.generate_error = generate_error
        self.interval = self._parse_interval(interval)
        self.delay = delay
        self.event_kwargs = event_kwargs or {}
        self.output = event_class
        self.producers = producers
        self.scheduler = GeventScheduler()

    def _parse_interval(self, interval):
        _interval = self.DEFAULT_INTERVAL

        if isinstance(interval, int):
            _interval['seconds'] = interval
        elif isinstance(interval, dict):
            _interval.update(interval)

        return _interval

    def _initialize_jobs(self):
        for i in xrange(self.producers):
            self.scheduler.add_job(self._do_produce, 'interval', **self.interval)

    def pre_hook(self):
        self._initialize_jobs()
        gevent.sleep(self.delay)
        self.scheduler.start()

    def post_hook(self):
        self.scheduler.shutdown()

    def _do_produce(self):
        event = self.output[0](**self.event_kwargs)
        self.logger.debug("Generated new event {event_id}".format(event_id=event.event_id))
        self.send_event(event)
        if self.generate_error:
            event = self.output(**self.event_kwargs)
            self.send_error(event)

    def consume(self, event, *args, **kwargs):
        self._do_produce()


class UDPEventGenerator(EventGenerator):
    """
    **An actor that utilized a UDP interface to coordinate between other UDPEventGenerator actors
    running on its same subnet to coordinate a master/slave relationship of generating an event
    with the specified arguments and attributes. Only the master in the 'pool' of registered actors
    will generate an event at the specified interval**
    """

    def __init__(self, name, service="default", environment_scope='default', *args, **kwargs):
        super(UDPEventGenerator, self).__init__(name, *args, **kwargs)
        self.peers_interface = UDPInterface("{0}-{1}".format(service, environment_scope), logger=self.logger)

    def pre_hook(self):
        self.peers_interface.start()
        super(UDPEventGenerator, self).pre_hook()

    def _do_produce(self):
        if self.peers_interface.is_master():
            super(UDPEventGenerator, self)._do_produce()


class CronEventGenerator(EventGenerator):

    """
    **An EventGenerator that supports cron-style scheduling, using the following keywords: year, month, day, week, day_of_week,
    hour, minute, second. See 'apscheduler' documentation for specifics of configuring those keywords**
    """

    DEFAULT_INTERVAL = {'year': '*',
                        'month': '*',
                        'day': '*',
                        'week': '*',
                        'day_of_week': '*',
                        'hour': '*',
                        'minute': '*',
                        'second': '*/12'}

    def _parse_interval(self, interval):
        _interval = self.DEFAULT_INTERVAL

        if isinstance(interval, dict):
            _interval.update(interval)

        return _interval

    def _initialize_jobs(self):
        for producer in xrange(self.producers):
            self.scheduler.add_job(self._do_produce, 'cron', **self.interval)


class UDPCronEventGenerator(CronEventGenerator, UDPEventGenerator):
    pass


