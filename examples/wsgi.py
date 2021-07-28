from compysition import Director
from compysition.actors import *

director = Director()

wsgi = director.register_actor(BottleWSGI, "wsgi", run_server=True, address="0.0.0.0", port=7000)
director.register_log_actor(STDOUT, "stdout")
stdout_two = director.register_actor(STDOUT, "stdout_two")
stdout_three = director.register_actor(STDOUT, "stdout_three")


# TODO: Concept... it would be nice to be able to do @wsgi.route(blah) instead
director.connect_queue(wsgi, stdout_two, bottle_route_kwargs={'path': "/base_entity/<sub_entity:re:applications>/<sub_entity_id:re:[0-9]+>", 'method': ['POST']})

director.connect_queue(stdout_two, wsgi)


director.start()
