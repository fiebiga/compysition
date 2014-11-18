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
from util import MatchedEvent

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
    
    def __init__(self, name, *args, **kwargs):
        Actor.__init__(self, name, *args, **kwargs)
        self.events = {}
        self.key = kwargs.get('key', self.name)

    def consume(self, event, *args, **kwargs):
        request_id = event['header']['event_id']
        inbox_origin = kwargs.get('origin', None)
        waiting_event = self.events.get(request_id, None)
        try:
            if waiting_event:
                waiting_event.report_inbox(inbox_origin, event['data'])
                if waiting_event.all_inboxes_reported():
                    event['data'] = waiting_event.get_aggregate_xml()
                    self.send_event(event)
                    del self.events[request_id]
            else:
                inbound_queues = []
                for queue in self.pool.listInboundQueues(names=True):
                    inbound_queues.append(queue)

                self.events[request_id] = MatchedEvent(self.key, inbound_queues)
                self.events.get(request_id).report_inbox(inbox_origin, event['data'])
        except Exception as error:
            self.logger.warn("Could not process incoming event: {0}".format(error), event_id=event['header']['event_id'])

