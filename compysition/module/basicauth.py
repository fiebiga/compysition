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
    '''**Sample module which reverses incoming events.**

    Parameters:

        - name (str):       The instance name.

    Queues:

        - inbox:    Incoming events.
        - outbox:   Outgoing events.
    '''

    def __init__(self, name, capitalize=False, key=None, *args, **kwargs):
        Actor.__init__(self, name, *args, **kwargs)
        self.capitalize=capitalize
        self.logging.info("Initialized")
        self.key = key or self.name
        self.caller = 'wsgi'

        self.createQueue('errors')

    def consume(self, event, *args, **kwargs):
        print event['header']['event_id']
        self.logging.info("Got event with headers: {}".format(event['header']))
        try:
            self.logging.info("Trying to extract authorization data")
            authorization = event['header'][self.caller]['environment']['HTTP_AUTHORIZATION']
            self.logging.info("Extracted authorization data: {}".format(authorization))
            user, password = base64.decodestring(authorization.split(' ')[1]).split(':')
            self.logging.info("User: {}, Password: {}".format(user, password))
            if user == 'testuser' and password == 'testpassword':
                self.logging.info("Authorization successful")
                self.send_event(event)
            else:
                message = "Authorization Failed for user {}".format(user)
                self.logging.info(message)
                raise Exception(message)
        except:
            event['header'].get(self.caller, {}).update({'status': '401 Unauthorized'})
            event['header'].get(self.caller, {}).get('http', []).append(('WWW-Authenticate', 'Basic realm="CUA Integrations"'))
            self.queuepool.errors.put(event)