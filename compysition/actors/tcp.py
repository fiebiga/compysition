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
from ast import literal_eval
from compysition.event import CompysitionEvent

"""
Implementation of a TCP in and out connection using gevent sockets
TODO: Add options like "Wait for response" and "Send response" for TCPIn and TCPOut, respectively
"""

DEFAULT_PORT = 9000
BUFFER_SIZE  = 8142

class TCPOut(Actor):

    """
    Send events over TCP
    """

    def __init__(self, name, port=None, host=None, listen=True, *args, **kwargs):
        Actor.__init__(self, name, *args, **kwargs)
        self.port = port or DEFAULT_PORT
        self.host = host or socket.gethostbyname(socket.gethostname())
        self.listen = listen
        self.socket_lsteners = []

    def consume(self, event, *args, **kwargs):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.host, self.port))
        sock.send(event.to_string())
        sock.close()

class TCPIn(Actor):

    """
    Receive Events over TCP
    """

    def __init__(self, name, port=None, host=None, *args, **kwargs):
        Actor.__init__(self, name, *args, **kwargs)
        self.port = port or DEFAULT_PORT
        self.host = host or "0.0.0.0"
        print "Connecting to {0} on {1}".format(self.host, self.port)
        self.server = StreamServer((self.host, self.port), self.connection_handler)

    def consume(self, event, *args, **kwargs):
     pass

    def pre_hook(self):
        self.server.start()

    def post_hook(self):
        self.server.stop()

    def connection_handler(self, socket, address):
        event = ""
        for l in socket.makefile('r'):
            event += l

        try:
            event = CompysitionEvent.from_string(event)
            self.send_event(event)
        except:
            pass






