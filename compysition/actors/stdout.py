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
import sys
import datetime

class STDOUT(Actor):

    '''**Prints incoming events to STDOUT.**

    Prints incoming events to STDOUT. When <complete> is True,
    the complete event including headers is printed to STDOUT.


    '''

    def __init__(self, name, complete=False, prefix="", timestamp=False, *args, **kwargs):
        super(STDOUT, self).__init__(name, *args, **kwargs)
        self.complete = complete
        self.prefix = prefix
        self.timestamp = timestamp

    def consume(self, event, *args, **kwargs):
        if self.complete:
            data = "{0}{1}".format(self.prefix, event)
        else:
            data = "{0}{1}".format(self.prefix, event.data_string())

        if self.timestamp:
            data = "[{0}] {1}".format(datetime.datetime.now(), data)

        print(data)
        sys.stdout.flush()
        self.send_event(event)
