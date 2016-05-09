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

from lxml import etree
import re
from util import XPathLookup
import json

"""
TODO: These util classes will replace eventrouter filters, and be designed for use across any actor who needs to match
an event for any reason
"""


class EventFilter(object):
    '''
    **A filter class to be used as a constructor argument for the EventRouter class. This class contains information about event
    match information and the outbox result of a successful match. Uses either regex match or literal equivalents**

    Paramters:
        - value_regexes ([str] or str):         The value(s) that will cause this filter to match. This is evaluated as a regex
        - outbox_names ([str] or str):          The desired outbox that a positive filter match should place the event on
        - event_scope (tuple(str)):             The string address of the location of the string value to check against this filter in an event, provided as a tuple chain
                                                    The scope step can either be a dictionary key or an object property
                                                    e.g. event.service == ("service",)
                                                    e.g. event.data == ("data",)
                                                    e.g. event.header['http'] == ("header", "http")
                                                    e.g. event.header.someotherobj == ("header", "someotherobj")
        - next_filter(str):                     (Default: None) This grants the ability to create complex matching scenarios. "If X = match, then check Y"
                                                    A positive match on this filter (X), will trigger another check on filter (Y), and then use the filter configured on filter Y
                                                    in the event of a positive match

    '''

    def __init__(self, value_regexes, outbox_names, event_scope=("data",), next_filter=None, *args, **kwargs):
        self._validate_scope_definition(event_scope)
        if not isinstance(value_regexes, list):
            value_regexes = [value_regexes]

        if not isinstance(outbox_names, list):
            outbox_names = [outbox_names]

        self.value_regexes = self.parse_value_regexes(value_regexes)
        self.outbox_names = outbox_names
        self.outboxes = []  # To be filled and defined later when the EventRouter initializes outboxes
        self.next_filter = self.set_next_filter(next_filter)

    def parse_value_regexes(self, value_regexes):
        return [re.compile(value_regex) for value_regex in value_regexes]

    def _validate_scope_definition(self, event_scope):
        if isinstance(event_scope, tuple):
            self.event_scope = event_scope
        elif isinstance(event_scope, str):
            self.event_scope = (event_scope,)
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
        values = self._get_value(event, self.event_scope)
        try:
            while True:
                value = next(values)
                if value is not None:
                    for value_regex in self.value_regexes:
                        if value_regex.search(str(value)):
                            if self.next_filter:
                                return self.next_filter.matches(event)
                            else:
                                return True
        except StopIteration:
            pass
        except Exception as err:
            raise Exception(
                "Error in attempting to apply regex patterns {0} to {1}: {2}".format(self.value_regexes, values, err))

        return False

    def _get_value(self, event, event_scope, *args, **kwargs):
        """
        This method iterates through the self.event_scope tuple in a series of getattr or get calls,
        depending on if the event in the scope step is a dict or an object. More supported types may be added in the future
        If the chain fails at any point, a None is returned
        """
        try:
            current_step = event
            for scope_step in event_scope:
                if isinstance(current_step, dict):
                    current_step = current_step.get(scope_step, None)
                elif isinstance(current_step, object):
                    current_step = getattr(current_step, scope_step, None)
        except Exception as err:
            current_step = None

        yield current_step


class EventXMLFilter(EventFilter):
    '''
    **A filter class for the EventRouter module that will additionally use xpath lookup values to apply a regex comparison**
    '''

    def __init__(self, xpath, value_regexes, outbox_names, xslt=None, *args, **kwargs):
        super(EventXMLFilter, self).__init__(value_regexes, outbox_names, *args, **kwargs)
        self.xpath = xpath

        if xslt:
            self.xslt = etree.XSLT(etree.XML(xslt))
        else:
            self.xslt = None

    def _get_value(self, event, event_scope, xpath=None, *args, **kwargs):
        value = next(super(EventXMLFilter, self)._get_value(event, event_scope))
        xpath = xpath or self.xpath
        try:
            xml = etree.XML(value)

            if self.xslt:
                xml = self.xslt(xml)

            lookup = XPathLookup(xml)
            xpath_lookup = lookup.lookup(xpath)

            if len(xpath_lookup) == 0:
                yield None
            else:
                for result in xpath_lookup:
                    yield self._parse_xpath_result(result)
        except Exception as err:
            yield None

    def _parse_xpath_result(self, lookup_result):
        try:
            if isinstance(lookup_result, etree._ElementStringResult):
                value = lookup_result
            else:
                value = lookup_result.text

            # We want to be able to mimic the behavior of "If this tag exists at all, even if it's blank, forward it"
            if value is None:
                value = ""
        except Exception as err:
            value = None

        return value


class EventXMLXpathsFilter(EventXMLFilter):

    def __init__(self, xpath, value_xpath, outbox_names, *args, **kwargs):
        super(EventXMLXpathsFilter, self).__init__(xpath, [], outbox_names, *args, **kwargs)
        self.value_xpath = value_xpath

    def matches(self, event):
        new_regexes = []
        regex_values = self._get_value(event, self.event_scope, xpath=self.value_xpath)
        try:
            while True:
                regex = next(regex_values)
                if regex is not None:
                    new_regexes.append(regex)
        except StopIteration:
            pass

        self.value_regexes = self.parse_value_regexes(new_regexes)
        return super(EventXMLXpathsFilter, self).matches(event)


class EventJSONFilter(EventFilter):
    '''
    **A filter class for the EventRouter module that will additionally use json lookup values to apply a regex comparison**
    '''

    def __init__(self, json_scope, *args, **kwargs):
        super(EventJSONFilter, self).__init__(*args, **kwargs)
        self.json_scope = json_scope

    def _get_value(self, event, event_scope):
        values = next(super(EventJSONFilter, self)._get_value(event, self.event_scope))
        try:

            if not isinstance(values, dict) and isinstance(values, str):
                values = json.loads(values)

            if isinstance(values, list):
                for value in values:
                    json_value = next(super(EventJSONFilter, self)._get_value(value, self.json_scope))
                    yield json_value
            else:
                json_value = next(super(EventJSONFilter, self)._get_value(values, self.json_scope))
                yield json_value
        except Exception as err:
            yield None


