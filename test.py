from compysition import Director
from compysition.module import TestEvent
from compysition.module import STDOUT

director = Director()
event_generator = director.register_module(TestEvent, "event_generator", interval=1)
output_one      = director.register_module(STDOUT, "output_one", prefix="I am number one: ", timestamp=True)
output_two      = director.register_module(STDOUT, "output_two", prefix="I am number two: ", timestamp=True)

director.connect(event_generator, output_one)
director.connect(event_generator, output_two)

director.start()
director.block()