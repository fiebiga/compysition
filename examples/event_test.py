from compysition import Director
from compysition.actors import TestEvent, STDOUT

director = Director()
event_generator = director.register_actor(TestEvent, "event_generator", interval=1)
output_one      = director.register_actor(STDOUT, "output_one", prefix="I am number one: ", timestamp=True)
output_two      = director.register_actor(STDOUT, "output_two", prefix="I am number two: ", timestamp=True)

director.connect_queue(event_generator, [output_one, output_two])

director.start()