from __future__ import absolute_import

from compysition.actor import Actor
import xmltodict
import json

class XMLToDict(Actor):
    """
    *Actor implementation of the dicttoxml lib. Converts an incoming dictionary to XML*

    Input/Output Types:
        - Input: <(str) XML>
        - Output: <(str) dict>

    Parameters:
        - name (REQ) (str)
            | Actor Name

        - flatten (Default: False) If true, the root element of the incoming XML will be stripped out, as a root
            node is not a requirement for a json object
    """

    def __init__(self, name, flatten=False, *args, **kwargs):
        self.flatten = flatten
        super(XMLToDict, self).__init__(name, *args, **kwargs)

    def consume(self, event, *args, **kwargs):
        try:
            dict_data = xmltodict.parse(event.data)
            if dict_data is not None:
                if self.flatten:
                    dict_data = dict_data[dict_data.keys()[0]]

                event.data = json.dumps(dict_data)
                self.logger.info("Successfully converted XML to Dict", event=event)
            else:
                raise Exception("Incoming data was not valid XML")
        except Exception as err:
            self.logger.error("Unable to convert XML: {0}".format(err), event=event)

        self.send_event(event)