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

class QLogger(object):

    '''
    Generates Compysition formatted log messages following the Syslog priority
    definition.
    '''

    def __init__(self, name, queue):
        self.name = name
        self.logs = queue

    def __log(self, level, message, event_id=None):
        while True:
            try:
                self.logs.put({"header":{"event_id":event_id},"data":{"level":level,
                                                        "time":time(),
                                                        "name":self.name,
                                                        "message":message}})
                break
            except QueueFull:
                self.logs.waitUntilFree()

    def critical(self, message, event_id=None):
        """Generates a log message with priority logging.CRITICAL
        """
        self.__log(logging.CRITICAL, message, event_id=event_id)

    def error(self, message, event_id=None):
        """Generates a log message with priority error(3).
        """
        self.__log(logging.ERROR, message, event_id=event_id)

    def warn(self, message, event_id=None):
        """Generates a log message with priority logging.WARN
        """
        self.__log(logging.WARN, message, event_id=event_id)
    warning=warn

    def info(self, message, event_id=None):
        """Generates a log message with priority logging.INFO.
        """
        self.__log(logging.INFO, message, event_id=event_id)

    def debug(self, message, event_id=None):
        """Generates a log message with priority logging.DEBUG
        """
        self.__log(logging.DEBUG, message, event_id=event_id)