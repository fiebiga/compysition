#!/usr/bin/env python
#
# -*- coding: utf-8 -*-
#
#  header.py
#
#  Copyright 2014 Adam Fiebig <fiebig.adam@gmail.com>
#  Originally based on 'wishbone' project by smetj
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
#
#

from compysition import Actor
from lxml import etree
from util import XPathLookup

class EventAttributeModifier(Actor):

    '''**Adds or updates static information to an event**

    Parameters:

        - name  (str):          The instance name.
        - key   (str):          (Default: data) The key to set or update on the incoming event
        - value (Anything):     (Default: {})   The value to assign to the key
        - type  (static, xpath) (Default: static) Determines how the value is evaluated.
    '''

    def __init__(self, name, key='data', value={}, type="static", log_change=False, *args, **kwargs):
        Actor.__init__(self, name, *args, **kwargs)
        self.value = value
        if key is None:
            self.key = name
        else:
            self.key = key

        self.modify_event = getattr(self, "{0}_modify_event".format(type))
        self.log_change = log_change

    def consume(self, event, *args, **kwargs):
        event = self.modify_event(event)
        self.send_event(event)

    def static_modify_event(self, event):
        return self._do_modify_event(event, self.key, self.value)

    def xpath_modify_event(self, event):
        xml = etree.XML(event.data)
        lookup = XPathLookup(xml)
        xpath_lookup = lookup.lookup(self.value)

        if len(xpath_lookup) <= 0:
            value = None
        elif len(xpath_lookup) == 1:
            if isinstance(xpath_lookup[0], etree._ElementStringResult):
                value = xpath_lookup[0]
            else:
                value = xpath_lookup[0].text
        else:
            value = []
            for result in xpath_lookup:
                if isinstance(result, etree._ElementStringResult):
                    value.append = result
                else:
                    value.append = result.text

        return self._do_modify_event(event, self.key, value)

    def _do_modify_event(self, event, key, value):
        if self.log_change:
            self.logger.info("Changed event.{key} to {value}".format(key=self.key, value=value), event=event)

        event.set(key, value)
        return event
