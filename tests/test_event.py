import unittest
import json
from lxml import etree
from collections import OrderedDict, defaultdict
from contextlib import contextmanager

from collections import Mapping

from compysition.errors import ResourceNotFound, InvalidEventDataModification
from compysition.event import HttpEvent, Event, CompysitionException, XMLEvent, JSONEvent

conversion_classes = [str, etree._Element, etree._ElementTree, etree._XSLTResultTree, dict, list, OrderedDict, None.__class__]

class TestEvent(unittest.TestCase):
    def setUp(self):
        self.event = Event(data={'foo': 'bar'}, meta_id='123456abcdef')

    def test_distinct_meta_and_event_ids(self):
        self.assertNotEqual(self.event.event_id, self.event.meta_id)


class TestHttpEvent(unittest.TestCase):
    def test_default_status(self):
        self.event = HttpEvent(data='quick brown fox')
        self.assertEquals(self.event.status, (200, 'OK'))

    def test_setting_status_tuple(self):
        error = (404, 'Not Found')
        self.event = HttpEvent(data='quick brown fox')
        self.event.status = error
        self.assertEquals(self.event.status, error)

    def test_setting_status_string_space_delimited(self):
        error = '404 Not Found'
        self.event = HttpEvent(data='quick brown fox')
        self.event.status = error
        self.assertEquals(self.event.status, (404, 'Not Found'))

    def test_setting_status_string_dash_delimited(self):
        error = '404-Not Found'
        self.event = HttpEvent(data='quick brown fox')
        self.event.status = error
        self.assertEquals(self.event.status, (404, 'Not Found'))

    def test_resource_not_found_status_updated(self):
        self.event = HttpEvent()
        self.event.error = ResourceNotFound()
        self.assertEquals(self.event.status, (404, 'Not Found'))

    def test_internal_server_error(self):
        self.event = HttpEvent()
        self.event.error = CompysitionException()
        self.assertEquals(self.event.status, (500, 'Internal Server Error'))

    def test_xml_to_json_single_element_default_to_dict(self):
        sample_xml = """
            <root>
                <sample_item>
                    <stuff>45</stuff>
                </sample_item>
            </root>
        """
        event = XMLEvent(data=sample_xml)
        json_event = event.convert(JSONEvent)
        assert isinstance(json_event.data['root']['sample_item'], Mapping)
        assert json_event.data['root']['sample_item']['stuff'] == '45'

    def test_xml_to_json_single_element_should_force_list(self):
        sample_xml = """
            <root>
                <sample_item force_list="True">
                    <stuff>45</stuff>
                </sample_item>
            </root>
        """
        event = XMLEvent(data=sample_xml)
        json_event = event.convert(JSONEvent)
        assert isinstance(json_event.data['root']['sample_item'], list)
        assert json_event.data['root']['sample_item'][0]['stuff'] == '45'

    def test_xml_to_json_multiple_element_default_to_list(self):
        sample_xml = """
            <root>
                <sample_item>
                    <stuff>45</stuff>
                </sample_item>
                <sample_item>
                    <stuff>45</stuff>
                </sample_item>
                <sample_item>
                    <stuff>45</stuff>
                </sample_item>
            </root>
        """
        event = XMLEvent(data=sample_xml)
        json_event = event.convert(JSONEvent)
        assert isinstance(json_event.data['root']['sample_item'], list)
        assert len(json_event.data['root']['sample_item']) == 3

    def test_xml_to_json_multiple_element_should_force_list(self):
        sample_xml = """
            <root>
                <sample_item force_list="True">
                    <stuff>45</stuff>
                </sample_item>
                <sample_item>
                    <stuff>45</stuff>
                </sample_item>
                <sample_item>
                    <stuff>45</stuff>
                </sample_item>
            </root>
        """
        event = XMLEvent(data=sample_xml)
        json_event = event.convert(JSONEvent)
        assert isinstance(json_event.data['root']['sample_item'], list)
        assert json_event.data['root']['sample_item'][2]['stuff'] == '45'
        assert '@force_list' not in json_event.data['root']['sample_item'][0]


    def test_json_to_xml_simple(self):
        sample_json = """
        {"apple": 1}
        """

        e = JSONEvent(data=sample_json)
        xml_event = e.convert(XMLEvent)
        assert xml_event.data_string() == '<apple>1</apple>'

    def test_json_to_xml_to_json_nesting(self):
        sample_json = """
        {"candy": [
            {"apple": 2},
            {"grape": 3}
            ]
        }
        """

        XML_VERSION = ''.join([
        '<jsonified_envelope>',
            '<candy>',
                '<apple>2</apple>',
            '</candy>',
            '<candy>',
                '<grape>3</grape>',
            '</candy>',
        '</jsonified_envelope>',
        ])

        e = JSONEvent(data=sample_json)
        xml_event = e.convert(XMLEvent)
        assert xml_event.data_string() == XML_VERSION

        json_event = xml_event.convert(JSONEvent)
        # check that jsonified_envelope has been removed and data is correct.
        assert 'candy' in json_event.data
        # The type changed from int to str but that's not really avoidable
        assert json_event.data['candy'][0]['apple'] == '2'
        assert json_event.data['candy'][1]['grape'] == '3'


parser = etree.XMLParser(remove_blank_text=True)
#used to ignore spacing differences and look at basic XML structure
def xml_formatter(xml_str):
    return etree.tostring(etree.XML(xml_str, parser=parser))

#used to ignore spacing differences and look at basic JSON structure
def json_formatter(json_str):
    return json.dumps(json.loads(json_str))


@contextmanager
def throws_excpetion(*exceptions):
    exceptions = (Exception) if len(exceptions) == 0 else exceptions
    try:
        yield
        assert False
    except exceptions:
        pass

class TestXMLEvent(unittest.TestCase):

    def test_conversion_classes(self):
        current_conversion_classes = XMLEvent().conversion_methods.keys()
        assert len(current_conversion_classes) == len(conversion_classes)
        for cur_conv_meth in current_conversion_classes:
            assert cur_conv_meth in conversion_classes

    def test_json_conversion_methods(self):
        src = {"my_data":123}
        event = XMLEvent(data=src)
        assert event.data_string() == xml_formatter("<my_data>123</my_data>")
    
        src = {"my_data":{"lvl1":[1,2,3]}}
        event = XMLEvent(data=src)
        assert event.data_string() == xml_formatter("<my_data><lvl1>1</lvl1><lvl1>2</lvl1><lvl1>3</lvl1></my_data>")
        
        src = {"my_data":{"lvl1":1}}
        event = XMLEvent(data=src)
        assert event.data_string() == xml_formatter("<my_data><lvl1>1</lvl1></my_data>")

        src = {"my_data":{"lvl1":1, "@my_attr": "type"}}
        event = XMLEvent(data=src)
        assert event.data_string() == xml_formatter("<my_data my_attr='type'><lvl1>1</lvl1></my_data>")

        src = {"lvl1":[1,2,3]}
        event = XMLEvent(data=src)
        assert event.data_string() == xml_formatter("<jsonified_envelope><lvl1>1</lvl1><lvl1>2</lvl1><lvl1>3</lvl1></jsonified_envelope>")

        src = [1,2,3]
        event = XMLEvent(data=src)
        assert event.data_string() == xml_formatter("<jsonified_envelope><jsonified_envelope>1</jsonified_envelope><jsonified_envelope>2</jsonified_envelope><jsonified_envelope>3</jsonified_envelope></jsonified_envelope>")

        src = {}
        with throws_excpetion(InvalidEventDataModification):
            event = XMLEvent(data=src)
        #ATTENTION
        # I think this should be true instead
        #assert event.data_string() == xml_formatter("<jsonified_envelope/>")

    def test_str_conversion_methods(self):
        src = "<my_data my_attr='type'>123</my_data>"
        event = XMLEvent(data=src)
        assert event.data_string() == xml_formatter("<my_data my_attr='type'>123</my_data>")

        src = ""
        with throws_excpetion(InvalidEventDataModification):
            event = XMLEvent(data=src)
        #ATTENTION
        # I think this should be true instead
        #assert event.data_string() == xml_formatter("<data/>")
    
        src = json_formatter('{"test":"ok"}')
        with throws_excpetion(InvalidEventDataModification):
            event = XMLEvent(data=src)

        src = "some random text"
        with throws_excpetion(InvalidEventDataModification):
            event = XMLEvent(data=src)

        src = "<element><invalid_xml></element>"
        with throws_excpetion(InvalidEventDataModification):
            event = XMLEvent(data=src)

        src = "<element>"
        with throws_excpetion(InvalidEventDataModification):
            event = XMLEvent(data=src)

    def test_none_conversion_methods(self):
        src = None
        event = XMLEvent(data=src)
        assert event.data_string() == xml_formatter("<root/>")
        #ATTENTION
        # I think one of these should be true instead
        #assert event.data_string() == xml_formatter("<data/>")

    def test_xml_conversion_methods(self):
        src = etree.fromstring(xml_formatter("<my_data my_attr='type'>123</my_data>"))
        event = XMLEvent(data=src)
        assert event.data_string() == xml_formatter("<my_data my_attr='type'>123</my_data>")
    
    def test_error_string(self):
        event = XMLEvent()
        event.error = InvalidEventDataModification(message="Oops Something Went Wrong")
        assert xml_formatter(event.error_string()) == xml_formatter("<errors><error><message>Oops Something Went Wrong</message></error></errors>")
        
        event = XMLEvent()
        event.error = InvalidEventDataModification(message=["Oops Something Went Wrong", "Oops Something Else Went Wrong Too"])
        assert xml_formatter(event.error_string()) == xml_formatter("<errors><error><message>Oops Something Went Wrong</message></error><error><message>Oops Something Else Went Wrong Too</message></error></errors>")

        event = XMLEvent()
        event.error = InvalidEventDataModification(message="Oops Something Went Wrong", code="555")
        assert xml_formatter(event.error_string()) == xml_formatter("<errors><error><message>Oops Something Went Wrong</message><code>555</code></error></errors>")

        event = XMLEvent()
        event.error = InvalidEventDataModification(message="Oops Something Went Wrong", code=555)
        with throws_excpetion(TypeError):
            event.error_string()
        #ATTENTION
        # I don't think this should throw and error
        # Instead I think this should be true
        #assert xml_formatter(event.error_string()) == xml_formatter("<errors><error><message>Oops Something Went Wrong</message><code>555</code></error></errors>")

        event = XMLEvent()
        event.error = InvalidEventDataModification(message="Oops Something Went Wrong", code="555", override="123")
        assert event.error_string() == "123"

        src = xml_formatter("<my_data my_attr='type'>123</my_data>")
        event = XMLEvent()
        event.error = InvalidEventDataModification(message="Oops Something Went Wrong", code="555", override=src)
        assert xml_formatter(event.error_string()) == xml_formatter("<my_data my_attr='type'>123</my_data>")
        
        src = etree.fromstring(xml_formatter("<my_data my_attr='type'>123</my_data>"))
        event = XMLEvent()
        event.error = InvalidEventDataModification(message="Oops Something Went Wrong", code="555", override=src)
        assert xml_formatter(event.error_string()) == xml_formatter("<errors><error><message>Oops Something Went Wrong</message><code>555</code></error></errors>")
        #ATTENTION
        # I think this should be true instead
        #assert xml_formatter(event.error_string()) == xml_formatter("<my_data my_attr='type'>123</my_data>")

        src = {"my_data":{"lvl1":1, "@my_attr": "type"}}
        event = XMLEvent()
        event.error = InvalidEventDataModification(message="Oops Something Went Wrong", code="555", override=src)
        assert event.error_string() == {"my_data":{"lvl1":1, "@my_attr": "type"}}
        #ATTENTION
        # I think this should be a string vs a json object
        #assert json_formatter(event.error_string()) == json_formatter("<my_data my_attr='type'>123</my_data>")


class TestJSONEvent(unittest.TestCase):

    def test_conversion_classes(self):
        current_conversion_classes = JSONEvent().conversion_methods.keys()
        assert len(current_conversion_classes) == len(conversion_classes)
        for cur_conv_meth in current_conversion_classes:
            assert cur_conv_meth in conversion_classes

    def test_json_conversion_methods(self):
        src = {"test":"ok"}
        event = JSONEvent(data=src)
        assert event.data_string() == json_formatter(json.dumps({"test":"ok"}))

        src = {"test":"ok","test2":1234}
        event = JSONEvent(data=src)
        assert event.data_string() == json_formatter(json.dumps({"test":"ok","test2":1234}))

        src = {"test":{"ok":"data"},"test2":[1,2,3,4]}
        event = JSONEvent(data=src)
        assert event.data_string() == json_formatter(json.dumps({"test":{"ok":"data"},"test2":[1,2,3,4]}))

        src = [1,2,3,4]
        event = JSONEvent(data=src)
        assert event.data_string() == json_formatter(json.dumps([1,2,3,4]))

        src = {}
        event = JSONEvent(data=src)
        assert event.data_string() == json_formatter(json.dumps({}))

    def test_xml_conversion_methods(self):
        '''
            Not implemented but a way to translate numbers would be nice
        '''
        
        src = etree.fromstring("<my_data>123</my_data>")
        event = JSONEvent(data=src)
        assert event.data_string() == json_formatter(json.dumps({"my_data":"123"}))

        src = etree.fromstring("<my_data><lvl1>1</lvl1><lvl1>2</lvl1><lvl1>3</lvl1></my_data>")
        event = JSONEvent(data=src)
        assert event.data_string() == json_formatter(json.dumps({"my_data":{"lvl1":["1","2","3"]}}))

        src = etree.fromstring("<my_data><lvl1>1</lvl1></my_data>")
        event = JSONEvent(data=src)
        assert event.data_string() == json_formatter(json.dumps({"my_data":{"lvl1":"1"}}))

        src = etree.fromstring("<my_data my_attr='type'><lvl1>1</lvl1></my_data>")
        event = JSONEvent(data=src)
        assert event.data_string() == json_formatter(json.dumps({"my_data":{"lvl1":"1", "@my_attr": "type"}}))

        src = etree.fromstring("<jsonified_envelope><lvl1>1</lvl1><lvl1>2</lvl1><lvl1>3</lvl1></jsonified_envelope>")
        event = JSONEvent(data=src)
        assert event.data_string() == json_formatter(json.dumps({"lvl1":["1","2","3"]}))

        src = etree.fromstring("<jsonified_envelope><jsonified_envelope>1</jsonified_envelope><jsonified_envelope>2</jsonified_envelope><jsonified_envelope>3</jsonified_envelope></jsonified_envelope>")
        event = JSONEvent(data=src)
        assert event.data_string() == json_formatter(json.dumps({"jsonified_envelope":["1","2","3"]}))
        #ATTENTION
        # I think this should be true instead to reverse the functionality of XMLEvent conversion
        #assert event.data_string() == json_formatter(json.dumps(["1","2","3"]))

        src = etree.fromstring("<jsonified_envelope/>")
        event = JSONEvent(data=src)
        assert event.data_string() == 'null'
        #ATTENTION
        # I think one of these should be true instead (preferably the first)
        #assert event.data_string() == json_formatter(json.dumps({}))
        #assert event.data_string() == None

        src = etree.fromstring("<my_data force_list=''>123</my_data>")
        event = JSONEvent(data=src)
        assert event.data_string() == json_formatter(json.dumps({"my_data":[{"#text":"123"}]}))
        #ATTENTION
        # I feel like this would be more usable
        #assert event.data_string() == json_formatter(json.dumps({"my_data":["123"]}))
        
        src = etree.fromstring("<my_data force_list=''><level1>123</level1></my_data>")
        event = JSONEvent(data=src)
        assert event.data_string() == json_formatter(json.dumps({"my_data":[{"level1":"123"}]}))
        
    def test_str_conversion_methods(self):
        src = json.dumps({"my_data":"ok"})
        event = JSONEvent(data=src)
        assert event.data_string() == json_formatter(json.dumps({"my_data":"ok"}))

        src = ""
        with throws_excpetion(InvalidEventDataModification):
            event = JSONEvent(data=src)
        #ATTENTION
        # I think this should be true instead
        #assert event.data_string() == json_formatter(json.dumps({}))

        src = "some random text"
        with throws_excpetion(InvalidEventDataModification):
            event = JSONEvent(data=src)

        src = "<some_xml/>"
        with throws_excpetion(InvalidEventDataModification):
            event = JSONEvent(data=src)

        src = '{"invalid: "json"}'
        with throws_excpetion(InvalidEventDataModification):
            event = JSONEvent(data=src)

    def test_none_conversion_methods(self):
        src = None
        event = JSONEvent(data=src)
        assert event.data_string() == json_formatter(json.dumps({}))

    def test_error_string(self):
        event = JSONEvent()
        event.error = InvalidEventDataModification(message="Oops Something Went Wrong")
        assert json_formatter(event.error_string()) == json_formatter(json.dumps([{"override":None, "message":"Oops Something Went Wrong", "code": None}]))
        #ATTENTION
        # Probably don't need to return "override" data or null code data        

        event = JSONEvent()
        event.error = InvalidEventDataModification(message=["Oops Something Went Wrong", "Oops Something Else Went Wrong Too"])
        assert json_formatter(event.error_string()) == json_formatter(json.dumps([{"override":None, "message":"Oops Something Went Wrong", "code": None}, {"override":None, "message":"Oops Something Else Went Wrong Too", "code": None}]))

        event = JSONEvent()
        event.error = InvalidEventDataModification(message="Oops Something Went Wrong", code=555)
        assert json_formatter(event.error_string()) == json_formatter(json.dumps([{"override":None, "message":"Oops Something Went Wrong", "code": 555}]))
        
        event = JSONEvent()
        event.error = InvalidEventDataModification(message="Oops Something Went Wrong", code="555")
        assert json_formatter(event.error_string()) == json_formatter(json.dumps([{"override":None, "message":"Oops Something Went Wrong", "code": "555"}]))
        
        event = JSONEvent()
        event.error = InvalidEventDataModification(message="Oops Something Went Wrong", code="555", override="123")
        assert event.error_string() == '"123"'
        #ATTENTION
        # This seems odd probably should be without the added quotes
        #assert event.error_string() == '123'

        src = json_formatter(json.dumps({"my_data":123}))
        event = JSONEvent()
        event.error = InvalidEventDataModification(message="Oops Something Went Wrong", code="555", override=src)
        assert json_formatter(event.error_string()) == '"{\\\"my_data\\\": 123}"'
        #ATTENTION
        # This seems odd probably should be without the added quotes
        #assert json_formatter(event.error_string()) == json_formatter(json.dumps({"my_data":123}))
        
        src = {"my_data":123}
        event = JSONEvent()
        event.error = InvalidEventDataModification(message="Oops Something Went Wrong", code="555", override=src)
        assert json_formatter(event.error_string()) == json_formatter(json.dumps({"my_data":123}))
        
        src = etree.fromstring(xml_formatter("<my_data my_attr='type'>123</my_data>"))
        event = JSONEvent()
        event.error = InvalidEventDataModification(message="Oops Something Went Wrong", code="555", override=src)
        with throws_excpetion(TypeError):
            json_formatter(event.error_string())
