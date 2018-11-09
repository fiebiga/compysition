from compysition import Actor
from compysition.event import http_code_map

class ErrorHandler(Actor):
    def format_event(self, event):
        if event.error is not None:
            event.data = event.error_string()
            event.status = http_code_map[event.error.__class__]
            event.error = None
        return event
    def consume(self, event, *args, **kwargs):
        self.send_event(self.format_event(event=event)) 