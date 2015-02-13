#!/usr/bin/env python
#
# -*- coding: utf-8 -*-
#
#  header.py
#
#  Copyright 2014 Adam Fiebig <fiebig.adam@gmail.com>
#  Originally based on 'wishbone' project by smetj
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


class Data(Actor):

    '''**Adds information to event data.**'''

    def __init__(self, name, key=None, data={}, *args, **kwargs):
        Actor.__init__(self, name, *args, **kwargs)
        self.data = data
        self.key = key

    def consume(self, event, *args, **kwargs):
        event = self.update_data(event)
        self.send_event(event)

    def update_data(self, event):
        if self.key:
            event["data"][self.key] = self.data
        else:
            event["data"] = self.data

        return event
