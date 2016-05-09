#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  default.py
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
#
from uuid import uuid4 as uuid
from .errors import *
import json
from lxml import etree
import xmltodict
from collections import OrderedDict, defaultdict
from xml.parsers import expat
import traceback
from datetime import datetime
from xml.sax.saxutils import XMLGenerator
import re
from copy import deepcopy

"""
Compysition event is created and passed by reference among actors
"""

DEFAULT_EVENT_SERVICE = "default"
DEFAULT = object()


def internal_xmlify(_json):
    if isinstance(_json, list) or len(_json) > 1:
        _json = {"jsonified_envelope": _json}

    if isinstance(_json[_json.keys()[0]], list):
        _json = {"jsonified_envelope": _json}

    return _json


def remove_internal_xmlify(_json):
    if len(_json) == 1 and isinstance(_json, dict):
        first_key = _json.keys()[0]
        if first_key == "jsonified_envelope":
            _json = _json[first_key]

    return _json


class UnescapedDictXMLGenerator(XMLGenerator):
    """
    Simple class designed to enable the use of an unescaped functionality
    in the event that dictionary value data is already XML
    """

    def characters(self, content):
        try:
            if content.lstrip().startswith("<"):
                etree.fromstring(content)
                self._write(content)
            else:
                XMLGenerator.characters(self, content)
        except:
            XMLGenerator.characters(self, content)

setattr(xmltodict, "XMLGenerator", UnescapedDictXMLGenerator)
_XML_TYPES = [etree._Element, etree._ElementTree, etree._XSLTResultTree]
_JSON_TYPES = [dict, list, OrderedDict]


class DataFormatInterface(object):
    """
    Interface used as an identifier for data format classes. Used during event type conversion
    To create a new datatype, simply implement this interface on the newly created class
    """
    pass


class Event(object):

    """
    Anatomy of an event:
        - event_id: The unique and functionally immutable ID for this new event
        - meta_id:  The ID associated with other unique event data flows. This ID is used in logging
        - service:  (default: default) Used for compatability with the ZeroMQ MajorDomo configuration. Scope this to specific types of interprocess routing
        - data:     <The data passed and worked on from event to event. Mutable and variable>
        - kwargs:   All other kwargs passed upon Event instantiation will be added to the event dictionary

    """

    _content_type = "text/plain"

    def __init__(self, meta_id=None, service=None, data=None, *args, **kwargs):
        self.event_id = uuid().get_hex()
        self.meta_id = meta_id if meta_id else self.event_id
        self.service = service or DEFAULT_EVENT_SERVICE
        self.data = data
        self.error = None
        self.__dict__.update(kwargs)

    def set(self, key, value):
        try:
            setattr(self, key, value)
            return True
        except:
            return False

    def get(self, key, default=DEFAULT):
        val = getattr(self, key, default)
        if val is DEFAULT:
            raise AttributeError("Event property '{property}' does not exist".format(property=key))
        return val

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        try:
            self._data = self.conversion_methods[data.__class__](data)
        except Exception as err:
            raise InvalidEventDataModification("Data of type '{_type}' was not valid for event type {cls}: {err}".format(_type=type(data), cls=self.__class__, err=traceback.format_exc()))

    @property
    def event_id(self):
        return self._event_id

    @event_id.setter
    def event_id(self, event_id):
        if self.get("_event_id", None):
            raise InvalidEventDataModification("Cannot alter event_id once it has been set. A new event must be created")
        else:
            self._event_id = event_id

    def get_properties(self):
        """
        Gets a dictionary of all event properties except for event.data
        Useful when event data is too large to copy in a performant manner
        """
        return {k: v for k, v in self.__dict__.items() if k != "data" and k != "_data"}

    def __getstate__(self):
        return dict(self.__dict__)

    def __setstate__(self, state):
        self.__dict__ = state
        self.data = state['_data']

    def __str__(self):
        return str(self.__getstate__())

    @property
    def error(self):
        return self._error

    @error.setter
    def error(self, exception):
        self._set_error(exception)

    def _set_error(self, exception):
        self._error = exception

    conversion_methods = defaultdict(lambda: lambda data: data)

    def format_error(self):
        if self.error:
            messages = self.error.message
            if not isinstance(messages, list):
                messages = [messages]
            print map(lambda _error: _error.message if isinstance(_error, Exception) else _error, messages)
            return map(lambda _error: _error.message if isinstance(_error, Exception) else _error, messages)

        else:
            return None

    def error_string(self):
        if self.error:
            return str(self.format_error())
        else:
            return None

    def data_string(self):
        return str(self.data)

    def convert(self, convert_to):
        if issubclass(convert_to, self.__class__):
            # Widening conversion
            new_class = convert_to
        else:
            if not issubclass(self.__class__, convert_to):
                # A complex widening conversion
                bases = tuple([convert_to] + filter(lambda cls: not issubclass(cls, DataFormatInterface) and not issubclass(convert_to, cls), list(self.__class__.__bases__) + [self.__class__]))
                if len(bases) == 1:
                    new_class = bases[0]
                else:
                    new_class = filter(lambda cls: cls.__bases__ == bases, built_classes)[0]
            else:
                # This is an attempted narrowing conversion
                raise InvalidEventConversion("Narrowing event conversion attempted, this is not allowed <Attempted {old} -> {new}>".format(
                        old=self.__class__, new=convert_to))

        new_class = new_class.__new__(new_class)
        new_class.__dict__.update(self.__dict__)
        new_class.data = self.data
        return new_class

    def clone(self):
        return deepcopy(self)


class HttpEvent(Event):

    def __init__(self, headers=None, status=(200, "OK"), environment={}, *args, **kwargs):
        headers = headers or {}
        content_type = headers.get("Content-Type", None)

        if not content_type:
            headers['Content-Type'] = self._content_type

        self.headers = headers
        self.status = status
        self.environment = environment
        super(HttpEvent, self).__init__(*args, **kwargs)

    @property
    def headers(self):
        self._headers["Content-Type"] = self._content_type
        return self._headers

    @headers.setter
    def headers(self, headers):
        self._headers = headers

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, status):
        if isinstance(status, tuple):
            self._status = status
        elif isinstance(status, str):
            status = re.split(' |-', status, 1)
            if len(status) == 2:
                self._status = (int(status[0]), status[1])

    def _set_error(self, exception):
        if exception is not None:
            error_state = http_code_map[exception.__class__]
            self.status = error_state.get("status")
            self.headers.update(error_state.get("headers", {}))

        super(HttpEvent, self)._set_error(exception)


class _XMLFormatInterface(DataFormatInterface):

    _content_type = "application/xml"

    conversion_methods = {str: lambda data: etree.fromstring(data)}
    conversion_methods.update(dict.fromkeys(_XML_TYPES, lambda data: data))
    conversion_methods.update(dict.fromkeys(_JSON_TYPES, lambda data: etree.fromstring(xmltodict.unparse(internal_xmlify(data)).encode('utf-8'))))
    conversion_methods.update({None.__class__: lambda data: etree.fromstring("<root/>")})

    def __getstate__(self):
        state = super(_XMLFormatInterface, self).__getstate__()
        state['_data'] = etree.tostring(self.data)
        return state

    def data_string(self):
        return etree.tostring(self.data)

    def format_error(self):
        errors = super(_XMLFormatInterface, self).format_error()
        if errors:
            _root = etree.Element("errors")
            for error in errors:
                error_element = etree.Element("error")
                error_element.text = error
                _root.append(error_element)

            errors = _root

        return errors

    def error_string(self):
        error = self.format_error()
        if error is not None:
            error = etree.tostring(error, pretty_print=True)
        return error


class _JSONFormatInterface(DataFormatInterface):

    _content_type = "application/json"

    conversion_methods = {str: lambda data: json.loads(data)}
    conversion_methods.update(dict.fromkeys(_JSON_TYPES, lambda data: json.loads(json.dumps(data))))
    conversion_methods.update(dict.fromkeys(_XML_TYPES, lambda data: remove_internal_xmlify(xmltodict.parse(etree.tostring(data), expat=expat))))
    conversion_methods.update({None.__class__: lambda data: {}})

    def __getstate__(self):
        state = super(_JSONFormatInterface, self).__getstate__()
        state['_data'] = json.dumps(self.data)
        return state

    def data_string(self):
        return json.dumps(self.data)

    def format_error(self):
        errors = super(_JSONFormatInterface, self).format_error()
        if errors:
            errors = [{"error": error} for error in errors]

        return errors

    def error_string(self):
        error = self.format_error()
        if error:
            error = json.dumps(error)
        return error


class XMLEvent(_XMLFormatInterface, Event):
    pass


class JSONEvent(_JSONFormatInterface, Event):
    pass


class JSONHttpEvent(JSONEvent, HttpEvent):
    pass


class XMLHttpEvent(XMLEvent, HttpEvent):
    pass


class LogEvent(Event):
    """
    This is a lightweight event designed to mimic some of the event properties of a regular event
    """

    def __init__(self, level, origin_actor, message, id=None):
        self.id = id or uuid().get_hex()
        self.level = level
        self.time = datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]
        self.origin_actor = origin_actor
        self.message = message
        self.data = {"id":              self.id,
                    "level":            self.level,
                    "time":             self.time,
                    "origin_actor":     self.origin_actor,
                    "message":          self.message}

built_classes = [Event, XMLEvent, JSONEvent, HttpEvent, JSONHttpEvent, XMLHttpEvent, LogEvent]
__all__ = map(lambda cls: cls.__name__, built_classes)

http_code_map = defaultdict(lambda: {"status": ((500, "Internal Server Error"))},
                            {
                                ResourceNotModified:    {"status": (304, "Not Modified")},
                                MalformedEventData:     {"status": (400, "Bad Request")},
                                UnauthorizedEvent:      {"status": (401, "Unauthorized"),
                                                         "headers": {'WWW-Authenticate': 'Basic realm="Compysition Server"'}},
                                ForbiddenEvent:         {"status": (403, "Forbidden")},
                                ResourceNotFound:       {"status": (404, "Not Found")},
                                EventCommandNotAllowed: {"status": (405, "Method Not Allowed")},
                                ActorTimeout:           {"status": (408, "Request Timeout")},
                                ResourceConflict:       {"status": (409, "Conflict")},
                                ResourceGone:           {"status": (410, "Gone")},
                                UnprocessableEventData: {"status": (422, "Unprocessable Entity")},
                                EventRateExceeded:      {"status": (429, "Too Many Requests")},
                                CompysitionException:   {"status": (500, "Internal Server Error")},
                                ServiceUnavailable:     {"status": (503, "Service Unavailable")}
                            })