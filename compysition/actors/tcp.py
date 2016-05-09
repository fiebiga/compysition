#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  mdpactors.py
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
#

from compysition import Actor
import gevent.socket as socket
from gevent.server import StreamServer
import gevent
import cPickle as pickle

"""
Implementation of a TCP in and out connection using gevent sockets
"""

#TODO: Add options like "Wait for response" and "Send response" for TCPIn and TCPOut, respectively
#TODO: Add non-event TCPIn (Origination from a non-compysition source)

DEFAULT_PORT = 9000
BUFFER_SIZE  = 1024

class TCPOut(Actor):

    """
    Send events over TCP
    """


    def __init__(self, name, port=None, host=None, listen=True, *args, **kwargs):
        super(TCPOut, self).__init__(name, *args, **kwargs)

        self.blockdiag_config["shape"] = "cloud"
        self.port = port or DEFAULT_PORT
        self.host = host or socket.gethostbyname(socket.gethostname())

    def consume(self, event, *args, **kwargs):
        self._send(event)

    def _send(self, event):
        while True:
            try:
                sock = socket.socket()
                sock.connect((self.host, self.port))
                sock.send((pickle.dumps(event)))
                sock.close()
                break
            except Exception as err:
                self.logger.error("Unable to send event over tcp to {host}:{port}: {error}".format(host=self.host, port=self.port, error=err))
                gevent.sleep(0)

class TCPIn(Actor):

    """
    Receive Events over TCP
    """

    def __init__(self, name, port=None, host=None, *args, **kwargs):
        super(TCPIn, self)._init__(name, *args, **kwargs)
        self.blockdiag_config["shape"] = "cloud"
        self.port = port or DEFAULT_PORT
        self.host = host or "0.0.0.0"
        self.server = StreamServer((self.host, self.port), self.connection_handler)

    def consume(self, event, *args, **kwargs):
     pass

    def pre_hook(self):
        self.logger.info("Connecting to {0} on {1}".format(self.host, self.port))
        self.server.start()

    def post_hook(self):
        self.server.stop()

    def connection_handler(self, socket, address):
        event_string = ""
        for l in socket.makefile('r'):
            event_string += l

        try:
            event = pickle.loads(event_string)
            self.send_event(event)
        except:
            self.logger.error("Received invalid event format: {0}".format(event_string))






