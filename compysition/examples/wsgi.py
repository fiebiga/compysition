from compysition import Director
from compysition.actors import *

director = Director()

wsgi = director.register_actor(BottleWSGI, "wsgi", run_server=True, address="0.0.0.0", port=7000)
director.register_log_actor(STDOUT, "stdout")
stdout_two = director.register_actor(STDOUT, "stdout_two")

director.connect_queue(wsgi, stdout_two, bottle_route_kwargs={'path': "/", 'method': '[POST]'})

director.start()