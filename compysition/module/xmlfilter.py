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

class XMLFilter(Actor):
    '''**A module that forwards or discards an event based on the presence/absence of or value of 
    a given xml path for the event XML data**

    Parameters:

        - name (str):           The instance name.
        - xpath (str):          The xpath we wish to filter on. If this leads to an element and 'value' is also specified, the text of that element
                                    will be used to evaluate the provided value.
        - value (str):          (Default: None) The value to filter on for the given xpath. 
                                    If unspecified the event will be forwarded if the given xpath element exists at all.
        - blacklist (bool):     (Default: False) Whether or not to use a blacklist for a given 'value'. 
                                    Setting this value to true will cause the module discard the event only if the element value equals the value given.
                                    If no value is set, and blacklist=True, the XMLFilter will discard the event if the xpath element DOES exist

    event = {
        'data': '<some_xml_data></some_xml_data>'

        'header': {
            'wsgi': {
                'request_id': 1
            }
        }
    }
    '''
    
    def __init__(self, name, xpath, value=None, whitelist=True, *args, **kwargs):
        Actor.__init__(self, name, setupbasic=False)
        self.xpath = xpath
        self.value = value
        self.whitelist = whitelist
        if not isinstance(self.whitelist, bool):
            self.whitelist = True

    def consume(self, event, *args, **kwargs):
        xml = etree.fromstring(event['data'])
        xpath_lookup = xml.xpath(self.xpath)

        if len(xpath_lookup) < 1:
            if self.whitelist: # No results found on a 'whitelist' search means the event is discarded
                self.discard_event(event)
            else:
                self.forward_event(event)
        else:
            if self.value is None:
                if self.whitelist: # No filter value specified, so the existance of ANY results prompts forwarding
                    self.forward_event(event)
                else: # No filter value specified, so the xpath coming back with ANY results triggers the blacklist discard
                    self.discard_event(event)
            else:
                found_match = False
                for element in xpath_lookup:
                    if isinstance(element, etree._Element): # If xpath leads to an element, analyze the Element.text
                        compare_value = element.text
                        if compare_value is None:
                            compare_value = ''
                    else:
                        compare_value = element

                    if compare_value == self.value:
                        found_match = True
                        break

                if not found_match and self.whitelist:
                    self.discard_event(event)
                elif found_match and not self.whitelist:
                    self.discard_event(event)
                else:
                    self.forward_event(event)

                
    def forward_event(self, event):
        print("Forwarding event")
        self.send_event(event)

    def discard_event(self, event):
        print("Discarding event")
        del event
