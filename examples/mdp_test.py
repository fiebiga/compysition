from compysition.actors import MDPClient, MDPWorker, MDPBroker, WSGI, MDPBrokerRegistrationService, STDOUT, EventAttributeModifier
from compysition import Director

director = Director()
stdout_logger       = director.register_log_actor(STDOUT,                    "stdoutmodule", timestamp=True)
mdp_client          = director.register_actor(MDPClient,                     "mdp_client")
mdp_broker          = director.register_actor(MDPBroker,                     "mdp_broker")     # This could be it's own process
mdp_regservice      = director.register_actor(MDPBrokerRegistrationService,  "mdp_regservice") # This could be it's own process
mdp_worker          = director.register_actor(MDPWorker,                     "mdp_worker", "test_service") # This (These) would be their own processes
stdout              = director.register_actor(STDOUT,                        "stdout")
data                = director.register_actor(EventAttributeModifier,        "data", value="Hello, this has been a test")
wsgi                = director.register_actor(WSGI,                          "wsgi", run_server=True, address="0.0.0.0", port=7000)

director.connect_queue(wsgi,             mdp_client)
director.connect_queue(mdp_worker,       data)
director.connect_queue(data,             mdp_worker)
director.connect_queue(mdp_client,       wsgi)

director.start()