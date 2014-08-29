#!/usr/bin/env python
#
# -*- coding: utf-8 -*-
#
#  loglevelfilter.py
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

from compysition import Actor
from time import strftime, localtime
from time import time
from configobj import ConfigObj
import logging

class LogLevelFilter(Actor):
    '''**Filters Compysition log events for use by non-traditional logging modules (ones that don't implement a pythonic logger to
    inherently filter, and ones that may initiate more complex logic chains after the logging module)**

        name(str)       :   The name of the module.

        max_level(bool) :   The maximum log level to show.
                            Default: logging.INFO
    '''

    def __init__(self, name, max_level=logging.INFO, config_file=None, *args, **kwargs):
        Actor.__init__(self, name, *args, **kwargs)
        self.name=name

        if config_file is None:
            self.max_level=max_level
        else:
            try:
                config = ConfigObj(config_file)
                logging_opts = config.get('logging')
                self.max_level = getattr(logging, logging_opts['level'].upper(), None)
            except Exception as error:
                self.logging.error("Unable to load logging level from logging.conf. Using default values: Error is {0}".format(error))
                self.max_level=max_level

    def consume(self, event, *args, **kwargs):
        if event["data"][0] >= self.max_level:
            self.send_event(event)
        else:
            del event