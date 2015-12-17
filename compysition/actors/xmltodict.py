from __future__ import absolute_import

from compysition.actor import Actor
import xmltodict

class XMLToDict(Actor):
    """
    Actor implementation of the xmltodict lib
        - Input: <XML>
        - Output: <Dict>
    """

    def __init__(self, name, *args, **kwargs):
        self.xmltodict_kwargs = kwargs
        super(XMLToDict, self).__init__(name, *args, **kwargs)

    def consume(self, event, *args, **kwargs):
        try:
            dict_data = xmltodict.parse(event.data, **self.xmltodict_kwargs)
            if dict_data is not None:
                event.data = dict_data
            else:
                raise Exception("Incoming data was not valid XML")
        except Exception as err:
            self.logger.error("Unable to convert XML: {0}".format(err), event=event)

        self.send_event(event)
