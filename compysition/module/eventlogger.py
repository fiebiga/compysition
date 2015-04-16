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

    '''

    def __init__(self, name, level=logging.INFO, logged_tags=['header', 'data'], prefix="", *args, **kwargs):
        Actor.__init__(self, name, *args, **kwargs)
        self.level = level
        self.prefix = prefix

    def consume(self, event, *args, **kwargs):
        message = self.prefix + ""
        for tag in logged_tags:
            message += str(getattr(event, tag, None))

        self.logger.log(self.level, message, event=event)
        self.send_event(event)