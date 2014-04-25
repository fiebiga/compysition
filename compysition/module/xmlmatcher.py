#!/usr/bin/env python
#
# -*- coding: utf-8 -*-
#
#  xmlaggregator.py
#
#  Copyright 2014 James Hulett <james.hulett@cuanswers.com>,
#        Adam Fiebig <fiebig.adam@gmail.com>
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
from copy import deepcopy

class XMLMatcher(Actor):
    '''**Holds event data until a matching request id, then appends the match to the specified xpath of the XML in the data.**

    Parameters:

        - name (str):       The instance name.

    Queues:

        - inbox:    Incoming events.
        - outbox:   Outgoing events.

    event = {
        'data': '<event><id>1</id><data>data for 1</data></event>'

        'header': {
            'wsgi': {
                'request_id': 1
            }
        }
    }
    '''
    
    def __init__(self, name, xpath=None, *args, **kwargs):
        Actor.__init__(self, name)
        self.xpath = xpath
        self.events = {}
        self.key = kwargs.get('key', self.name)
        self.logging.info("Initialized with: {}".format(self.xpath))

    def consume(self, event, *args, **kwargs):
        #pdb.set_trace()
        request_id = event['header']['wsgi']['request_id']
        waiting_event = self.events.get(request_id, None)
        if waiting_event:
            print("Found Waiting Event")
            if self.xpath is not None:
                xml = etree.fromstring(str(waiting_event['data']['XML']))
                #xml.xpath(self.xpath).append(etree.XML(str(event['data']['XML'])))
                xml.append(etree.XML(str(event['data']['XML'])))
                event['data'] = etree.tostring(xml, pretty_print=True)
            else:
                xml = etree.fromstring(str(waiting_event['data']['XML']))
                second_xml = etree.fromstring(str(event['data']['XML']))
                new_xml = etree.tostring(xml) + etree.tostring(second_xml)
                event['data'] = new_xml
            print event['data']
            self.send_event(event)
        else:
            print "Sending event {0} to outbox.".format(request_id)
            self.events.update({request_id: deepcopy(event)})