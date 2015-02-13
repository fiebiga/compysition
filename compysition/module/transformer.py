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
from pprint import pformat
from lxml import etree
import os

class Transformer(Actor):
    '''**A sample module which applies a provided XSLT to an incoming event XML data**

    Parameters:

        - name (str):               The instance name.
        - xslt_path (str):          The path to the xslt to apply
        - add_to_header (Boolean):  If this option is specified, the results of the transform will be added to the
                                        data header instead of replacing the event['data'] field

    Queues:

        - inbox:    Incoming events.
        - outbox:   Outgoing events.
    '''

    def __init__(self, name, xslt=None, xslt_path=None, add_to_header=False, *args, **kwargs):
        Actor.__init__(self, name, *args, **kwargs)
        self.logger.info("Initialized")
        self.subjects = args or None
        self.add_to_header = add_to_header or kwargs.get('add_to_header', False) or False
        self.key = kwargs.get('key', None) or self.name
        self.caller = 'wsgi'

        if xslt is None:
            if xslt_path is not None:
                self.template = self.load_template(xslt_path)
            else:
                raise Exception("No xslt defined, you must define a transform using xslt or xslt_path")
        else:
            self.template = etree.XSLT(etree.XML(xslt))


    def consume(self, event, *args, **kwargs):
        try:
            original_xml = etree.fromstring(event['data'])
            transformed_xml = self.transform(original_xml)
            event['data'] = etree.tostring(transformed_xml)
            self.logger.info("Successfully transformed XML", event_id=event['header']['event_id'])
            self.send_event(event)
        except KeyError:
            event['header'].get(self.caller, {}).update({'status': '400 Bad Request'})
            event['data'] = "Malformed Request"
            self.send_error(event)

    def transform(self, etree_element):
        return self.template(etree_element)

    def load_template(self, path):
        try:
            return etree.XSLT(etree.parse(path))
        except Exception as e:
            self.logger.error("Unable to load XSLT at {0}:{1}".format(path, e))