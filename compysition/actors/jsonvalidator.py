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
from jsonschema import Draft4Validator
from jsonschema.exceptions import SchemaError, ValidationError
import json
from ast import literal_eval


class JSONValidator(Actor):
    '''**A sample module which applies a provided jsonschema to an incoming event JSON data**

    Parameters:

        - name (str):               The instance name.
        - schema (str):             The schema (jsonschema) to validate the incoming json against

    '''

    def __init__(self, name, schema=None, *args, **kwargs):
        Actor.__init__(self, name, *args, **kwargs)
        if schema:
            try:
                if isinstance(schema, str):
                    schema = literal_eval(schema)

                if isinstance(schema, dict):
                    self.schema = Draft4Validator(schema)
                else:
                    raise ValueError("Schema must be of type str or dict. Instead received type '{type}'".format(type=type(schema)))
            except Exception as err:
                self.logger.error("Invalid schema: {err}".format(err=err))
                self.schema = None
        else:
            self.schema = None

        self.caller = "wsgi"

    def consume(self, event, *args, **kwargs):
        try:
            json_data = json.loads(event.data)
        except Exception as err:
            self.process_error(event, err)
        else:
            try:
                if self.schema:
                    self.schema.validate(json_data)

                self.logger.info("Incoming JSON successfully validated", event=event)
                self.send_event(event)

            except (SchemaError, ValidationError):
                error_reasons = []
                for error in self.schema.iter_errors(json_data):
                    err_message = ""
                    path = map(str, list(error.path))
                    if len(path) > 0:
                        err_message = ": ".join(path)

                    err_message += error.message
                    error_reasons.append(err_message)
                message = error_reasons
                self.process_error(event, message)

    def process_error(self, event, message):
        event.get(self.caller, {}).update({'status': '400 Bad Request'})
        event.data = "Malformed Request (Invalid JSON): {0}".format(message)
        self.logger.error("Error validating incoming JSON: {0}".format(message), event=event)
        self.send_error(event)
