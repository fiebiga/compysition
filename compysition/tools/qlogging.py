#!/usr/bin/env python
#
# -*- coding: utf-8 -*-
#
#  qlogging.py
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


from compysition.tools import CompysitionQueue
from time import time
from os import getpid
import logging

class QLogging():

    '''
    Generates Compysition logging events, following the pythonic logging module priority levels
    Generated logs are stored in a local queue <self.logs>.  It is up to an external process the consume this queue.
    '''

    def __init__(self, name):
        self.logs=CompysitionQueue()
        self.name=name
        self.pid=getpid()

    def __log(self, level, message):
        self.logs.put({"header":{},"data":(level, time(), self.pid, self.name, message)})

    def critical(self, message):
        """Generates a log message with priority logging.CRITICAL
        """
        self.__log(logging.CRITICAL, message)

    def error(self, message):
        """Generates a log message with priority error(3).
        """
        self.__log(logging.ERROR, message)

    def warn(self, message):
        """Generates a log message with priority logging.WARN
        """
        self.__log(logging.WARN, message)
    warning=warn

    def info(self, message):
        """Generates a log message with priority logging.INFO.
        """
        self.__log(logging.INFO, message)

    def debug(self, message):
        """Generates a log message with priority logging.DEBUG
        """
        self.__log(logging.DEBUG, message)