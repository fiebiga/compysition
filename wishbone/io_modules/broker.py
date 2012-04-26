#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  io.py
#  
#  Copyright 2012 Jelle Smet development@smetj.net
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
#  

import logging
from amqplib import client_0_8 as amqp
from wishbone.toolkit import QueueFunctions
from gevent import Greenlet, sleep, spawn
from gevent.queue import Queue
from gevent import monkey; monkey.patch_all()

class Broker(Greenlet, QueueFunctions):
    '''Creates an object doing all broker I/O.  It's meant to be resillient to disconnects and broker unavailability.
    Data going to the broker goes into Broker.outgoing_queue.  Data coming from the broker is submitted to the scheduler_callback method'''
    
    def __init__(self, name, block, host, vhost, username, password, consume_queue='wishbone_in', produce_exchange='wishbone_out', routing_key='wishbone' ):
        Greenlet.__init__(self)
        self.logging = logging.getLogger( 'Broker' )
        self.name = 'Broker'
        self.logging.info('Initiated')
        self.host=host
        self.vhost=vhost
        self.username=username
        self.password=password
        self.consume_queue = consume_queue
        self.produce_exchange = produce_exchange
        self.routing_key = routing_key
        self.block = block
        self.outbox=Queue(None)
        self.inbox=Queue(None)
        self.connected=False

    def __setup(self):
        self.conn = amqp.Connection(host="%s:5672"%(self.host), userid=self.username,password=self.password, virtual_host=self.vhost, insist=False)
        self.incoming = self.conn.channel()
        self.outgoing = self.conn.channel()
        self.logging.info('Connected to broker')
        
    def submitBroker(self):
        while self.block() == True:
            while self.connected == True:
                while self.outbox.qsize() > 0:
                    try:
                        self.logging.info('Submitting data to broker')
                        self.produce(self.outbox.get())
                    except:
                        break
                sleep(1)
            sleep(1)
                                
    def _run(self):
        self.logging.info('Started')
        night=0.5
        outgoing = spawn ( self.submitBroker )

        while self.block() == True:
            while self.connected==False:
                try:
                    if night < 512:
                        night *=2
                    self.__setup()
                    self.incoming.basic_consume(queue=self.consume_queue, callback=self.consume, consumer_tag='request')
                    self.connected=True
                    night=0.5
                except Exception as err:
                    self.connected=False
                    self.logging.warning('Connection to broker lost. Reason: %s. Try again in %s seconds.' % (err,night) )
                    sleep(night)
            while self.block() == True and self.connected == True:
                try:
                    self.incoming.wait()
                except Exception as err:
                    self.logging.warning('Connection to broker lost. Reason: %s' % err )
                    self.connected = False
                    self.incoming.close()
                    self.conn.close()
                    break
        
    def consume(self,doc):
        self.sendData({'header':{},'data':doc.body}, queue='inbox')
        self.logging.info('Data received from broker.')
        self.incoming.basic_ack(doc.delivery_tag)
        
    def produce(self,message):
        if message["header"].has_key('broker_exchange') and message["header"].has_key('broker_key'):            
            if self.connected == True:
                msg = amqp.Message(message['data'])
                msg.properties["delivery_mode"] = 2
                self.outgoing.basic_publish(msg,exchange=message['header']['broker_exchange'],routing_key=message['header']['broker_key'])
            else:
                raise Exception('Not Connected to broker')
        else:
            self.logging.warn('Received data for broker without exchange or key information in header. Purged.')

    def shutdown(self):
        self.logging.info('Shutdown')
