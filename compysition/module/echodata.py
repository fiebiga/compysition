#!/usr/bin/env python
#
# -*- coding: utf-8 -*-
#
#  echodata.py
#
#  Copyright 2014 James Hulett <james.hulett@cuanswers.com>
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
from pprint import pformat
import json

class EchoData(Actor):
    '''**Sample module which reverses incoming events.**

    Parameters:

        - name (str):       The instance name.

    Queues:

        - inbox:    Incoming events.
        - outbox:   Outgoing events.
    '''

    def __init__(self, name, capitalize=False, key=None, *args, **kwargs):
        Actor.__init__(self, name, *args, **kwargs)
        self.capitalize=capitalize
        self.logging.info("Initialized")
        self.key = key or self.name

    def consume(self, event, *args, **kwargs):
        self.logging.info("Got request with headers: {0}".format(event['header']))
        self.logging.info("Got request with data: {0}".format(event['data']))
        xml = event['data']['XML']
        xml += "** Touched by {} ***".format(self.name)
        event['data'] = xml
        self.logging.info("Replying to request: {0}".format(event['data']))
        self.queuepool.outbox.put(event)