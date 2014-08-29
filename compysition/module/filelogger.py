#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       stdout.py
#
#       Copyright 2013 Jelle Smet development@smetj.net
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
#

from compysition import Actor
from compysition.tools import RotatingFileHandler, LoggingConfigLoader
import gevent
from os import getpid
from time import strftime, localtime
from time import time
import logging
import logging.handlers
import os

class FileLogger(Actor):
    '''**Prints incoming events to a log file for debugging.**
    '''

    def __init__(self, name, filename, *args, **kwargs):
        Actor.__init__(self, name, *args, **kwargs)
        self.config = LoggingConfigLoader(**kwargs)
        self.filepath = "{0}/{1}".format(self.config.config['directory'], filename)
        
        self.colors={
            logging.CRITICAL:"\x1B[0;35m",  # Purple
            logging.ERROR:"\x1B[1;31m",     # Red
            logging.WARNING:"\x1B[1;33m",   # Orange
            logging.INFO:None,              # No Coloring
            logging.DEBUG:"\x1B[1;37m"}     # White

        self.logger_queue = gevent.queue.Queue()

        self.logger = logging.getLogger("filelogger")
        logHandler = RotatingFileHandler(r'{0}'.format(self.filepath), maxBytes=self.config.config['maxBytes'], backupCount=self.config.config['backupCount'])
        logFormatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        logHandler.setFormatter(logFormatter)
        self.logger.addHandler(logHandler)
        self.logger.setLevel(self.config.config['level'])

    def preHook(self):
        gevent.spawn(self.go)

    def go(self):
        """
        Consumes a private queue, expects the event in the queue to be in a tuple,
        in the format of (log_level (int), 
        """
        while not self.is_blocked():
            if self.logger_queue.qsize() > 0:
                entry = self.logger_queue.get()
                self.logger.log(entry[0], entry[1])
            else:
                gevent.sleep(1)


    def consume(self, event, *args, **kwargs):

        if event["header"].get("event_id"):
            entry = "pid-{0}, module={1} id={2} {3}".format(event["data"][2], event["data"][3], event["header"].get("request_id"), event["data"][4])
        else:
            entry = "pid-{0} {1} {2}".format(event["data"][2], event["data"][3], event["data"][4])

        entry = self.colorize(entry, event["data"][0])

        self.logger_queue.put((event["data"][0], entry))

    def colorize(self, message, level):
        color = self.colors[level]
        if color is not None:
            message = color + message + "\x1B[0m"
        return message