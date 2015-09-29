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
import re

class XMLValidator(Actor):
    '''**A sample module which applies a provided XSD to an incoming event XML data**

    Parameters:

        - name (str):               The instance name.
        - xsd (str):                The XSD to validate the schema against

    '''

    def __init__(self, name, xsd=None, *args, **kwargs):
        Actor.__init__(self, name, *args, **kwargs)
        if xsd:
            self.schema = etree.XMLSchema(etree.XML(xsd))
        else:
            self.schema = None

        self.caller = "wsgi"

    def consume(self, event, *args, **kwargs):
        try:
            xml = etree.fromstring(event.data)

            if self.schema:
                self.schema.assertValid(xml)

            self.logger.info("Incoming XML successfully validated", event=event)
            self.send_event(event)
        except etree.DocumentInvalid as xml_errors:
            messages = xml_errors.error_log.filter_levels([1, 2])
            message = ''.join(["{0}\n".format(message.message) for message in messages ])
            self.process_error(event, message)
        except Exception as error:
            self.process_error(event, error)

    def process_error(self, event, message):
        event.get(self.caller, {}).update({'status': '400 Bad Request'})
        event.data = "Malformed Request (Invalid XML): {0}".format(message)
        self.logger.error("Error validating incoming XML: {0}".format(message), event=event)
        self.send_error(event)
