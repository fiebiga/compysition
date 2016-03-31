from __future__ import absolute_import

from compysition.actor import Actor
import json
from lxml import etree
from .util.dataformat import str_to_json
from xml.sax.saxutils import XMLGenerator
import xmltodict


class UnescapedDictXMLGenerator(XMLGenerator):
    """
    Simple class designed to enable the use of an unescaped functionality
    in the event that dictionary value data is already XML
    """

    def characters(self, content):
        try:
            etree.fromstring(content)
            self._write(content)
        except:
            XMLGenerator.characters(self, content)

class DictToXML(Actor):
    """
    *Actor implementation of the xmltodict lib (unparse). Converts an incoming dictionary to XML*
    Input(s)/Output Types:
        - Input: <(str) dict>
        - Input: <(str) json>
            | Refers to strict JSON standards, though this is implemented in python as a 'dict'
        - Input: <dict>
        - Input: <json>
            | Refers to strict JSON standards, though this is implemented in python as a 'dict'
        - Output: <(str) XML>

    Parameters:
        - name (REQ) (str)
            | Actor Name

        - escape_xml (bool) (Default: False)
            | If set to True, a dict key or nested dict key that contains an XML-style string element will be
            | XML escaped. If False, that XML will be retained in the XML element node created from the dictionary key
            | as a literal XML tree

        - mode (str<"data"|"properties"> (Default: "data")
            | If set to "data" it will convert the event data from dict to XML.
            | If set to "properties" it will take the internal event dict MINUS data,
            | and override data with the generated XML
    """

    def __init__(self, name, escape_xml=False, key=None, *args, **kwargs):
        # Override the dicttoxml xml_escape method with a simple echo
        if escape_xml:
            setattr(xmltodict, "XMLGenerator", UnescapedDictXMLGenerator)

        super(DictToXML, self).__init__(name, *args, **kwargs)
        self.input_types_processing_map.update({
            dict: self._process_dict_input
        })

        # TODO: Remove this once "all" is no longer universal to all Actors
        self.input_types_processing_map.pop("all", None)
        self.key = key or name

    def _process_dict_input(self, data):
        # Documents must have only 1 root
        if len(data) > 1:
            data = {self.key: data}

        return data

    def _process_str_input(self, data):
        data = str_to_json(data)
        return self._process_dict_input(data)

    def consume(self, event, *args, **kwargs):
        try:
            xml = self.convert(event)
            event.data = str(xml)
            self.logger.info("Successfully converted Dict to XML", event=event)
            self.send_event(event)
        except Exception as err:
            self.logger.error("Unable to convert XML: {0}".format(err), event=event)
            self.send_error(event)

    def convert(self, event):
        return xmltodict.unparse(event.data)

    @staticmethod
    def find_dict_paths(dict_, path=None):
        """
        This is currently unused. This was the original direction for enabling unescaped dict to xml transformations
        for dictionaries that contained values that were ALREADY xml, but I decided to go with the parser replacement
        for now instead. I kept this code in here because it's not a bad function to find dict paths, and I may
        switch to this method in the future after performance analysis
        """
        def concat_path(path, key):
            if path is None:
                return (key, )
            else:
                return tuple(list(path) + [key])

        for key, value in dict_.iteritems():
            if isinstance(value, dict):
                for result in DictToXML.find_dict_paths(value, concat_path(path, key)):
                    yield result
            else:
                try:
                    data = etree.fromstring(value)
                except:
                    data = None

                if data is not None:
                    yield (concat_path(path, key), data)

    def populate_dict_paths(self):
        pass


class PropertiesToXML(DictToXML):
    """
    *Subclass of DictToXml. Converts event properties to XML, rather than incoming data*
    """

    def __init__(self, *args, **kwargs):
        super(PropertiesToXML, self).__init__(*args, **kwargs)
        self.input_types_processing_map = {
            "all": self._process_all_input
        }

    def convert(self, event):
        properties_dict = {self.key: event.get_properties()}
        return xmltodict.unparse(properties_dict)