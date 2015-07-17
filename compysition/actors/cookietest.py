#!/usr/bin/env python
#
# -*- coding: utf-8 -*-
#
#  flowcontroller.py
#
#  Copyright 2014 Adam Fiebig <adam.fiebig@cuanswers.com>
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
import Cookie

class CookieTest(Actor):

    def __init__(self, name, *args, **kwargs):
        Actor.__init__(self, name, *args, **kwargs)

    def consume(self, event, *args, **kwargs):
        if 'HTTP_COOKIE' in event.wsgi['environment']:
            #self.logger.info("FOUND Cookie! Deleting it", event=event)
            session_cookie = Cookie.SimpleCookie()
            session_cookie['session'] = "somedata"
            session_cookie['session']["Path"] = '/'
            session_cookie['session']['expires'] ='Thu, 01 Jan 1970 00:00:00 GMT'
        else:
            #self.logger.info("DIDNT find Cookie! Creating it", event=event)
            session_cookie = Cookie.SimpleCookie()
            session_cookie['session'] = "somedata"
            session_cookie['session']["Path"] = '/'

        event.get("wsgi", {}).get('http', []).append(("Set-Cookie", session_cookie.values()[0].OutputString()))
        self.send_event(event)
