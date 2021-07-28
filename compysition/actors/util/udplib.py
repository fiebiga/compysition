# A Simple UDP class

import socket
import time
import uuid
import zmq.green as zmq
import gevent

from gevent import event
from gevent.pool import Pool

PING_PORT_NUMBER    = 6999  # The UDP port to ping over
PING_INTERVAL       = 1.0   # The time between sending each ping (seconds)
PEER_EXPIRY         = 10   # How many pings a peer can miss before they are reaped
UUID_BYTES          = 32    # The number of bytes in the UUID
BURN_IN_PINGS       = 5     # The number of pings to wait before a master is determined from peers that report in that time
TIMESTAMP_BYTES     = 10    # The number of bytes in the timestamp

class UDP(object):
    """
    **An interface to handle the sending, receiving, and interpreting of a UDP broadcast**

    Parameters:

        - port (int):       The port to broadcast and receive over
        - address (str):    (Default: None) The local IP address. If None, it will attempt to determine it's own IP
        - broadcast (str):  (Default: None) The specific subnet to broadcast over. If set to none, it will default to 255.255.255.255

    """

    handle = None   # Socket for send/recv
    port = 0        # UDP port we work on
    address = ''    # Own address
    broadcast = ''  # Broadcast address

    def __init__(self, port, address=None, broadcast=None):
        if address is None:
            local_addrs = socket.gethostbyname_ex(socket.gethostname())[-1]
            for addr in local_addrs:
                if not addr.startswith('127'):
                    address = addr
        if broadcast is None:
            broadcast = ['255.255.255.255']
        elif not isinstance(broadcast, list):
            broadcast = [broadcast]

        self.address = address
        self.broadcasts = broadcast
        self.port = port

        self.handle = self.get_handle()

    def get_handle(self):
        handle = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

        # Ask operating system to let us do broadcasts from socket
        handle.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        # Allow socket to be resused by multiple processes
        handle.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Bind UDP socket to local port so we can receive pings
        handle.bind(('', self.port))

        return handle

    def send(self, buf):
        for broadcast in self.broadcasts:
            self.handle.sendto(buf, 0, (broadcast, self.port))

    def recv(self, service_length, uuid_length, timestamp_length):
        message, addrinfo = self.handle.recvfrom(service_length + uuid_length + timestamp_length)
        service = message[0:service_length]
        id = message[service_length:service_length + uuid_length]
        timestamp = message[service_length + uuid_length:service_length + uuid_length + timestamp_length]
        return (service, id, timestamp, addrinfo[0])


class Peer(object):
    
    uuid = None         # The uuid the peer broadcasted
    expires_at = None   # The time the peer will expire

    def __init__(self, uuid, ip, timestamp, expiry=None, interval=None):
        self.uuid = uuid
        self.ip = ip
        self.timestamp = timestamp
        self.expiry = expiry or PEER_EXPIRY
        self.interval = interval or PING_INTERVAL
        self.is_alive()

    def is_alive(self):
        """Reset the peers expiry time
        
        Call this method whenever we get any activity from a peer.
        """
        self.expires_at = time.time() + (self.expiry * self.interval)

class UDPInterface(object):
    """
    This class is the fully implemented connector that communicates over UDP multicast broadcasts to peers
    registered to the same port and service configuration.

    This class also deterministically elects a master in the peer group
    """
    
    udp = None                 # UDP object
    uuid = None                # Our UUID as binary blob
    peers = None               # Hash of known peers, fast lookup

    __master_methods = {
        "uuid": lambda peers, pn: sorted(peers, key=lambda peer: peer.uuid, reverse=True),
        "network": lambda peers, pn: sorted(peers, key=lambda peer: '{}{}'.format('1' if peer.ip.startswith(pn) else '0', peer.uuid), reverse=True),
        "oldest": lambda peers, pn: sorted(sorted(peers, key=lambda peer: peer.uuid, reverse=True), key=lambda peer: peer.timestamp, reverse=True),
        "youngest": lambda peers, pn: sorted(sorted(peers, key=lambda peer: peer.uuid, reverse=True), key=lambda peer: peer.timestamp),
        "network_then_oldest": lambda peers, pn: sorted(sorted(sorted(peers, key=lambda peer: peer.uuid, reverse=True), key=lambda peer: peer.timestamp, reverse=True), key=lambda peer: '1' if peer.ip.startswith(pn) else '0', reverse=True),
        "network_then_youngest": lambda peers, pn: sorted(sorted(sorted(peers, key=lambda peer: peer.uuid, reverse=True), key=lambda peer: peer.timestamp), key=lambda peer: '1' if peer.ip.startswith(pn) else '0', reverse=True),
    }

    def __init__(self, service, logger=None, interval=None, expiry=None, burn_in_pings=None, broadcast=None, master_method="uuid", master_priority_network=None):
        assert master_method in self.__master_methods
        if master_method in ["network", "network_then_oldest", "network_then_youngest"]:
            assert master_priority_network is not None
        self.created_timestamp = str(int(time.time()))
        self.master_method = master_method
        self.master_priority_network = master_priority_network

        self.pool = Pool()
        udpkwargs = {'port': PING_PORT_NUMBER}
        if broadcast is not None:
            udpkwargs['broadcast'] = broadcast
        self.udp = UDP(**udpkwargs)
        self.uuid = uuid.uuid4().hex.encode('utf8')
        self.poller = zmq.Poller()
        self.poller.register(self.udp.handle, zmq.POLLIN)
        self.service = service
        self.logger = logger

        self.expiry = expiry or PEER_EXPIRY
        self.interval = interval or PING_INTERVAL
        self.burn_in_pings = burn_in_pings or BURN_IN_PINGS;

        self.__master_block = event.Event()
        self.__master_block.clear()

        self.__block = event.Event()
        self.__block.clear()

        self.__burned_in = False

        self.__loop = event.Event()
        self.__loop = False
        self.__set_slave()
        self.peers = {}
        self.as_peer = Peer(self.uuid, self.udp.address, self.created_timestamp)

    
    def stop(self):
        self.__loop = False
    
    def start(self):
        self.__loop = True
        self.pool.spawn(self.run)
        self.pool.spawn(self.send_pings)
        self.pool.spawn(self.__burn_in_timer)

    def __burn_in_timer(self):
        """
        A method which exists to clear the block on master determination
        after a suitable burn in time. This is to prevent several instances being brought up at the same time
        recognizing as master and doing work as such
        """

        gevent.sleep(self.burn_in_pings * self.interval)
        self.__burned_in = True


    def block(self):
        self.__block.wait()

    def wait_until_master(self):
        '''Blocks until stop() is called.'''
        self.__master_block.wait()
    
    def send_pings(self, *args, **kwargs):
        while self.__loop:
            try:
                self.udp.send(self.service + self.uuid + self.created_timestamp)
                gevent.sleep(self.interval)
            except Exception as e:
                self.loop.stop()

    def run(self):
        while self.__loop:
            items = self.poller.poll(self.interval)
            if items:
                service, uuid, timestamp, address = self.udp.recv(len(self.service), UUID_BYTES, TIMESTAMP_BYTES)
                if service == self.service and uuid != self.uuid:
                    if uuid in self.peers:
                        self.peers[uuid].is_alive()
                    else:
                        self.peers[uuid] = Peer(uuid, address, timestamp, interval=self.interval, expiry=self.expiry)
                        self.log("New peer ({0}) discovered in '{1}' peer pool. (Total: {2})".format(uuid, self.service, len(self.peers) + 1))
            else:
                gevent.sleep(1)

            self.reap_peers()
            self.determine_master()
    
    def reap_peers(self):
        now = time.time()
        cur_peers = {}
        peer_cnt = len(self.peers) + 1
        for uuid, peer in self.peers.iteritems():
            if peer.expires_at < now:
                peer_cnt -= 1
                self.log("Reaping expired peer ({0}) from '{1}' peer pool. (Total remaining: {2})".format(peer.uuid, self.service, peer_cnt))
            else:
                cur_peers[uuid] = peer
        self.peers = cur_peers
    
    def determine_master(self):
        if self.__burned_in:
            if len(self.peers) > 0:
                peers = [peer for peer in self.peers.itervalues()] + [self.as_peer]
                sorted_peers = self.__master_methods[self.master_method](peers, self.master_priority_network)
                if sorted_peers[0].uuid != self.uuid:
                    if self.is_master():
                        self.log("Changing from master to slave")
                    self.__set_slave()
                else:
                    if self.is_slave():
                        self.log("Changing from slave to master")
                    self.__set_master()
            else:
                if self.is_slave():
                    self.log("Changing from slave to master")
                self.__set_master()

    def __set_slave(self):
        self.__is_master = False
        self.__master_block.clear()

    def __set_master(self):
        self.__is_master = True
        self.__master_block.set()

    def is_master(self):
        return self.__is_master

    def is_slave(self):
        return not self.__is_master

    def log(self, message):
        if self.logger is not None:
            self.logger.info(message)
        else:
            print(message)