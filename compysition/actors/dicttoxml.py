from __future__ import absolute_import

from compysition.actor import Actor
import dicttoxml

class DictToXML(Actor):
    """
    Actor implementation of the dicttoxml lib
        - Input: <Dict>
        - Output: <XML>
    """

    def __init__(self, name, *args, **kwargs):
        self.dicttoxml_kwargs = kwargs
        super(DictToXML, self).__init__(name, *args, **kwargs)

    def consume(self, event, *args, **kwargs):
        try:
            xml = dicttoxml.dicttoxml(event.data, **self.dicttoxml_kwargs)
            if xml is not None:
                event.data = xml
            else:
                raise Exception("Incoming data was not a dictionary")
        except Exception as err:
            self.logger.error("Unable to convert XML: {0}".format(err), event=event)

        self.send_event(event)
