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

from compysition import Actor
from compysition.actors.util.managedqueue import ManagedQueue
from gevent import pywsgi, spawn, sleep
import traceback

from bottle import *

class WSGI(Actor, Bottle):
    '''**Receive events over HTTP.**
    This module starts a webserver to which events can be submitted using the
    http protocol.
    Parameters:
        - name (str):       The instance name.
        - address(str):     The address to bind to.
                            Default: 0.0.0.0
        - port(str):        The port to bind to.
                            Default: 10080
        - keyfile(str):     In case of SSL the location of the keyfile to use.
                            Default: None
        - certfile(str):    In case of SSL the location of the certfile to use.
                            Default: None
        - delimiter(str):   The delimiter between multiple events.
                            Default: None
        - run_server(bool): Specify whether or not to run a WSGI server on the specified
                            port and address
                            Default: False
        - base_path(str):   The path the use as the base when stripping out an outbox path.
                            Example:    base_path="/foo"
                                        Incoming Path Info = "/foo/bar"
                                        Outbox Used: "bar"
    Queues:
        - outbox:   Events coming from the outside world and submitted to /
    When more queues are connected to this module instance, they are
    automatically mapped to the URL resource.
    For example http://localhost:10080/fubar is mapped to the <fubar> queue.
    The root resource "/" is mapped the <outbox> queue.
    '''

    def __init__(self, name, base_path='/', address="0.0.0.0", port=8080, keyfile=None, certfile=None, delimiter=None, key=None, run_server=False, *args, **kwargs):
        Actor.__init__(self, name, *args, **kwargs)
        self.blockdiag_config["shape"] = "cloud"

        self.name=name
        self.address=address
        self.port=port
        self.keyfile=keyfile
        self.certfile=certfile
        self.delimiter=delimiter
        self.key = key or self.name
        self.responders = {}
        self.default_status = "200 OK"
        self.default_content_type = ("Content-Type", "text/html")
        self.run_server = run_server
        self.base_path = base_path
        self.wsgi_app = self.application

    def pre_hook(self):
        if self.run_server:
            self.__serve()

    def application(self, env, start_response):
        try:
            request = Request(env)
        except Exception as err:
            start_response('400 Bad Request', [self.default_content_type])
            return """  <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
                        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
                        <html>
                          <body>
                            Invalid content submitted
                          </body>
                        </html>"""

        try:
            if env['PATH_INFO'] == self.base_path:
                service = self.DEFAULT_EVENT_SERVICE
                outbox = "outbox"
            else:
                outbox = env['PATH_INFO'].replace("{0}/".format(self.base_path), "", 1).lstrip('/').split('/')[0]
                service = outbox

            response_queue = ManagedQueue()
            #TODO: Remove request_id?
            environment_header = {"request_id": response_queue.label,
                                    "service": "",
                                    "environment": request.environment,
                                    "status": self.default_status,
                                    "http": [self.default_content_type]}
            event = self.create_event(data=request.input, service=service)
            event.set(self.key, environment_header)

            self.logger.info("Putting received message on outbox {0}".format(outbox), event=event)
            queue = self.pool.outbound_queues.get(outbox, None)

            if queue:
                self.send_event(event, queue=queue)
            else:
                raise Exception("Service {0} not found".format(outbox))

            self.responders.update({response_queue.label: start_response})
            start_response(self.default_status, [self.default_content_type])
            return response_queue
        except Exception as err:
            self.logger.warn("Exception on application processing: {0}".format(traceback.format_exc()), event=event)
            start_response('404 Not Found', [self.default_content_type])
            return "A problem occurred processing your request. Reason: {0}".format(err)

    def consume(self, event, *args, **kwargs):
        header = event.get(self.key)
        request_id = header['request_id']
        response_queue = ManagedQueue(request_id)
        start_response = self.responders.pop(request_id)  # Run this needed or not to be sure it's removed from memory with pop()
        start_response(header['status'], header['http'])  # Make sure we have all the headers so far
        response_queue.put(str(event.data))
        response_queue.put(StopIteration)

    def post_hook(self):
        self.__server.stop()
        self.logger.info("Stopped serving.")

    def __serve(self):
        if self.keyfile is not None and self.certfile is not None:
            self.__server = pywsgi.WSGIServer((self.address, self.port), self, keyfile=self.keyfile, certfile=self.certfile)
        else:
            self.__server = pywsgi.WSGIServer((self.address, self.port), self, log=None)
        self.logger.info("Serving on %s:%s"%(self.address, self.port))
        self.__server.start()

class BottleWSGI(WSGI, Bottle):

    def __init__(self, *args, **kwargs):
        WSGI.__init__(self, *args, **kwargs)
        Bottle.__init__(self)
        self.wsgi_app = self

    def pre_hook(self):
        self.set_routes()
        super(BottleWSGI, self).pre_hook()

    def set_routes(self):
        self.route(path="/<url:re:.+>", callback=self.default_callback, method=['POST'])
        self.route(path="/explicit", callback=self.explicit_callback, method=['POST'])

    def explicit_callback(self, *args, **kwargs):
        event = self.create_event(environment=request.environ, data=request.forms.items())
        print event.data
        response_queue = ManagedQueue()
        spawn(self.test, response_queue)
        return response_queue

    def default_callback(self, *args, **kwargs):
        event = self.create_event(environment=request.environ, data=request.forms.items())
        print event.data
        response_queue = ManagedQueue()
        spawn(self.test, response_queue)
        return response_queue

    def test(self, response_queue):
        response = HTTPResponse()
        response.status = 404
        response.body = "Hi there"
        response_queue.put(response)
        response_queue.put(StopIteration)

    def callback(self):
        pass

    def connect_queue(self, bottle_route_kwargs=None, *args, **kwargs):
        bottle_route_kwargs = kwargs.pop('bottle_route_kwargs', None)
        if bottle_route_kwargs:
            self.route(**bottle_route_kwargs)
        WSGI.connect_queue(self, *args, **kwargs)