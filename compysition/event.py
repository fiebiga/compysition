#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  default.py
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
#
from uuid import uuid4 as uuid
from ast import literal_eval
"""
Compysition event is created and passed by reference among modules
"""

DEFAULT_EVENT_SERVICE="default"

class CompysitionEvent(object):

    """
    Anatomy of an event:
        - header:
            - event_id: The unique and functionally immutable ID for this new event
            - meta_id:  The ID associated with other unique event data flows. This ID is used in logging
            - service:  (default: default) Used for compatability with the ZeroMQ MajorDomo configuration. Scope this to specific types of interproces routing
        - data:
            <The data passed and worked on from event to event. Mutable and variable>
    """

    def __init__(self, meta_id=None, service=None, data=None, header=None):
        self.event_id = uuid().get_hex()
        self.meta_id = meta_id or self.event_id
        self.service = service or DEFAULT_EVENT_SERVICE
        self.header = header
        self.data = data

    def to_string(self):
        return_dict = {}
        keys = self.__dict__.keys()
        for key in keys:
            return_dict[key] = b"{0}".format(self.__dict__[key])

        return return_dict

    def from_string(self, string_value):
        value_dict = literal_eval(string_value)
        keys = value_dict.keys()
        for key in keys:
            setattr(self, key, value_dict[key])

if __name__ == "__main__":
    """
    Event Test execution. Will be removed or migrated to a test suite
    """
    test = CompysitionEvent()
    str_value = test.to_string()
    print str_value
    test_two = CompysitionEvent()
    print test_two.from_string(str_value)