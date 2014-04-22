from compysition.router import Default
from compysition.module import TestEvent
from compysition.module import RoundRobin
from compysition.module import STDOUT

router=Default()
router.register(TestEvent, "input")
router.register(RoundRobin, "mixing")
router.register(STDOUT, "output1", prefix="I am number one: ")
router.register(STDOUT, "output2", prefix="I am number two: ")

router.connect("input.outbox", "mixing.inbox")
router.connect("mixing.one", "output1.inbox")
router.connect("mixing.two", "output2.inbox")

router.start()
router.block()