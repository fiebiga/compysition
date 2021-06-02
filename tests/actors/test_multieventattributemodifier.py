import unittest

from compysition.actors.multieventattributemodifier import MultiEventAttributeModifier, ModifyDefinition, LookupModifyDefinition
from compysition.event import JSONEvent, Event
from compysition.testutils.test_actor import TestActorWrapper

class TestMultiEventAttributeModifier(unittest.TestCase):

    def test_modify_defintion(self):
        key = "foo"
        orig_value = "the_far_car"
        new_value = "not_the_far_car"
        actor = TestActorWrapper(MultiEventAttributeModifier('actor', definitions=[
            ModifyDefinition(key=key, value=new_value)
            ]))
        _input = Event(**{key: orig_value})
        self.assertEquals(getattr(_input, key, None), orig_value)
        actor.input = _input
        output = actor.output
        self.assertEquals(getattr(output, key, None), new_value)


        key = "foo"
        key_chain = '{key}/test/the/route'.format(key=key)
        orig_value = "the_far_car"
        new_value = "not_the_far_car"
        actor = TestActorWrapper(MultiEventAttributeModifier('actor', definitions=[
            ModifyDefinition(key=key_chain, value=new_value)
            ]))
        _input = Event(**{key: {'test':{'the':{'route':orig_value}}}})
        self.assertEquals(getattr(_input, key)['test']['the']['route'], orig_value)
        actor.input = _input
        output = actor.output
        self.assertEquals(getattr(output, key)['test']['the']['route'], new_value)

    def test_lookup_modify_defintion(self):
        key = "foo"
        orig_value = "the_far_car"
        new_value = "not_the_far_car"
        data = {'test':{'the': {'route': new_value}}}
        actor = TestActorWrapper(MultiEventAttributeModifier('actor', definitions=[
            LookupModifyDefinition(key=key, value=['_data', 'test', 'the', 'route'])
            ]))
        _input = JSONEvent(**{key: orig_value, '_data': data})
        self.assertEquals(getattr(_input, key, None), orig_value)
        actor.input = _input
        output = actor.output
        self.assertEquals(getattr(output, key, None), new_value)

    def test_multi_defintions(self):
        key1, orig_value1, new_value1 = "foo", 'val1', 'val2'
        key2, orig_value2, new_value2 = "foo2", 'val3', 'val4'
        data = {'test':{'the': {'route': new_value2}}}
        actor = TestActorWrapper(MultiEventAttributeModifier('actor', definitions=[
            ModifyDefinition(key=key1, value=new_value1),
            LookupModifyDefinition(key=key2, value=['_data', 'test', 'the', 'route'])
            ]))
        _input = JSONEvent(**{
            key1: orig_value1,
            key2: orig_value2, 
            '_data': data
        })
        self.assertEquals(getattr(_input, key1, None), orig_value1)
        self.assertEquals(getattr(_input, key2, None), orig_value2)
        actor.input = _input
        output = actor.output
        self.assertEquals(getattr(output, key1, None), new_value1)
        self.assertEquals(getattr(output, key2, None), new_value2)