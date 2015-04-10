from compysition.module import MDPClient, MDPWorker, MDPBroker, WSGI, MDPBrokerRegistrationService, STDOUT, Data
from compysition import Director

director = Director()

mdp_client          = director.register_module(MDPClient,                     "mdp_client")
mdp_broker          = director.register_module(MDPBroker,                     "mdp_broker")     # This could be it's own process
mdp_regservice      = director.register_module(MDPBrokerRegistrationService,  "mdp_regservice") # This could be it's own process
mdp_worker          = director.register_module(MDPWorker,                     "mdp_worker", "test_service") # This (These) would be their own processes
stdout              = director.register_module(STDOUT,                        "stdout")
data                = director.register_module(Data,                          "data", data="Hello, this has been a test")

wsgi                = director.register_module(WSGI,                          "wsgi", run_server=True, address="0.0.0.0", port=7000)
director.register_log_module(STDOUT,                                          "stdoutmodule", timestamp=True)

director.connect(wsgi,             mdp_client)
director.connect(mdp_worker,       data)
director.connect(data,             mdp_worker)
director.connect(mdp_client,       wsgi)

director.start()
director.block()
