#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       stdout.py
#
#       Copyright 2014 Adam Fiebig fiebig.adam@gmail.com
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
from compysition.module.util import RotatingFileHandler, LoggingConfigLoader
import gevent
from compysition import Queue
from os import getpid
from time import strftime, localtime
from time import time
import logging
import logging.handlers
import os
import traceback

class FileLogger(Actor):
    '''**Prints incoming events to a log file for debugging.**
    '''

    def __init__(self, name, filename, colorize=False, *args, **kwargs):
        super(FileLogger, self).__init__(name, *args, **kwargs)

        self.config = LoggingConfigLoader(**kwargs)
        self.filepath = "{0}/{1}".format(self.config.config['directory'], filename)
        self.colorize = colorize
        
        self.colors={
            logging.CRITICAL:"\x1B[0;35m",  # Purple
            logging.ERROR:"\x1B[1;31m",     # Red
            logging.WARNING:"\x1B[1;33m",   # Orange
            logging.INFO:None,              # No Coloring
            logging.DEBUG:"\x1B[1;37m"}     # White

        self.logger_queue = Queue("logger_queue") 

        self.file_logger = logging.getLogger(self.name)

        logHandler = RotatingFileHandler(r'{0}'.format(self.filepath), maxBytes=int(self.config.config['maxBytes']), backupCount=int(self.config.config['backupCount']))
        logFormatter = logging.Formatter('%(message)s') # We will do ALL formatting ourselves in qlogger, as we want to be extremely literal to make sure the timestamp
                                                        # is generated at the time that logger.log was invoked, not the time it was written to file
        logHandler.setFormatter(logFormatter)
        self.file_logger.addHandler(logHandler)
        self.file_logger.setLevel(self.config.config['level'])

    def preHook(self):
        self.threads.spawn(self.__go)

    def __go(self):
        """
        Consumes a private queue, expects the event in the queue to be in a tuple,
        in the format of (log_level (int), message)
        """
        while self.loop():
            if self.logger_queue.qsize() > 0:
                entry = self.logger_queue.get()
                try:
                    self.file_logger.log(entry[0], entry[1])
                except Exception as err:
                    print traceback.format_exc()
            else:
                self.logger_queue.waitUntilContent()

        while True:
            if self.logger_queue.qsize() > 0:
                entry = self.logger_queue.get()
                
                try:
                    self.file_logger.log(entry[0], entry[1])
                except Exception as err:
                    print traceback.format_exc()
            else:
                break



    def consume(self, event, *args, **kwargs):
        module_name = event["data"].get("name", None)
        event_id = event["header"].get("event_id", None)
        message = event["data"].get("message", None)
        level = event["data"].get("level", None)
        time = event["data"].get("time", None)

        entry_prefix = "{0} {1} ".format(time, logging._levelNames.get(level)) # Use the time from the logging invocation as the timestamp

        if event_id:
            entry = "module={0}, event_id={1} :: {2}".format(module_name, event_id, message)
        else:
            entry = "module={0} :: {1}".format(module_name, message)

        if self.colorize:
            entry = self.colorize_entry(entry, level)

        self.logger_queue.put((level, "{0}{1}".format(entry_prefix, entry)))

    def colorize_entry(self, message, level):
        color = self.colors[level]
        if color is not None:
            message = color + message + "\x1B[0m"
        return message