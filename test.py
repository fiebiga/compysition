from compysition import Director
from compysition.module import TestEvent
from compysition.module import STDOUT, TCPIn, TCPOut

director = Director()
director_two = Director()

event_generator = director.register_module(TestEvent, "event_generator", interval=0.5)
tcp_out      	= director.register_module(TCPOut, "tcp_out")
stdout 			= director_two.register_module(STDOUT, "stdout")
tcp_in			= director_two.register_module(TCPIn, "tcp_in")

director.connect(event_generator, tcp_out)
director_two.connect(tcp_in,	stdout)
director.start()   
director_two.start()
director.block()