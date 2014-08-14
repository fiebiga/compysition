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
from compysition.tools import ManagedQueue
from compysition.tools.wsgi import Request
from gevent import pywsgi, spawn, queue
from uuid import uuid4 as uuid
import pdb

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
        self.run_server = run_server
        self.base_path = base_path

    def preHook(self):
        if self.run_server:
            spawn(self.__serve)

    def application(self, env, start_response):
        self.logging.info('UCI Received Message')
        response_queue = ManagedQueue()
        self.responders.update({response_queue.label: start_response})
        request = Request(env)
        message = {
            "header": {
                self.key: {
                    "request_id": response_queue.label,
                    "environment": request.environment(),
                    "status": self.default_status,
                    "http": [
                        ("Content-Type", "text/html")
                    ]
                }
            },
            "data": None
        }
        try:
            message.update({"data":request.input})
            message['header']['event_id'] = message['header']['wsgi']['request_id'] # event_id is required for certain modules to track same event
            if env['PATH_INFO'] == self.base_path:
                self.logging.info("Putting received message on outbox {0}".format(env['PATH_INFO']))
                self.queuepool.outbox.put(message)
            else:
                outbox_path = env['PATH_INFO'].lstrip("{0}/".format(self.base_path)).split('/')[0]
                self.logging.info("Putting received message on outbox {0}".format(outbox_path))
                getattr(self.queuepool, outbox_path).put(message)
            start_response(self.default_status, message['header'][self.key]['http'])
            return response_queue
        except Exception as err:
            start_response('404 Not Found', message['header'][self.key]['http'])
            return "A problem occurred processing your request. Reason: %s"%(err)

    def consume(self, event, *args, **kwargs):
        #pdb.set_trace()
        self.logging.debug("WSGI Received Response from origin: {0}".format(kwargs.get('origin')))
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

    def __setupQueues(self):
        return
        self.deleteQueue("inbox")
        for resource in self.resources:
            path=resource.keys()[0]
            queue=resource[resource.keys()[0]]
            self.createQueue(queue)
            self.queue_mapping[path]=getattr(self.queuepool, queue)

    def __serve(self):
        if self.keyfile != None and self.certfile != None:
            self.__server = pywsgi.WSGIServer((self.address, self.port), self.application, keyfile=self.keyfile, certfile=self.certfile)
        else:
            self.__server = pywsgi.WSGIServer((self.address, self.port), self.application, log=None)
        self.__server.start()
        self.logging.info("Serving on %s:%s"%(self.address, self.port))
        self.block()
        self.logging.info("Stopped serving.")
        self.__server.stop()

