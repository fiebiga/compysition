#!/usr/bin/env python
#
# -*- coding: utf-8 -*-
#
#  xmlaggregator.py
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
from lxml import etree
import pdb

class XMLAggregator(Actor):
    '''**Sample module which reverses incoming events.**

    Parameters:

        - name (str):       The instance name.

    Queues:

        - inbox:    Incoming events.
        - outbox:   Outgoing events.
    '''
    
    def __init__(self, name, *args, **kwargs):
        Actor.__init__(self, name, *args, **kwargs)
        self.subjects = list(args)
        self.root = self.subjects.pop()
        self.logging.info("Initialized with: {}".format(self.subjects))

    def consume(self, event, *args, **kwargs):
        #pdb.set_trace()
        root_tag = etree.XML(event['data'][self.root])
        for subject in self.subjects:
            root_tag.append(etree.XML(subject))
        event['data'] = etree.tostring(root_tag)
        self.queuepool.outbox.put(event)