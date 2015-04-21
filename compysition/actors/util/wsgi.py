#!/usr/bin/env python
#
# -*- coding: utf-8 -*-
#
#  wsgi.py
#
#  Copyright 2014 James Hulett <james.hulett@cuanswers.com>
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

from urlparse import parse_qsl
import re

class Request(object):

    def __init__(self, environ):
        self.environment = {}                                                       # 'environment' contains all header information
        self.input = {}                                                             # 'input' ultimately will contain the processed POST data

        self.environment.update({k.replace('.','_'):v for k,v in environ.items()})  # method syntax safe properties
        self.environment.update({'FINAL_PATH_ENTRY': self.environment['PATH_INFO'].split('/').pop()})

        self._wsgi_input = self.environment.pop('wsgi_input', [])                   # Remove these fields as we don't want them also included in the environment dict
        self._wsgi_error = self.environment.pop('wsgi_errors', [])

        try:                  
            keys = ('mime_type', 'boundary')                                        # Building key word arguments for the extract method
            kwargs = dict( zip(keys, re.split(';\s*boundary=',self.environment.get("CONTENT_TYPE"))))   # Something like {'boundary': '----WebKitFormBoundaryTGvuUpWjh0LZhgK0', 'mime_type': 'multipart/form-data'}
            self.extract(**kwargs)
        except AttributeError:                                                      # Means not form data type specified. "CONTENT_TYPE" above.
            pass

    def extract(self, mime_type, *args, **kwargs):
        mime_type = mime_type or kwargs.get('mime_type', 'multipart/form-data')
        method_name = mime_type.replace('/', '_').replace('-', '_')                 # Example multipart/form-data -> multipart_form_data
        method = getattr(self, 'extract_'+method_name, self.extract_raw)            # Get the method matching the name otherwise self.extract_raw
        method(*args, **kwargs)                                                     # Execute the method with the additional provided arguments
        self.extract_querystring()

    def extract_raw(self):
        self.input.update({'raw': self._wsgi_input.read()})

    def extract_multipart_form_data(self, boundary):
        sep = '--' + boundary
        data = self._wsgi_input.read()                                              # Read all of the wsgi.input into memory
        self.input.update({'form_headers': {}})
        for field in data.strip().rstrip('--').split(sep):                          # Take the -- off the end and iter each field
            if field:                                                               # If it's not blank
                header_dict = {}
                headers, field_value = field.strip().split("\r\n\r\n")              # Divide into headers and the field value
                for header in headers.split('\n'):                                  # Iter over each header
                    name, value = header.split(':')                                 # Split the header into the name and value
                    header_dict.update({name.strip().lower(): value.strip()})       # Update the header dict with consistant case like {'header name': 'header value'}
                field_name = header_dict['content-disposition'].split('name=')[1].strip('"')    # Get the field name from the appropriate header
                self.input['form_headers'].update({field_name: header_dict})
                self.input.update({field_name: field_value})                        # Update out dict of fields like {'field name': 'field value'}

    def extract_application_x_www_form_urlencoded(self):
        data = self._wsgi_input.read()
        if data != "":                                                              # Empty data is not technically MALFORMED data... but parse_qsl strict parsing would throw an exception for empty data
            self.input.update(parse_qsl(data, strict_parsing=True))

    def extract_querystring(self):
        query_string = self.environment.get('QUERY_STRING', '')
        if query_string != '':
            self.environment['QUERY_STRING_DATA'] = {}
            self.environment['QUERY_STRING_DATA'].update(parse_qsl(query_string))