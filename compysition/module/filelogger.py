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
import gevent
from os import getpid
from time import strftime, localtime
from time import time
import logging
import logging.handlers
import os

class RotatingFileHandler(logging.handlers.RotatingFileHandler):

	def __init__(self, file_path, *args, **kwargs):
		self.make_file(file_path)
		super(RotatingFileHandler, self).__init__(file_path, *args, **kwargs)

	def make_file(self, file_path):
		file_dir = os.path.dirname(file_path)
		if not os.path.isfile(file_path):
			if not os.path.exists(file_dir):
				self.make_file_dir(file_dir)
			open(file_path, 'w+')

	def make_file_dir(self, file_path):
		sub_path = os.path.dirname(file_path)
		if not os.path.exists(sub_path):
			self.make_file_dir(sub_path)
		if not os.path.exists(file_path):
			os.mkdir(file_path)

class FileLogger(Actor):
    '''**Prints incoming events to a log file for debugging.**
    '''

    def __init__(self, name, filepath, *args, **kwargs):
        Actor.__init__(self, name, *args, **kwargs)
        self.filepath = filepath
        self.levels={0:logging.CRITICAL,
                     1:logging.CRITICAL,
                     2:logging.CRITICAL,
                     3:logging.ERROR,
                     4:logging.WARNING,
                     5:logging.INFO,
                     6:logging.INFO,
                     7:logging.DEBUG} # For legacy support. Ultimately, let's make the router use these numbers to begin with.
        self.colors={
            0:"\x1B[0;35m",
            1:"\x1B[1;35m",
            2:"\x1B[0;31m",
            3:"\x1B[1;31m",
            4:"\x1B[1;33m",
            5:"\x1B[1;30m",
            6:"\x1B[1;37m",
            7:"\x1B[1;37m"}
        self.logger_queue = gevent.queue.Queue()

        self.logger = logging.getLogger("filelogger")
        logHandler = RotatingFileHandler(r'{0}'.format(self.filepath), maxBytes=209715200, backupCount=10)
        logFormatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        logHandler.setFormatter(logFormatter)
        self.logger.addHandler(logHandler)
        self.logger.setLevel(logging.INFO)

    def preHook(self):
        gevent.spawn(self.go)

    def go(self):
        while True:
            if self.logger_queue.qsize() > 0:
                entry = self.logger_queue.get()
                self.logger.log(entry[0], entry[1])
            else:
                gevent.sleep(1)

    def consume(self, event, *args, **kwargs):

        entry = "pid-{0} {1} {2}".format(event["data"][2], event["data"][3], event["data"][4])
        entry = self.colorize(entry, event["data"][0])

        self.logger_queue.put((self.levels[event["data"][0]], entry))

    def colorize(self, message, level):
        return self.colors[level]+message+"\x1B[0m"