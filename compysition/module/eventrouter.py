#!/usr/bin/env python
#
# -*- coding: utf-8 -*-
#
#  xmlfilter.py
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
from lxml import etree
import re
from ast import literal_eval
from compysition.errors import QueueMissing
import traceback
from util import XPathLookup

class EventRouter(Actor):
    '''**A module that filters incoming events to specific outboxes depending the input "Filter" args**

    Parameters:

        - name (str):                               The instance name.
        - routing_filters ([EventFilter]):          (Default: []) Array of "EventFilter" objects. Defaults to [] to allow for an implementing process to set these via the "set_filter" method
        - type (str):                               (Default: whitelist) Either "whitelist" or "blacklist" -  If an event fails to match any defined filters, a "whitelist" EventRouter
                                                        will purge the event entirely. A "blacklist" EventRouter will use the provided 'default_outbox' parameter to forward the event
        - default_outbox_regexes (str or [str]):    (Default: .*) Only used for a "blacklist" EventRouter. If an EventRouter is "blacklist" and fails to match any provided filters,
                                                        the event will be output to all connected outboxes that do not have an explicit filter condition declared, that match the 
                                                        regex(es) provided

    '''
    
    def __init__(self, name, routing_filters=[], type="whitelist", default_outbox_regexes=[".*"], *args, **kwargs):
        Actor.__init__(self, name, *args, **kwargs)
        self.filters = []
        self.default_outbox_regexes = default_outbox_regexes
        self.default_outboxes = []          
        for filter in routing_filters:
            self.set_filter(filter)

        if type is "whitelist":
            self.whitelist = True
        else:
            self.whitelist = False

    def preHook(self):
        # We only need to initialized default outboxes if this is a 'blacklist' router
        if not self.whitelist:
            self._initialize_default_outboxes()

    def _initialize_default_outboxes(self):
        # Check to see which outboxes are 'filtered' outboxes, as we do not want to include these in a "default" outbox list
        filtered_outboxes = set()
        for filter in self.filters:
            for outbox in filter.outboxes:
                filtered_outboxes.add(outbox)

        # Determine default outboxes for a 'blacklist' routing scenario
        for default_outbox_regex in self.default_outbox_regexes:
            outbox_regex = re.compile(default_outbox_regex)
            for outbox in self.pool.listOutboundQueues():
                if outbox.name not in filtered_outboxes:
                    if outbox_regex.search(outbox.name):
                        self.default_outboxes.append(outbox)

    def consume(self, event, *args, **kwargs):
        matched = False
        for filter in self.filters:
            if filter.matches(event):
                matched = True
                for outbox in filter.outboxes:
                    try:
                        filter_queue = self.pool.getQueue(outbox)
                        self.send_event(event, queue=filter_queue)
                        self.logger.debug("EventFilter matched for outbound queue '{queue_name}'. Event successfully forwarded".format(queue_name=outbox), 
                                          event_id=event['header']['event_id'])
                    except QueueMissing as err:
                        self.logger.error("EventFilter to outbound queue '{queue_name}' was matched, but no queue by that name was connected. Event will be discarded".format(queue_name=outbox), 
                                          event_id=event['header']['event_id'])

        if not matched:
            if not self.whitelist:
                if len(self.default_outboxes) > 0:
                    for default_outbox in self.default_outboxes:
                            self.send_event(event, queue=default_outbox)
                            self.logger.debug("No EventFilters matched for event. Event forwarded on default outbox '{queue_name}'".format(queue_name=default_outbox), 
                                              event_id=event['header']['event_id'])
                else:
                    self.logger.error("No EventFilters matched for event and no default queues are connected. Event has been discarded", event_id=event['header']['event_id'])
            else:
                self.logger.debug("No EventFilters matched for event. Event has been discarded", event_id=event['header']['event_id'])

    def set_filter(self, filter):
        if isinstance(filter, EventFilter):
            self.filters.append(filter)
        else:
            raise TypeError("The provided filter is not a valid EventFilter type")

class EventFilter(object):
    '''
    **A filter class to be used as a constructor argument for the EventRouter class. This class contains information about event
    match information and the outbox result of a successful match. Uses either regex match or literal equivalents**
    
    Paramters:
        - value_regexes ([str] or str):         The value(s) that will cause this filter to match. This is evaluated as a regex
        - outboxes ([str] or str):              The desired outbox that a positive filter match should place the event on
        - event_scope (tuple(str)):             The string address of the location of the string value to check against this filter in an event, provided as a tuple chain
                                                    e.g. 'event["header"]["service"] == ("header", "service")'
                                                    e.g. 'event["data"] == ("data")'
        - next_filter(str):                     (Default: None) This grants the ability to create complex matching scenarios. "If X = match, then check Y"
                                                    A positive match on this filter (X), will trigger another check on filter (Y), and then use the filter configured on filter Y
                                                    in the event of a positive match

    '''

    def __init__(self, value_regexes, outboxes, event_scope=("data",), next_filter=None, *args, **kwargs):
        super(EventFilter, self).__init__(*args, **kwargs)
        self._validate_scope_definition(event_scope)
        if not isinstance(value_regexes, list):
            value_regexes = [value_regexes]

        if not isinstance(outboxes, list):
            outboxes = [outboxes]

        self.value_regexes = [re.compile(value_regex) for value_regex in value_regexes]
        self.outboxes = outboxes
        self.next_filter = self.set_next_filter(next_filter)
        

    def _validate_scope_definition(self, event_scope):
        if isinstance(event_scope, tuple):
            self.event_scope = event_scope
        elif isinstance(event_scope, str):
            self.event_scope = (event_scope, )
        else:
            raise TypeError("The defined event_scope must be either type str or tuple(str)")

    def set_next_filter(self, filter):
        if filter is not None:
            if isinstance(filter, EventFilter):
                self.next_filter = filter
            else:
                raise TypeError("The provided filter is not a valid EventFilter type")
        else:
            self.next_filter = None

    def matches(self, event):
        value = self._get_value(event)
        try:
            if value is not None:
                for value_regex in self.value_regexes:
                    if value_regex.search(str(value)):
                        if self.next_filter:
                            return self.next_filter.matches(event)
                        else:
                            return True
        except Exception as err:
            self.logger.error("Error in attempting to apply regex patterns {0} to {1}: {2}".format(self.value_regexes, value, err), event_id=event['header']['event_id'])

        return False

    def _get_value(self, event):
        """
        This method iterates through the self.event_scope tuple in a series of get() calls on the event,
        returning a None if the provided chain fails
        """
        try:
            current_step = event
            for scope_step in self.event_scope:
                current_step = current_step.get(scope_step, None)
        except Exception as err:
            current_step = None

        return current_step

class EventXMLFilter(EventFilter):
    '''
    **A filter class for the EventRouter module that will additionally use xpath lookup values to apply a regex comparison**
    '''
    
    def __init__(self, xpath, value_regexes, outboxes, xslt=None, *args, **kwargs):
        super(EventXMLFilter, self).__init__(value_regexes, outboxes, *args, **kwargs)
        self.xpath = xpath

        if xslt:
            self.xslt = etree.XSLT(etree.XML(xslt))
        else:
            self.xslt = None

    def _get_value(self, event):
        value = super(EventXMLFilter, self)._get_value(event)

        xml = etree.XML(value)

        if self.xslt:
            xml = self.xslt(xml)

        lookup = XPathLookup(xml)
        xpath_lookup = lookup.lookup(self.xpath)

        if len(xpath_lookup) == 0:
            value = None
        else:
            value = xpath_lookup[0].text

            # We want to be able to mimic the behavior of "If this tag exists at all, even if it's blank, forward it"
            if value is None:
                value = ""

        return value

