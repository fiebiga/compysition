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
from compysition.errors import QueueLocked
from util.wsgi import Request
from util.managedqueue import ManagedQueue
from gevent import pywsgi, spawn, queue
from uuid import uuid4 as uuid
import pdb
import traceback

class WSGI(Actor):
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

    def preHook(self):
        if self.run_server:
            self.__serve()


    def application(self, env, start_response):        
        try:
            request = Request(env)
        except Exception as err:
            start_response('400 Bad Request', [self.default_content_type])
            return "Malformed or empty request"

        response_queue = ManagedQueue()

        self.responders.update({response_queue.label: start_response})

        event = {
            "header": {
                "event_id": response_queue.label, 
                self.key: {
                    "request_id": response_queue.label,
                    "service": "",
                    "environment": request.environment,
                    "status": self.default_status,
                    "http": [
                        ("Content-Type", "text/html")
                    ]
                }
            },
            "data": request.input
        }

        try:
            self.logger.info('Received Message', event_id=event['header']['event_id'])
            if env['PATH_INFO'] == self.base_path:
                self.logger.info("Putting received message on outbox {0}".format(env['PATH_INFO']), event_id=event['header']['event_id'])
                event['header']['service'] = "default"
                self.send_event(event, queue=self.pool.getQueue("outbox"))
            else:
                outbox_path = env['PATH_INFO'].replace("{0}/".format(self.base_path), "", 1).lstrip('/').split('/')[0]
                event['header']['service'] = outbox_path
                self.logger.info("Putting received message on outbox {0}".format(outbox_path), event_id=event['header']['event_id'])
                self.send_event(event, queue=self.pool.getQueue(outbox_path))

            start_response(self.default_status, event['header'][self.key]['http'])
            return response_queue
        except Exception as err:
            self.logger.warn("Exception on application processing: {0}".format(traceback.format_exc()), event_id=event['header']['event_id'])
            start_response('404 Not Found', [self.default_content_type])
            return "A problem occurred processing your request. Reason: {0}".format(err)
        

    def consume(self, event, *args, **kwargs):
        self.logger.debug("WSGI Received Response from origin: {0}".format(kwargs.get('origin')), event_id=event['header']['event_id'])
        header = event['header'][self.key]
        request_id = header['request_id']
        response_queue = ManagedQueue(request_id)
        start_response = self.responders.pop(request_id)  # Run this needed or not to be sure it's removed from memory with pop()
        start_response(header['status'], header['http'])  # Make sure we have all the headers so far
        response_queue.put(str(event['data']))
        response_queue.put(StopIteration)

    def serialize(self, dictionary):
        result = {}
        allowed = (dict, list, basestring, int, long, float, bool)
        for key, value in dictionary.items():
            if isinstance(value, allowed) or value is None:
                result.update({key:value})
        return json.dumps(result)

    def postHook(self):
        self.__server.stop()
        self.logger.info("Stopped serving.")

    def __serve(self):
        if self.keyfile != None and self.certfile != None:
            self.__server = pywsgi.WSGIServer((self.address, self.port), self.application, keyfile=self.keyfile, certfile=self.certfile)
        else:
            self.__server = pywsgi.WSGIServer((self.address, self.port), self.application, log=None)
        self.logger.info("Serving on %s:%s"%(self.address, self.port))
        self.__server.start()
