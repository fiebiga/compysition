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

class EventAttributeModifier(Actor):

    '''**Adds or updates static information to an event**

    Parameters:

        - name  (str):          The instance name.
        - key   (str):          (Default: data) The key to set or update on the incoming event
        - value (Anything):     (Default: {})   The value to assign to the key
    '''

    def __init__(self, name, key='data', value={}, *args, **kwargs):
        Actor.__init__(self, name, *args, **kwargs)
        self.value = value
        if key is None:
            self.key = name
        else:
            self.key = key

    def consume(self, event, *args, **kwargs):
        setattr(event, self.key, self.value)
        self.send_event(event)
