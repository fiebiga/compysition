import re

from lxml import etree

from .util.xpath import XPathLookup
from compysition.actor import Actor
from compysition.event import XMLEvent, JSONEvent
from compysition.errors import MalformedEventData, CompysitionException

__all__ = ["MultiEventAttributeModifier", "ModifyDefinition", "LookupModifyDefinition"]

class _DictKeyChainMixin:
    def get_key_chain_value(self, event, value):
        #TODO: Redo this to not modify arrays
        keys = self.key.split(self.separator)
        event_key = keys.pop(0)
        if len(keys) == 0:
            event.set(event_key, value)
        else:
            current_step = event.get(event_key, None)
            if not current_step:
                current_step = {}
                event.set(event_key, current_step)

            try:
                while True:
                    try:
                        item = keys.pop(0)
                        if len(keys) > 0:
                            next_step = current_step[item]
                            current_step = next_step
                        else:
                            current_step[item] = value
                    except KeyError:
                        next_step = {} if len(keys) > 0 else value
                        current_step[item] = next_step
                        current_step = next_step
                    except IndexError:
                        break
            except Exception as err:
                self.logger.error("Unable to follow key chain. Ran into non-dict value of '{value}'".format(value=current_step), event=event)
                raise

        return event

class _SimpleLookupMixin:
    def _get_modify_value(self, event):
        return self.value

class _LookupMixin:
    def _get_modify_value(self, event):
        return event.lookup(self.value)

class MultiEventAttributeModifier(Actor):
    def __init__(self, name, definitions=[], *args, **kwargs):
        super(MultiEventAttributeModifier, self).__init__(name, *args, **kwargs)
        self.definitions = definitions
        for definition in definitions:
            definition.logger = self.logger

    def consume(self, event, *args, **kwargs):
        for definition in self.definitions:
            try:
                event = definition.modify(event)
            except Exception as err:
                raise MalformedEventData(err)
        self.send_event(event)

class _BaseModifyDefinition:
    def __init__(self, key='data', value={}, log_change=False, separator="/"):
        self.key = name if key is None else key
        self.value = value
        self.log_change = log_change
        self.separator = separator

    def modify(self, event):
        modify_value = self._get_modify_value(event)
        if self.log_change and get(self, 'logger', None) is not None:
            self.logger.info("Changed event.{key} to {value}".format(key=self.key, value=modify_value), event=event)
        return self.get_key_chain_value(event, modify_value)

class ModifyDefinition(_BaseModifyDefinition, _SimpleLookupMixin, _DictKeyChainMixin): pass
class LookupModifyDefinition(_BaseModifyDefinition, _LookupMixin, _DictKeyChainMixin): pass