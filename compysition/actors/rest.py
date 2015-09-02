#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  rest.py
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

class RESTTranslator(Actor):
    """
    The purpose of this actor is to translate a returning event into a proper RESTful
    response.

    e.g. method = POST and status = "200 OK" "method = 201 Created"
    """

    def __init__(self, name, web_interface="wsgi", url_post_location=None, *args, **kwargs):
        super(RESTTranslator, self).__init__(name, *args, **kwargs)
        self.web_interface = web_interface
        self.default_status = "200 OK"
        self.url_post_location = url_post_location

    def consume(self, event, *args, **kwargs):
        headers = event.get(self.web_interface, {})
        if len(headers) == 0:
            self.logger.warn("No HTTP headers were defined for incoming event", event=event)

        method = headers.get("environment", {}).get("REQUEST_METHOD", None)

        event = getattr(self, "translate_{method}".format(method=method))(event)
        self.send_event(event)

    def translate_POST(self, event):
        headers = event.get(self.web_interface, {})
        status_code = int(headers.get("status", self.default_status).split(' ')[0])

        if status_code == 200:
            headers['status'] = "201 Created"
            local_url = self.url_post_location or headers.get("environment", {}).get("PATH_INFO", None)
            entity_id = event.get("entity_id", event.meta_id)

            if local_url is not None:
                if "{entity_id}" in local_url:
                    location = local_url.format(entity_id=entity_id)
                else:
                    location = local_url + "/" + entity_id

                headers['http'].append(('Location', location))
        else:
            pass

        return event

    def translate_UPDATE(self, event):
        headers = event.get(self.web_interface, {})
        status_code = int(headers.get("status", self.default_status)).split(' ')[0]

        if status_code == 200:
            if event.data is None or event.data == "" or len(event.data) == 0:
                headers['status'] = "204 No Content"
        else:
            pass

        return event

    def translate_GET(self, event):
        return self.translate_UPDATE(event)

    def translate_PUT(self, event):
        return self.translate_UPDATE(event)

    def translate_DELETE(self, event):
        return self.translate_UPDATE(event)
