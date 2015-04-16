#!/usr/bin/env python
#
# -*- coding: utf-8 -*-
#
#  basicauth.py
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

from compysition import Actor
import base64
from pprint import pformat

class BasicAuth(Actor):
    '''**Sample module demonstrating http basic auth. This module should be subclassed and implemented in a specific manner**
    '''

    def __init__(self, name, caller='wsgi', *args, **kwargs):
        Actor.__init__(self, name, *args, **kwargs)
        self.caller = caller

    def consume(self, event, *args, **kwargs):
        try:
            try:
                authorization = event.header[self.caller]['environment']['HTTP_AUTHORIZATION']
                user, password = base64.decodestring(authorization.split(' ')[1]).split(':')
            except:
                raise Exception("No auth headers present in submitted request")

            if self._authenticate(user, password):
                self.logger.info("Authorization successful", event=event)
                self.send_event(event)
            else:
                message = "Authorization Failed for user {0}".format(user)
                self.logger.info(message, event=event)
                raise Exception(message)
        except Exception as err:
            self.logger.warn("Authorization Failed: {0}".format(err), event=event)
            event.header.get(self.caller, {}).update({'status': '401 Unauthorized'})
            event.header.get(self.caller, {}).get('http', []).append(('WWW-Authenticate', 'Basic realm="Compysition Authentication"'))
            self.send_error(event)

    def _authenticate(self, username, password):
        """ The method to be implemented in a manner specific to an organization """

        self.logger.error("Error, attempted to use an un-implemented version of the basicauth module. This is not safe, please implement the _authenticate method in this module")
        raise Exception("Non-implemented authenticate module")
