from lxml import etree
from time import time

class MatchedEvent(object):
    
    aggregate_xml = None # The data appended under the new matched root
    inboxes_reported = None # A dictionary containing inbox names as the key, and True|False for reported vs not reported for this event

    def __init__(self, root_node_name, inboxes):
        self.inboxes_reported = {}
        self.aggregate_xml = etree.Element(root_node_name)
        self.created = time()
        if isinstance(inboxes, list):
            for inbox in inboxes:
                self.inboxes_reported[inbox] = False
        else:
            raise Exception("Must provide inboxes as a list")

    def report_inbox(self, inbox_name, xml_data):
        if not self.inboxes_reported[inbox_name]:
            xml = etree.fromstring(xml_data)
            try:
                self.aggregate_xml.append(xml)
                self.inboxes_reported[inbox_name] = True
            except:
                raise Exception("Malformed data found while attempting to aggregate xml")
        else:
            raise Exception("Inbox {0} already reported for event. Ignoring".format(inbox_name))    

    def all_inboxes_reported(self):
        for key in self.inboxes_reported:
            if not self.inboxes_reported[key]:
                return False

        return True

    def get_aggregate_xml(self):
        return etree.tostring(self.aggregate_xml)