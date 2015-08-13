import gevent.monkey
gevent.monkey.patch_all(thread=False)
from compysition import Actor
import traceback
import gevent
from compysition.actors.util.udplib import UDPInterface
import time
from configobj import ConfigObj

class UDPEventGenerator(Actor):
    """
    An actor that utilized a UDP interface to coordinate between other UDPEventGenerator actors
    running on its same subnet to coordinate a master/slave relationship of generating an event
    with the specified arguments and attributes. Only the master in the 'pool' of registered actors
    will generate an event at the specified interval
    """

    def __init__(self, name, service="default", interval=120, config_filepath=None, environment='default', event_kwargs={}, *args, **kwargs):
        super(UDPEventGenerator, self).__init__(name, *args, **kwargs)

        if config_filepath:
            try:
                config_obj = ConfigObj(config_filepath)
                environment = config_obj['general']['environment']
            except:
                self.logger.warn("Environment not found in {config_filepath}, using '{environment}'".format(config_filepath=config_filepath,
                                                                                                            environment=environment))
                environment = environment
        else:
            environment = environment

        self.event_kwargs = event_kwargs
        self.interval = interval
        self.generate_at = time.time()
        self.peers_interface = UDPInterface("{0}-{1}".format(service, environment), logger=self.logger)

    def pre_hook(self):
        self.peers_interface.start()
        self.threads.spawn(self.go)

    def refresh_interval(self, interval=None):
        if interval is None:
            interval = self.interval

        self.generate_at = time.time() + interval

    def should_generate_event(self):
        return time.time() > self.generate_at

    def go(self):
        self.peers_interface.wait_until_master()
        while self.loop():
            if self.peers_interface.is_slave():
                self.peers_interface.wait_until_master()
                self.refresh_interval(interval=(self.interval / 6)) # Wait some time to prevent dual polling after a failover

            if self.should_generate_event():
                self.generate_event()
            else:
                gevent.sleep(5)

    def generate_event(self):
        event = self.create_event(**self.event_kwargs)
        self.logger.info("Generating event", event=event)
        self.send_event(event)
        self.refresh_interval()

    def consume(self, event, *args, **kwargs):
        if self.peers_interface.is_master():
            self.generate_event()
        else:
            self.logger.warn("Received prompt to generate event, but actor is not the master in the pool", event=event)
