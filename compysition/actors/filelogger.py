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
from compysition.actors.util import RotatingFileHandler, LoggingConfigLoader
import gevent
from compysition import Queue
import logging
import logging.handlers
import traceback

class FileLogger(Actor):
    '''**Prints incoming events to a log file for debugging.**
    '''

    def __init__(self, name, default_filename="compysition.log", *args, **kwargs):
        super(FileLogger, self).__init__(name, *args, **kwargs)
        self.blockdiag_config["shape"] = "note"
        self.default_filename = default_filename

        self.config = LoggingConfigLoader(**kwargs)
        self.loggers = {}

    def _create_logger(self, filepath):
        file_logger = logging.getLogger(filepath)
        logHandler = RotatingFileHandler(r'{0}'.format(filepath), maxBytes=int(self.config.config['maxBytes']), backupCount=int(self.config.config['backupCount']))
        logFormatter = logging.Formatter('%(message)s') # We will do ALL formatting ourselves in qlogger, as we want to be extremely literal to make sure the timestamp
                                                        # is generated at the time that logger.log was invoked, not the time it was written to file
        logHandler.setFormatter(logFormatter)
        file_logger.addHandler(logHandler)
        file_logger.setLevel(self.config.config['level'])
        return file_logger

    def _process_log_entry(self, event):
        event_filename = event.get("logger_filename", self.default_filename)
        logger = self.loggers.get(event_filename, None)
        if not logger:
            logger = self._create_logger("{0}/{1}".format(self.config.config['directory'], event_filename))
            self.loggers[event_filename] = logger

        self._do_log(logger, event)

    def _do_log(self, logger, event):
        module_name = event.data.get("name", None)
        id = event.data.get("id", None)
        message = event.data.get("message", None)
        level = event.data.get("level", None)
        time = event.data.get("time", None)

        entry_prefix = "{0} {1} ".format(time, logging._levelNames.get(level)) # Use the time from the logging invocation as the timestamp

        if id:
            entry = "module={0}, id={1} :: {2}".format(module_name, id, message)
        else:
            entry = "module={0} :: {1}".format(module_name, message)

        try:
            logger.log(level, "{0}{1}".format(entry_prefix, entry))
        except:
            print traceback.format_exc()

    def consume(self, event, *args, **kwargs):
        self._process_log_entry(event)
