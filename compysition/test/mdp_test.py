from compysition.module import MDPClient, MDPWorker, MajorDomoBroker, WSGI, BrokerRegistrationService, STDOUT, Data
from compysition.router import Default

router = Default()

router.registerModule(MDPClient, "mdp_client")
router.registerModule(MajorDomoBroker, "mdp_broker")
router.registerModule(BrokerRegistrationService, "mdp_regservice")
router.registerModule(MDPWorker, "mdp_worker", "test_service")
router.registerModule(STDOUT, "stdout")
router.registerModule(Data, "data", data="Hello Adam, this has been a test")

router.registerModule(WSGI, "wsgi", run_server=True, address="127.0.0.1", port=7000)
router.registerLogModule(STDOUT, "stdoutmodule", timestamp=True)
router.connect("wsgi.test_service", "mdp_client.inbox")
router.connect("mdp_worker.outbox", "data.inbox")
router.connect("data.outbox", "mdp_worker.inbox")

router.connect("mdp_client.outbox", "wsgi.mdp_client_inbox")

router.start()
router.block()