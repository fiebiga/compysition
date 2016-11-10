import unittest

from compysition.actors import JSONValidator
from compysition.event import JSONEvent
from compysition.testutils.test_actor import TestActorWrapper

jschema = """
{
  "$schema": "http://json-schema.org/draft-04/schema#",
  "description": "Validation for mysql timestamp",
  "type": "object",
  "properties": {
    "start": {
      "format": "mysql_timestamp"
    },
    "end": {
      "format": "mysql_timestamp"
    }
  },
  "required": [
    "start",
    "end"
  ]
}
"""

valid_input = """
{
    "start": "1990-01-01 00:00:59",
    "end": "2016-10-31 13:54:00"
}
"""

invalid_input = """
{
    "start": "90-01-01 00:00:59",
    "end": "2016-10-31 99:99:99"
}
"""


class TestMySQLTimestampValidation(unittest.TestCase):

    def setUp(self):
        self.actor = TestActorWrapper(JSONValidator("json_validation", schema=jschema))

    def test_valid_mysql_timestamp_json(self):
        _input = JSONEvent(data=valid_input)
        self.actor.input = _input
        _output = self.actor.output
        self.assertEqual(_input, _output)

    def test_invalid_mysql_timestamp_json(self):
        _input = JSONEvent(data=invalid_input)
        self.actor.input = _input
        _output = self.actor.error
        self.assertTrue(isinstance(_output.error, ValueError))
