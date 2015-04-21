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
from compysition.event import CompysitionEvent

class QLogger(object):

    '''
    Generates Compysition formatted log messages following the python priority
    definition.
    '''

    def __init__(self, name, queue=None):
        self.name = name
        self.logs = queue
        self.buffer = []

    def log(self, level, message, event=None, log_entry_id=None):
        """
        Uses log_entry_id explicitely as the logged ID, if defined. Otherwise, will attempt to ascertain the ID from 'event', if passed
        """
        if not log_entry_id:
            if event:
                log_entry_id = event.meta_id

        while True:
            try:
                log_data = {"id":       log_entry_id,
                            "level":    level,
                            "time":     datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')[:-3],
                            "name":     self.name,
                            "message":  message}

                log_event = CompysitionEvent(data=log_data)
                if self.logs is None:
                    self.buffer.append(log_event)
                else:
                    self.logs.put(log_event)
                break
            except QueueFull:
                self.logs.wait_until_free()

    def critical(self, message, event=None, log_entry_id=None):
        """Generates a log message with priority logging.CRITICAL
        """
        self.log(logging.CRITICAL, message, event=event, log_entry_id=log_entry_id)

    def error(self, message, event=None, log_entry_id=None):
        """Generates a log message with priority error(3).
        """
        self.log(logging.ERROR, message, event=event, log_entry_id=log_entry_id)

    def warn(self, message, event=None, log_entry_id=None):
        """Generates a log message with priority logging.WARN
        """
        self.log(logging.WARN, message, event=event, log_entry_id=log_entry_id)
    warning=warn

    def info(self, message, event=None, log_entry_id=None):
        """Generates a log message with priority logging.INFO.
        """
        self.log(logging.INFO, message, event=event, log_entry_id=log_entry_id)

    def debug(self, message, event=None, log_entry_id=None):
        """Generates a log message with priority logging.DEBUG
        """
        self.log(logging.DEBUG, message, event=event, log_entry_id=log_entry_id)

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