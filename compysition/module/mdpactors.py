import zmq.green as zmq
from util.mdpregistrar import BrokerManager
import gevent
from gevent.queue import Queue
from compysition import Actor
from random import randint
from uuid import uuid4 as uuid
from ast import literal_eval
import util.mdpdefinition as MDPDefinition
import time
from pprint import pprint
from binascii import hexlify

"""
The MDPWorker and MDPClient are implementations of the ZeroMQ MajorDomo configuration, which deals with dynamic process routing based on service configuration and registration.

Also required for this implementation to function is a process or actor running a RegistrationService and one or more MDPBrokers

TODO: Frame documentation
"""

class MDPActor(Actor):

    """
    Receive or send events over ZMQ
    """

    context = None
    broker_manager = None
    socket_identity = None
    outbound_queue = None

    def __init__(self, name, *args, **kwargs):
        Actor.__init__(self, name, *args, **kwargs)
        self.socket_identity = uuid().get_hex()
        self.context = zmq.Context()
        self.outbound_queue = Queue()
        self.broker_manager = BrokerManager(controller_identity=self.socket_identity, logging=self.logger)

    def preHook(self):
        gevent.spawn(self.__listen)
        gevent.spawn(self.__consume_outbound_queue)
        gevent.spawn(self.verify_brokers)

    def consume(self, event, *args, **kwargs):
        self.outbound_queue.put(event)

    def __consume_outbound_queue(self):
        while self.loop():
            try:
                event = self.outbound_queue.get(timeout=2.5)
            except:
                event = None

            if event is not None:
                broker = self.broker_manager.get_next_broker_in_queue()
                if broker is None:
                    self.outbound_queue.put(event)
                    self.logger.info("There are events waiting on the client queue, but no brokers are registered. Queue size is {0}".format(self.outbound_queue.qsize()))
                    gevent.sleep(1)         # Place back on queue and wait for a broker
                else:
                    self.send_outbound_message(broker.outbound_socket, event)

            self.send_heartbeats()

    def __listen(self):
        while self.loop():
            try:
                polled_sockets = dict(self.broker_manager.inbound_poller.poll())
            except KeyboardInterrupt:
                break

            if polled_sockets:
                message = None

                for socket_tuple in self.broker_manager.inbound_poller.sockets:
                    inbound_socket, poll_type = socket_tuple
                    if inbound_socket is not None:
                        if polled_sockets.get(inbound_socket) == zmq.POLLIN:
                            message = inbound_socket.recv_multipart()
                            break

                self.process_inbound_message(message, origin_broker=inbound_socket.broker)

    def send_outbound_message(self, socket, event): # Default instantiation
        raise NotImplementedError("Please Implement method 'send_outbound_message'")

    def process_inbound_message(self, message, *args, **kwargs): # Default instantiation, just a raw echo
        raise NotImplementedError("Please Implement method 'process_inbound_message'")
        
    def verify_brokers(self): # Used to process verification messages
        raise NotImplementedError("Please Implement method 'verify_brokers'")

    def send_heartbeats(self):
        raise NotImplementedError("Please Implement method 'send_heartbeats'")

class MDPClient(MDPActor):

    client = None

    def __init__(self, name, *args, **kwargs):
        super(MDPClient, self).__init__(name, *args, **kwargs)

    def send_outbound_message(self, socket, event):
        try:
            request_id = event['header']['event_id'] # Set for broker logging so we can trace the path of an event easily
            service = event['header']['service']
            self.logger.info("Sending event to service '{0}'".format(service), event_id=event['header']['event_id'])
            message = [request_id, b"{0}".format(event)]
            self.send(service, message, broker_socket=socket)
        except Exception as err:
            self.logger.error("Unable to find necessary chains: {0}".format(err))

    def verify_brokers(self):
        while self.loop():
            self.broker_manager.send_verification_requests(MDPDefinition.C_CLIENT)
            gevent.sleep(1)

    def process_inbound_message(self, message, *args, **kwargs):
        if message:
            assert len(message) >= 3
                
            empty = message.pop(0)
            header = message.pop(0)
            assert MDPDefinition.C_CLIENT == header

            command = message.pop(0)

            if command == MDPDefinition.B_HEARTBEAT:
                self.logger.info("Got heartbeat: {0}".format(message))
            elif command == MDPDefinition.B_VERIFICATION_RESPONSE:
                self.logger.info("Received Verification Response from {0}".format(message))
                self.broker_manager.verify_broker(message.pop(0))
            elif command == MDPDefinition.W_REPLY:
                empty = message.pop(0)
                request_identity = message.pop(0)

                event = literal_eval(message[0])
                self.logger.info("Received reply from broker", event_id=event['header']['event_id'])
                self.send_event(event)

    def set_broker(self, broker_socket=None):
        if broker_socket is not None:
            self.broker_socket = broker_socket

    def send(self, service, request, command=None, broker_socket=None, *args, **kwargs):
        command = command or kwargs.get('command', None) or MDPDefinition.C_REQUEST
        broker_socket = broker_socket or kwargs.get('broker_socket', None)
        if broker_socket is not None:
            """Send request to broker
            """
            if not isinstance(request, list):
                request = [request]

            # Prefix request with protocol frames
            # Frame 0: empty (REQ emulation)
            # Frame 1: "MDPCxy" (six bytes, MDP/Client x.y)
            # Frame 2: Command (See MDPDefinition)
            # Frame 3: Service name (printable string)

            request = ['', MDPDefinition.C_CLIENT, command, service] + request
            broker_socket.send_multipart(request)

    def send_heartbeats(self):
        pass

class MDPWorker(MDPActor):

    service = None
    requests = None

    def __init__(self, name, service, *args, **kwargs):
        super(MDPWorker, self).__init__(name, *args, **kwargs)
        self.service = service
        self.requests = {}

    def verify_brokers(self):
        while self.loop():
            self.broker_manager.send_verification_requests(MDPDefinition.W_WORKER, message=self.service)
            gevent.sleep(1)

    def process_inbound_message(self, message, *args, **kwargs):
        origin_broker = kwargs.get('origin_broker', None) or None
        if message is not None:
            assert len(message) >= 3

            empty = message.pop(0)
            assert empty == ''

            header = message.pop(0)
            assert header == MDPDefinition.W_WORKER

            command = message.pop(0)
            if command == MDPDefinition.W_REQUEST:
                return_address = message.pop(0)
                empty = message.pop(0)
                request_id = message.pop(0)
                event = literal_eval(message.pop(0))

                self.requests[request_id] = Request(return_address, origin_broker)

                self.send_event(event)

            elif command == MDPDefinition.B_VERIFICATION_RESPONSE:
                self.logger.info("Received Verification Response from {0}".format(message))
                self.broker_manager.verify_broker(message.pop(0))
            elif command == MDPDefinition.W_HEARTBEAT:
                # Do nothing for heartbeats
                pass
            elif command == MDPDefinition.W_DISCONNECT:
                self.logger.info("Received disconnect command from {0}".format(message))
                self.broker_manager.disconnect_broker(origin_broker.identity)
            else:
                pass

    def send_outbound_message(self, socket, event):
        request_id = event['header']['wsgi']['request_id']
        request = self.requests.get(request_id)

        if request is not None:
            broker = request.origin_broker
            return_address = request.return_address

            message = ['', MDPDefinition.W_WORKER, MDPDefinition.W_REPLY, return_address, '', event['header']['event_id'], b"{0}".format(event)]

            if broker is not None:                  # Prioritize the originating broker first
                try:
                    broker.outbound_socket.send_multipart(message)
                    self.logger.info("Sent reply through originating broker", event_id=event['header']['event_id'])
                except zmq.ZMQError:
                    socket.send_multipart(message)  # Use the current broker in the round-robin rotation
                    self.logger.info("Sent reply through non-originating broker", event_id=event['header']['event_id'])
        else:
            self.logger.error("Received event response but was unable to find client return address: {0}".format(event), event_id=event['header']['event_id'])


    def send_heartbeats(self):
        self.broker_manager.send_heartbeats(message=['', MDPDefinition.W_WORKER, MDPDefinition.W_HEARTBEAT, self.socket_identity])


class Request(object):

    return_address = None       # The socket id of the originating client
    origin_broker = None        # The original broker this message was received through

    def __init__(self, return_address, origin_broker):
        self.return_address = return_address
        self.origin_broker = origin_broker
