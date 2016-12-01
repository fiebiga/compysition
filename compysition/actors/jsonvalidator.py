#!/usr/bin/env python
#
# -*- coding: utf-8 -*-
#
#  jsonvalidator.py
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
from jsonschema import Draft4Validator, FormatChecker
from jsonschema.exceptions import SchemaError, ValidationError
import json
from compysition.event import JSONEvent
from compysition.errors import MalformedEventData


class JSONValidator(Actor):

    input = JSONEvent
    output = JSONEvent

    '''**A simple module which applies a provided jsonschema to an incoming event JSON data**

    Parameters:

        name (str):
            | The instance name.
        schema (str):
            | The schema (jsonschema) to validate the incoming json against

    '''

    def __init__(self, name, schema=None, *args, **kwargs):
        super(JSONValidator, self).__init__(name, *args, **kwargs)
        self.schema = schema
        if self.schema:
            formatter = self._build_formatter()

            try:
                if isinstance(self.schema, str):
                    self.schema = json.loads(self.schema)

                if isinstance(self.schema, dict):
                    self.schema = Draft4Validator(self.schema, format_checker=formatter)
                else:
                    raise ValueError("Schema must be of type str or dict. Instead received type '{type}'".format(type=type(self.schema)))
            except Exception as err:
                self.logger.error("Invalid schema: {err}".format(err=err))
                self.schema = None

    def consume(self, event, *args, **kwargs):
        try:
            if self.schema:
                self.schema.validate(event.data)

            self.logger.info("Incoming JSON successfully validated", event=event)
            self.send_event(event)

        except (SchemaError, ValidationError):
            error_reasons = []
            for error in self.schema.iter_errors(event.data):
                err_message = ""
                path = map(str, list(error.path))
                if len(path) > 0:
                    err_message = ": ".join(path)

                err_message += " " + error.message
                error_reasons.append(err_message)
            message = error_reasons
            self.process_error(message, event)

    @staticmethod
    def _build_formatter():
        """Create a formatter to be passed to the validator. This method can be subclassed to add custom formatters ie:

        formatter = FormatChecker()
        @formatter.checks('my-custom-format', raises=ValidationError)
         def my_custom_format(instance):
            if matches_my_custom_format(instance):
                return True
            else:
                return False

        more info: https://python-jsonschema.readthedocs.io/en/latest/validate/#validating-formats
         """
        return FormatChecker()

    def process_error(self, message, event):
        self.logger.error("Error validating incoming JSON: {0}".format(message), event=event)
        raise MalformedEventData(message)
