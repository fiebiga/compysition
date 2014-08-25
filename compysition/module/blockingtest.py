from compysition import Actor
import gevent

class BlockingTest(Actor):
    '''
    Simple Actor designed to print an event to STDOUT every 2 seconds to test blocking
    in a any router configuration
    args:
        - log_entry (Default: False):   If true, will also submit an entry to the registered "Logging" module to test
            log write blocking
    '''
    
    def __init__(self, name, log_entry=False, *args, **kwargs):
        Actor.__init__(self, name, *args, **kwargs)
        self.log_entry = log_entry

    def preHook(self):
        gevent.spawn(self.go)

    def go(self):
        while not self.is_blocked():
            print "Router is not blocked"
            if self.log_entry:
                self.logging.info("Router is not blocked")
            gevent.sleep(2)

    def consume(self, event, *args, **kwargs):
        print("Received an event: {0}".format(event))
        print("Module event consumption is not being blocked")
        if self.log_entry:
            self.logging.info("Received an event: {0}".format(event))
            self.logging.info("Module event consumption is not being blocked")