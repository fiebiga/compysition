#!/usr/bin/env python
#
# -*- coding: utf-8 -*-
#
#  logging.py
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

from compysition.errors import QueueFull
from time import time
from os import getpid
import logging
from datetime import datetime

class QLogger(object):

    '''
    Generates Compysition formatted log messages following the python priority
    definition.
    '''

    def __init__(self, name, queue=None):
        self.name = name
        self.logs = queue
        self.buffer = []

    def log(self, level, message, event_id=None):
        while True:
            try:
                event = {"header":{"event_id":event_id},"data":{"level":level,
                                                        "time":datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')[:-3],
                                                        "name":self.name,
                                                        "message":message}}
                if self.logs is None:
                    self.buffer.append(event)
                else:
                    self.logs.put(event)
                break
            except QueueFull:
                self.logs.waitUntilFree()

    def critical(self, message, event_id=None):
        """Generates a log message with priority logging.CRITICAL
        """
        self.log(logging.CRITICAL, message, event_id=event_id)

    def error(self, message, event_id=None):
        """Generates a log message with priority error(3).
        """
        self.log(logging.ERROR, message, event_id=event_id)

    def warn(self, message, event_id=None):
        """Generates a log message with priority logging.WARN
        """
        self.log(logging.WARN, message, event_id=event_id)
    warning=warn

    def info(self, message, event_id=None):
        """Generates a log message with priority logging.INFO.
        """
        self.log(logging.INFO, message, event_id=event_id)

    def debug(self, message, event_id=None):
        """Generates a log message with priority logging.DEBUG
        """
        self.log(logging.DEBUG, message, event_id=event_id)

    def connect_logs_queue(self, queue):
        self.logs = queue
        self.dump_buffer()

    def dump_buffer(self):
        while True:
            try:
                event = self.buffer.pop()
                self.logs.put(event)
            except Exception as err:
                break