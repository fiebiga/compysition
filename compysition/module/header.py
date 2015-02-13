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


class Header(Actor):

    '''**Adds information to event headers.**


    Parameters:

        - name(str)
           |  The name of the module.

        - key(str) (Default: name)
           |  The header key to store the information.

        - header(dict)({})
           |  The data to store.

    '''

    def __init__(self, name, key=None, header={}, *args, **kwargs):
        Actor.__init__(self, name, *args, **kwargs)
        self.header = header

        if key is None:
            self.key = name
        else:
            self.key = key

    def consume(self, event, *args, **kwargs):
        event = self.update_header_dict(event)
        self.send_event(event)

    def update_header_dict(self, event):
        event["header"][self.key] = self.header
        return event
