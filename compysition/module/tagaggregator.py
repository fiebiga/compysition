#!/usr/bin/env python
#
# -*- coding: utf-8 -*-
#
#  tagaggregator.py
#
#  Copyright 2014 Adam Fiebig <fiebig.adam@gmail.com>
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

from compysition import Actor

class TagAggregator(Actor):
    '''**Simple module which aggregates all existing tags under event['data'] together as event['data'].
    e.g. event['data']['tagone'] and event['data']['tagtwo'] become event['data'], where data equals event['data']['tagone'] + event['data']['tagone']**

    Parameters:

        - name (str):       The instance name.

    '''

    def __init__(self, name, *args, **kwargs):
        Actor.__init__(self, name, *args, **kwargs)

    def consume(self, event, *args, **kwargs):
        new_data = ""
        if isinstance(event['data'], dict):
            for key in event['data']:
                data = event['data'].get(key)
                if data is not None:
                    new_data += data

            if new_data != "":
                event['data'] = new_data

        self.send_event(event)