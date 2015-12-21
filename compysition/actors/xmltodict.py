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

        - escape_xml (bool) (Default: False)
            | If set to True, a dict key or nested dict key that contains an XML-style string element will be
            | XML escaped. If False, that XML will be appended to the XML element node created from the dictionary key
            | as a literal XML tree
    """

    def __init__(self, name, *args, **kwargs):
        super(XMLToDict, self).__init__(name, *args, **kwargs)

    def consume(self, event, *args, **kwargs):
        try:
            dict_data = xmltodict.parse(event.data)
            if dict_data is not None:
                event.data = json.dumps(dict_data)
            else:
                raise Exception("Incoming data was not valid XML")
        except Exception as err:
            self.logger.error("Unable to convert XML: {0}".format(err), event=event)

        self.send_event(event)