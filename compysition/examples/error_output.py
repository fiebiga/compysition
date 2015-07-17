from compysition import Director
from compysition.actors import *

director = Director()

testevent = director.register_actor(TestEvent, "testevent")
stdout_err = director.register_actor(STDOUT, "stdout_err", prefix="ERROR : ")
stdout = director.register_actor(STDOUT, "stdout", prefix="STDOUT : ")

director.connect_queue(testevent, stdout)

director.start()
