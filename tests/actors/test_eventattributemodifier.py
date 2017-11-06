import unittest

from compysition.actors import JSONEventAttributeDelete
from compysition.event import JSONEvent

from compysition.testutils.test_actor import TestActorWrapper


class TestEventAttributeDelete(unittest.TestCase):

    def test_single_event_attribute(self):
        actor = TestActorWrapper(JSONEventAttributeDelete('actor', key_paths=[['foo']]))
        _input = JSONEvent(foo='foo')

        self.assertEqual(_input.foo, 'foo')
        actor.input = _input
        output = actor.output
        with self.assertRaises(AttributeError):
            output.foo

    def test_single_event_attribute_and_data_item(self):
        actor = TestActorWrapper(JSONEventAttributeDelete('actor', key_paths=[['foo'], ['data', 'bar']]))
        _input = JSONEvent(data={'bar': 'baz'}, foo='foo')

        self.assertEqual(_input.data, {'bar': 'baz'})
        actor.input = _input
        output = actor.output

        self.assertEqual(output.data, {})
        with self.assertRaises(AttributeError):
            output.foo

    def test_nested_data_item(self):
        actor = TestActorWrapper(JSONEventAttributeDelete('actor', key_paths=[['data', 'fruits', 'apple']]))
        _input = JSONEvent(data={'fruits': {'apple': 1, 'banana': 3}, 'count': 2})

        actor.input = _input
        output = actor.output
        self.assertEqual(output.data, {'count': 2, 'fruits': {'banana': 3}})
