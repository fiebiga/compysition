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
import zmq.green as zmq
from gevent.queue import Queue
import socket
import gevent
from compysition.event import CompysitionEvent

"""
Implementation of a TCP in and out connection using gevent sockets
TODO: Add options like "Wait for response" and "Send response" for TCPIn and TCPOut, respectively
"""

DEFAULT_PORT = 9000

class ZMQPush(Actor):

    """
    Send events over ZMQ Push
    """

    def __init__(self, name, port=None, host=None, listen=True, mode="connect", *args, **kwargs):
        Actor.__init__(self, name, *args, **kwargs)
        self.blockdiag_config["shape"] = "cloud"
        self.port = port or DEFAULT_PORT
        self.host = host or socket.gethostbyname(socket.gethostname())
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUSH)
        if mode == "connect":
            self.socket.connect("tcp://{0}:{1}".format(self.host, self.port))
        elif mode == "bind":
            self.socket.bind("tcp://*:{0}".format(self.port))
        self.outbound_queue = Queue()

    def consume(self, event, *args, **kwargs):
        self.outbound_queue.put(event)

    def pre_hook(self):
        self.threads.spawn(self.__consume_outbound_queue)

    def __consume_outbound_queue(self):
        while self.loop():
            try:
                event = self.outbound_queue.get(timeout=2.5)
            except:
                event = None

            if event is not None:
                self.socket.send(event.to_string())

class ZMQPull(Actor):

    """
    Receive Events over ZMQ Pull
    """

    def __init__(self, name, port=None, host=None, mode="bind", *args, **kwargs):
        Actor.__init__(self, name, *args, **kwargs)
        self.port = port or DEFAULT_PORT
        self.host = host or socket.gethostbyname(socket.gethostname())
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PULL)
        if mode == "connect":
            self.socket.connect("tcp://{0}:{1}".format(self.host, self.port))
        elif mode == "bind":
            self.socket.bind("tcp://*:{0}".format(self.port))

        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)

    def consume(self, event, *args, **kwargs):
        pass

    def pre_hook(self):
        self.threads.spawn(self._listen)

    def _listen(self):
        while self.loop():
            try:
                items = self.poller.poll()
            except KeyboardInterrupt:
                break

            if items:
                event = self.socket.recv_multipart()
                event = CompysitionEvent.from_string(event[0])
                self.send_event(event)







