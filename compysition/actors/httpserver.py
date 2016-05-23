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
from compysition.event import HttpEvent, JSONHttpEvent, XMLHttpEvent
from gevent import pywsgi
import json
from functools import wraps
from collections import defaultdict
from gevent.queue import Queue
from bottle import *

BaseRequest.MEMFILE_MAX = 1024 * 1024 # (or whatever you want)


class ContentTypePlugin(object):
    """**Bottle plugin that filters basic content types that are processable by Compysition**"""

    DEFAULT_VALID_TYPES = ("text/xml",
                           "application/xml",
                           "text/plain",
                           "text/html",
                           "application/json",
                           "application/x-www-form-urlencoded")

    name = "ctypes"
    api = 2

    def __init__(self, default_types=None):
        self.default_types = default_types or self.DEFAULT_VALID_TYPES

    def apply(self, callback, route):
        ctype = request.content_type.split(';')[0]
        ignore_ctype = route.config.get('ignore_ctype', False) or request.content_length < 1
        if ignore_ctype or ctype in route.config.get('ctypes', self.default_types):
            return callback
        else:
            raise HTTPError(415, "Unsupported Content-Type '{_type}'".format(_type=ctype))


class HTTPServer(Actor, Bottle):
    """**Receive events over HTTP.**

    Actor runs a pywsgi gevent webserver, using an optional routes json file for complex routing using Bottle

    Parameters:
        name (str):
            | The instance name.
        address(Optional[str]):
            | The address to bind to.
            | Default: 0.0.0.0
        port(Optional[int]):
            | The port to bind to.
            | Default: 8080
        keyfile(Optional([str]):
            | In case of SSL the location of the keyfile to use.
            | Default: None
        certfile(Optional[str]):
            | In case of SSL the location of the certfile to use.
            | Default: None
        routes_config(Optional[dict]):
            | This is a JSON object that contains a list of Bottle route config kwargs
            | Default: {"routes": [{"path: "/<queue>", "method": ["POST"]}]}

    Examples:
        Default:
            http://localhost:8080/foo is mapped to 'foo' queue
            http://localhost:8080/bar is mapped to 'bar' queue
        routes_config:
            routes_config {"routes": [{"path: "/my/url/<queue>", "method": ["POST"]}]}
                http://localhost:8080/my/url/goodtimes is mapped to 'goodtimes' queue
    """

    DEFAULT_ROUTE = {
        "routes":
            [
                {
                    "path": "/<queue>",
                    "method": [
                        "POST"
                    ]
                }
            ]
    }

    CONTENT_TYPE_MAP = defaultdict(lambda: HttpEvent,
                                   {"application/json": JSONHttpEvent,
                                    "text/xml": XMLHttpEvent,
                                    "application/xml": XMLHttpEvent,
                                    "text/html": XMLHttpEvent,
                                    "text/plain": HttpEvent})

    X_WWW_FORM_URLENCODED_KEY_MAP = defaultdict(lambda: HttpEvent, {"XML": XMLHttpEvent, "JSON": JSONHttpEvent})
    X_WWW_FORM_URLENCODED = "application/x-www-form-urlencoded"

    def __init__(self, name, address="0.0.0.0", port=8080, keyfile=None, certfile=None, routes_config=None, *args, **kwargs):
        Actor.__init__(self, name, *args, **kwargs)
        Bottle.__init__(self)
        self.blockdiag_config["shape"] = "cloud"
        self.address = address
        self.port = port
        self.keyfile = keyfile
        self.certfile = certfile
        self.responders = {}
        routes_config = routes_config or self.DEFAULT_ROUTE

        if isinstance(routes_config, str):
            routes_config = json.loads(routes_config)

        if isinstance(routes_config, dict):
            for route in routes_config.get('routes'):
                callback = getattr(self, route.get('callback', 'callback'))
                self.route(callback=callback, **route)

        self.wsgi_app = self
        self.wsgi_app.install(self.log_to_logger)
        self.wsgi_app.install(ContentTypePlugin())

    def log_to_logger(self, fn):
        '''
        Wrap a Bottle request so that a log line is emitted after it's handled.
        (This decorator can be extended to take the desired logger as a param.)
        '''
        @wraps(fn)
        def _log_to_logger(*args, **kwargs):
            self.logger.info('[{address}] {method} {url}'.format(address=request.remote_addr,
                                            method=request.method,
                                            url=request.url))
            actual_response = fn(*args, **kwargs)
            return actual_response
        return _log_to_logger

    def __call__(self, e, h):
        """**Override Bottle.__call__ to strip trailing slash from incoming requests**"""

        e['PATH_INFO'] = e['PATH_INFO'].rstrip('/')
        return Bottle.__call__(self, e, h)

    def consume(self, event, *args, **kwargs):
        # There is an error that results in responding with an empty list that will cause an internal server error

        original_event_class, response_queue = self.responders.pop(event.event_id, None)

        if response_queue:

            if not isinstance(event, original_event_class):
                self.logger.warning("Incoming event did did not match the clients content type format. Converting '{current}' to '{new}'".format(
                    current=type(event), new=original_event_class))
                event = event.convert(original_event_class)

            if event.error:
                response_data = event.error_string()
            else:
                response_data = event.data_string()

            status, status_message = event.status
            local_response = HTTPResponse()
            local_response.status = "{code} {message}".format(code=status, message=status_message)

            for header in event.headers.keys():
                local_response.set_header(header, event.headers[header])

            if int(status) == 204:
                response_data = ""

            local_response.body = response_data
            response_queue.put(local_response)
            response_queue.put(StopIteration)
        else:
            self.logger.warning("Received event response for an unknown event ID. The request might have already received a response", event=event)

    def _format_bottle_env(self, environ):
        """**Filters incoming bottle environment of non-serializable objects, and adds useful shortcuts**"""

        query_string_data = {}
        for key in environ["bottle.request"].query.iterkeys():
            query_string_data[key] = environ["bottle.request"].query.get(key)

        environ = {key: environ[key] for key in environ.keys() if isinstance(environ[key], (str, tuple, bool, dict))}
        environ['QUERY_STRING_DATA'] = query_string_data

        return environ

    def callback(self, queue=None, *args, **kwargs):
        queue_name = queue or self.name
        queue = self.pool.outbound.get(queue_name, None)
        ctype = request.content_type.split(';')[0]

        if ctype == '':
            ctype = None

        if queue:
            event_class, data = None, None

            if ctype == self.X_WWW_FORM_URLENCODED:
                for item in request.forms.items():
                    event_class, data = self.X_WWW_FORM_URLENCODED_KEY_MAP[item[0]], item[1]
                    # Compysition HTTPServer only supports one request urlencoded tag at this point
                    break
            else:
                event_class, data = self.CONTENT_TYPE_MAP[ctype], request.body.read()

            if data == '':
                data = None

            event = event_class(environment=self._format_bottle_env(request.environ),
                                service=queue_name, data=data, **kwargs)

            self.send_event(event, queue=queue)
            self.logger.info("Received {0} request for service {1}".format(request.method, queue_name), event=event)
            response_queue = Queue()
            self.responders.update({event.event_id: (event_class, response_queue)})
            local_response = response_queue
        else:
            response.body = "Service '{0}' not found".format(queue_name)
            response.status = "404 Not Found"
            self.logger.error("Received {method} request with URL '{url}'. Queue name '{queue_name}' was not found".format(method=request.method,
                                                                                                                       url=request.path,
                                                                                                                       queue_name=queue_name))
            local_response = response

        return local_response

    def post_hook(self):
        self.__server.stop()
        self.logger.info("Stopped serving")

    def __serve(self):
        if self.keyfile is not None and self.certfile is not None:
            self.__server = pywsgi.WSGIServer((self.address, self.port), self, keyfile=self.keyfile, certfile=self.certfile)
        else:
            self.__server = pywsgi.WSGIServer((self.address, self.port), self, log=None)
        self.logger.info("Serving on {address}:{port}".format(address=self.address, port=self.port))
        self.__server.start()

    def pre_hook(self):
        self.__serve()