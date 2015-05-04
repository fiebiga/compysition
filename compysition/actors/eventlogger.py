#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  stdout.py
#
#  Copyright 2015 Adam Fiebig <fiebig.adam@gmail.com>
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
import logging

class EventLogger(Actor):

    '''**Sends incoming events to logger.**

    Simple module that logs the current event contents
        - level (logging module level)      (Default: logging.INFO) The level that his module will log the incoming event
        - logged_tags ([string])            (Default: ['data']) The event attributes to log. Ignored if log_full_event is True
        - log_full_event (bool)             (Default: True) Whether or not to log the full value of event.to_string() to the logger
        - prefix (str)                      (Default: "") The prefix to prepend to the logged event string

    '''

    def __init__(self, name, level=logging.INFO, logged_tags=['data'], log_full_event=True, prefix="", *args, **kwargs):
        Actor.__init__(self, name, *args, **kwargs)
        self.level = level
        self.prefix = prefix
        self.logged_tags = logged_tags
        self.log_full_event = log_full_event

    def consume(self, event, *args, **kwargs):
        message = self.prefix + ""
        if self.log_full_event:
            message += event.to_string()
        else:
            for tag in self.logged_tags:
                message += str(getattr(event, tag, None))

        self.logger.log(self.level, message, event=event)
        self.send_event(event)