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
from compysition.event import XMLEvent, JSONEvent
from compysition.errors import MalformedEventData

class EventAttributeModifier(Actor):

    '''**Adds or updates static information to an event**

    Parameters:

        - name  (str):          The instance name.
        - key   (str):          (Default: "data") The key to set or update on the incoming event. Can be a key-chain
                                    to access recursive dictionary elements using 'separator'
        - value (Anything):     (Default: {}) The value to assign to the key
        - separator (str)       (Default: "/") Delimiter for recursive key lookups
    '''

    def __init__(self, name, key='data', value={}, log_change=False, separator="/", *args, **kwargs):
        super(EventAttributeModifier, self).__init__(name, *args, **kwargs)
        self.value = value
        self.separator = separator
        if key is None:
            self.key = name
        else:
            self.key = key

        self.log_change = log_change

    def consume(self, event, *args, **kwargs):
        modify_value = self.get_modify_value(event)

        if self.log_change:
            self.logger.info("Changed event.{key} to {value}".format(key=self.key, value=modify_value), event=event)

        try:
            event = self.get_key_chain_value(event, modify_value)
            self.send_event(event)
        except Exception as err:
            raise MalformedEventData(err)

    def get_key_chain_value(self, event, value):
        #TODO: Redo this to not modify arrays
        keys = self.key.split(self.separator)
        event_key = keys.pop(0)
        if len(keys) == 0:
            event.set(event_key, value)
        else:
            current_step = event.get(event_key, None)
            if not current_step:
                current_step = {}
                event.set(event_key, current_step)

            try:
                while True:
                    try:
                        item = keys.pop(0)
                        if len(keys) > 0:
                            next_step = current_step[item]
                            current_step = next_step
                        else:
                            current_step[item] = value
                    except KeyError:
                        next_step = {} if len(keys) > 0 else value
                        current_step[item] = next_step
                        current_step = next_step
                    except IndexError:
                        break
            except Exception as err:
                self.logger.error("Unable to follow key chain. Ran into non-dict value of '{value}'".format(value=current_step), event=event)
                raise

        return event

    def get_modify_value(self, event):
        return self.value


class HTTPStatusModifier(EventAttributeModifier):

    def __init__(self, name, value=(200, "OK"), *args, **kwargs):
        super(HTTPStatusModifier, self).__init__(name, key="status", value=value, *args, **kwargs)


class XpathEventAttributeModifer(EventAttributeModifier):

    input = XMLEvent
    output = XMLEvent

    def get_modify_value(self, event):
        lookup = XPathLookup(event.data)
        xpath_lookup = lookup.lookup(self.value)

        if len(xpath_lookup) <= 0:
            value = None
        elif len(xpath_lookup) == 1:
            value = XpathEventAttributeModifer._parse_result_value(xpath_lookup[0])
        else:
            value = []
            for result in xpath_lookup:
                value.append(XpathEventAttributeModifer._parse_result_value(result))

        return value

    @staticmethod
    def _parse_result_value(result):
        value = None
        if isinstance(result, etree._ElementStringResult):
            value = result
        elif isinstance(result, (etree._Element, etree._ElementTree)):
            if len(result.getchildren()) > 0:

                value = etree.tostring(result)
            else:
                value = result.text

        return value

class HTTPXpathEventAttributeModifier(XpathEventAttributeModifer, HTTPStatusModifier):
    pass

class JSONEventAttributeModifier(EventAttributeModifier):

    input = JSONEvent
    output = JSONEvent

    def __init__(self, name, separator="/", *args, **kwargs):
        self.separator = separator
        super(JSONEventAttributeModifier, self).__init__(name, *args, **kwargs)

    def get_modify_value(self, event):
        data = event.data
        if isinstance(data, list):
            for datum in data:
                value = reduce(lambda acc, key: acc.get(key, {}), [datum] + self.value.split(self.separator))
                if value is not None:
                    break
        else:
            value = reduce(lambda acc, key: acc.get(key, {}), [data] + self.value.split(self.separator))

        if isinstance(value, dict) and len(value) == 0:
            value = None

        return value

class HTTPJSONAttributeModifier(JSONEventAttributeModifier, HTTPStatusModifier):
    pass