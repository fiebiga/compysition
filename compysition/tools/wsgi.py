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
from pprint import pformat

class Request(object):

    def __init__(self, environ):
        self.__dict__.update({k.replace('.','_'):v for k,v in environ.items()})  # method syntax safe properties

        self._wsgi_input = self.__dict__.pop('wsgi_input', [])
        self._wsgi_error = self.__dict__.pop('wsgi_errors', [])

        self.input = {}

        try:
            # building key word arguments for the extract method
            keys = ('mime_type', 'boundary')
            kwargs = dict( zip(keys, re.split(';\s*boundary=',self.CONTENT_TYPE)))  # Something like {'boundary': '----WebKitFormBoundaryTGvuUpWjh0LZhgK0', 'mime_type': 'multipart/form-data'}
            self.extract(**kwargs)
        except AttributeError: # means not form data type specified. "CONTENT_TYPE" above.
            pass

    def read_input(self):
        data = "".join([line for line in self._wsgi_input])
        del(self._wsgi_input, self._wsgi_error)
        return data

    def extract(self, mime_type, *args, **kwargs):
        mime_type = mime_type or kwargs.get('mime_type', 'multipart/form-data')
        method_name = mime_type.replace('/', '_').replace('-', '_')  # Example multipart/form-data -> multipart_form_data
        method = getattr(self, 'extract_'+method_name, self.extract_raw)  # get the method matching the name otherwise self.extract_raw
        method(*args, **kwargs)  # Execute the method with the additional provided arguments
        self.extract_querystring()

    def extract_raw(self):
        self.input.update({'raw': self.read_input()})

    def extract_multipart_form_data(self, boundary):
        sep = '--' + boundary
        data = self.read_input()  # Read all of the wsgi.input into memory
        self.input.update({'form_headers': {}})
        for field in data.strip().rstrip('--').split(sep):  # Take the -- off the end and iter each field
            if field:  # If it's not blank
                header_dict = {}
                headers, field_value = field.strip().split("\r\n\r\n")  # divide into headers and the field value
                for header in headers.split('\n'):  # iter over each header
                    name, value = header.split(':')  # split the header into the name and value
                    header_dict.update({name.strip().lower(): value.strip()})  # update the header dict with consistant case like {'header name': 'header value'}
                field_name = header_dict['content-disposition'].split('name=')[1].strip('"')  # Get the field name from the appropriate header
                self.input['form_headers'].update({field_name: header_dict})
                self.input.update({field_name: field_value})  # update out dict of fields like {'field name': 'field value'}

    def extract_application_x_www_form_urlencoded(self):
        self.input.update(parse_qsl(self.read_input()))

    def extract_querystring(self):
        self.input.update(parse_qsl(self.QUERY_STRING))

    def environment(self):
        attrs = self.__dict__.copy()
        attrs.pop('input')
        return attrs

    def bless(self, **kwargs):
        self.__dict__ = dict(kwargs.items() + self.__dict__.items())

    def __getattr__(self, attr):
        try:
            return self.input[attr]
        except KeyError:
            raise AttributeError

if __name__=='__main__':
    from gevent import pywsgi

    def handle(env, sr):
        req = Request(env)
        sr("200 OK", [('Content-type', 'text/plain')])
        return [str(req.XML)]

    server = pywsgi.WSGIServer(('192.168.56.101', 8080), handle, log=None)
    server.serve_forever()