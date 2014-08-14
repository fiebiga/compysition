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
    a given xml path (or xslt transform) for the event XML data**

    Parameters:

        - name (str):           The instance name.
        - xpath (str):          The xpath we wish to filter on. If this leads to an element and 'value' is also specified, the text of that element
                                    will be used to evaluate the provided value.
        - xslt_filepath (str):  (Default: None) The path of the xslt to apply to any given received XML PRIOR to applying the XPath lookup to test.
                                    The XML sent in the outboxes is NOT transformed.
        - value (str):          (Default: None) The value to filter on for the given xpath. 
                                    If unspecified the event will be forwarded if the given xpath element exists at all.
        - whitelist (bool):     (Default: False) Whether or not to use a whitelist for a given 'value'. 
                                    Setting this value to true will cause the module discard the event only if the element value equals the value given.
                                    If no value is set, and blacklist=True, the XMLFilter will discard the event if the xpath element DOES exist

        - filter_type (str):    (Default: delete) What to do with the filtered event. Possible actions are as follows:
                                        - delete: Deletes the event completely
                                        - output: Outputs the event to 'error' queues connected to the module
                                        - log   : Output the text of an event to a log message, using the given log_level
                                        
        - log_level (int):      (Default: 3) Only taken into account 

        - delete_event (bool):  (Default: True) If true, the module will delete a filtered event. If False, it will attempt to send the event on any connected
                                    error queues.

    event = {
        'data': '<some_xml_data></some_xml_data>'

        'header': {
            'wsgi': {
                'request_id': 1
            }
        }
    }
    '''
    
    def __init__(self, name, xpath, xslt_filepath=None, value=None, whitelist=True, filter_type="delete", log_level=3, *args, **kwargs):
        Actor.__init__(self, name, *args, **kwargs)
        self.xpath = xpath
        self.value = value
        self.whitelist = whitelist
        self.filter_type = filter_type
        self.log_level = log_level

        if not isinstance(self.whitelist, bool):
            self.whitelist = True

        if xslt_filepath is not None:
            self.template = self.load_template(xslt_filepath)
        else:
            self.template = None

    def consume(self, event, *args, **kwargs):

        if self.template is None:
            xml = etree.fromstring(event['data'])
        else:
            xml = self.template(etree.fromstring(event['data']))

        if etree.tostring(xml) is None:
            xpath_lookup = []
        else:
            xpath_lookup = xml.xpath(self.xpath)

        if len(xpath_lookup) < 1:
            if self.whitelist: # No results found on a 'whitelist' search means the event is discarded
                self.filter_event(event, message="No results for xpath {0} found in event data".format(self.xpath))
            else:
                self.forward_event(event)
        else:
            if self.value is None:
                if self.whitelist: # No filter value specified, so the existance of ANY results prompts forwarding
                    self.forward_event(event)
                else: # No filter value specified, so the xpath coming back with ANY results triggers the blacklist discard
                    self.filter_event(event, message=', '.join([ element.text for element in xpath_lookup ]))
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
                    self.filter_event(event, message="Value '{0}' not found for xpath {1} found in event data. Found match was {2}".format(self.value, 
                                                                                                                                           self.xpath,
                                                                                                                                           ', '.join([ element.text for element in xpath_lookup ])))
                elif found_match and not self.whitelist:
                    self.filter_event(event, message="Value '{0}' found for xpath {1} found in event data".format(self.value, self.xpath))
                else:
                    self.forward_event(event)

                
    def forward_event(self, event):
        self.logging.info("XMLFilter {0} Forwarding event".format(self.name))
        self.send_event(event)

    def filter_event(self, event, message=None, *args, **kwargs):
        self.logging.info("XMLFilter {0} Filtering event".format(self.name))

        if self.filter_type == "delete":
            del event
        elif self.filter_type == "output":
            self.send_error(event)
        elif self.filter_type == "log":
            if message is not None:
                self.logging.error(message)
            else:
                self.logging.error(event["data"])
            del event

    def load_template(self, path):
        try:
            return etree.XSLT(etree.parse(path))
        except Exception as e:
            self.logging.error("Unable to load XSLT at {0}:{1}".format(path, e))
            return None

