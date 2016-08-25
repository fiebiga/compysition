import unittest
from compysition.event import *
from compysition.errors import InvalidEventDataModification


class TestEvent(unittest.TestCase):

    def setUp(self):
        self.event = Event(data={'foo': 'bar'}, meta_id='123456abcdef')

    def test_distinct_meta_and_event_ids(self):
        self.assertNotEqual(self.event.event_id, self.event.meta_id)


class TestHttpEvent(unittest.TestCase):

    def setUp(self):
        self.event = HttpEvent(data='quick brown fox')

    def test_basic_content_type(self):
        self.assertEqual(self.event.headers.get('Content-Type'), 'text/plain')


class TestJSONEvent(unittest.TestCase):

    def test_invalid_json_event_modification(self):
        self.assertRaises(InvalidEventDataModification, JSONEvent, data='cat')


class TestXMLHttpEvent(unittest.TestCase):

    def setUp(self):
        self.event = XMLHttpEvent(data={'cat': 'fat'})

    def test_xml_event_content_type(self):
        self.assertEqual(self.event.headers.get('Content-Type'), 'application/xml')


class TestJSONHttpEvent(unittest.TestCase):

    def setUp(self):
        self.event = JSONHttpEvent(data={'cat': 'fat'})

    def test_json_event_content_type(self):
        self.assertEqual(self.event.headers.get('Content-Type'), 'application/json')