#!/usr/bin/env python
#
# -*- coding: utf-8 -*-
#
#  transformer.py
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
from compysition.event import XMLEvent
from compysition.errors import MalformedEventData

class XSD(Actor):
    '''**A simple actor which applies a provided XSD to an incoming event XML data. If no XSD is defined, it will validate XML format correctness**

    Parameters:

        name (str):
            | The instance name.
        xsd (str):
            | The XSD to validate the schema against

    Input:
        XMLEvent

    Output:
        XMLEvent

    '''

    input = XMLEvent
    output = XMLEvent

    def __init__(self, name, xsd=None, *args, **kwargs):
        super(XSD, self).__init__(name, *args, **kwargs)
        if xsd:
            self.schema = etree.XMLSchema(etree.XML(xsd))
        else:
            self.schema = None

    def consume(self, event, *args, **kwargs):
        try:

            if self.schema:
                self.schema.assertValid(event.data)
            self.logger.info("Incoming XML successfully validated", event=event)
            self.send_event(event)
        except etree.DocumentInvalid as xml_errors:
            messages = [message.message for message in xml_errors.error_log.filter_levels([1, 2])]
            self.process_error(messages, event)
        except Exception as error:
            self.process_error(error, event)

    def process_error(self, message, event):
        self.logger.error("Error validating incoming XML: {0}".format(message), event=event)
        raise MalformedEventData(message)
