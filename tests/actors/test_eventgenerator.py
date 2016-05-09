from compysition.actors import *
import unittest
from compysition.event import *
from utils.test_actor import TestActorWrapper


class TestEventGenerator(unittest.TestCase):

    def test_xmlevent_generation(self):
        actor = TestActorWrapper(EventGenerator("eventgenerator", interval=1, delay=0, event_class=XMLEvent))
        _output = actor.output
        self.assertIsInstance(_output, XMLEvent)

    def test_event_generation(self):
        actor = TestActorWrapper(EventGenerator("eventgenerator", interval=1, delay=0, event_class=Event))
        _output = actor.output
        self.assertIsInstance(_output, Event)

    def test_jsonevent_generation(self):
        actor = TestActorWrapper(EventGenerator("eventgenerator", interval=1, delay=0, event_class=JSONEvent))
        _output = actor.output
        self.assertIsInstance(_output, JSONEvent)

    def test_attribute_generation(self):
        actor = TestActorWrapper(EventGenerator("eventgenerator", interval=1, delay=0, event_class=Event, event_kwargs={"test_kwarg": "value"}))
        _output = actor.output
        self.assertEqual(_output.test_kwarg, "value")