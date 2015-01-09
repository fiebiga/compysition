#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  stdout.py
#
#  Copyright 2013 Jelle Smet <smetj@gmail.com>
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

    '''**Prints incoming events to logger.**

    Simple module that logs the current event contents

    '''

    def __init__(self, name, level=logging.INFO, log_header=True, log_data=True, prefix="", *args, **kwargs):
        Actor.__init__(self, name, *args, **kwargs)
        self.log_data = log_data
        self.log_header = log_header
        self.level = level
        self.prefix = prefix

    def consume(self, event, *args, **kwargs):
        message = self.prefix + ""
        if self.log_header:
            message += "Event header: {header}\n".format(header=event['header'])

        if self.log_data:
            message += "Event data: {data}".format(data=event['data'])

        self.logger.log(self.level, message, event_id=event['header']['event_id'])
        self.send_event(event)