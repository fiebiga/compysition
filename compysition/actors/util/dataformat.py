import json
from ast import literal_eval
from compysition.errors import InvalidInputException


def str_to_json(data):
    try:
        data = json.loads(data)
    except ValueError:
        # There could be some single quotes here for property values that shouldn't be there.
        # This is really not ideal - incoming string should have been generated with json.dumps already
        try:
            data = literal_eval(data)
            data = json.dumps(data)
            data = json.loads(data)
        except Exception as err:
            pass

    if isinstance(data, dict):
        return data
    else:
        raise InvalidInputException("Event data was a string, but could not be parsed into a dictionary")