import logging
import logging.handlers
import os
from configobj import ConfigObj
import gevent.coros

class RotatingFileHandler(logging.handlers.RotatingFileHandler):

    def __init__(self, file_path, *args, **kwargs):
        self.make_file(file_path)
        super(RotatingFileHandler, self).__init__(file_path, *args, **kwargs)

    def createLock(self):
        """Set self.lock to a new gevent RLock.
        """
        self.lock = gevent.coros.RLock()

    def make_file(self, file_path):
        file_dir = os.path.dirname(file_path)
        if not os.path.isfile(file_path):
            if not os.path.exists(file_dir):
                self.make_file_dir(file_dir)
            open(file_path, 'w+')

    def make_file_dir(self, file_path):
        sub_path = os.path.dirname(os.path.abspath(file_path))
        if not os.path.exists(sub_path):
            self.make_file_dir(sub_path)
        if not os.path.exists(file_path):
            os.mkdir(file_path)

class LoggingConfigLoader(object):

    def __init__(self, **kwargs):
        default_config_file = "{0}/../../default_config/logging.conf".format(os.path.dirname(os.path.abspath(__file__)))
        local_config_file = "config/logging.conf"
        self.config = {}

        self.update_config(default_config_file) # Load defaults first
        self.update_config(local_config_file)   # Override with local configurations (if any)

        for key in self.config:                 # Finally, prioritize any module specific overrides over any of the previous modifications
            if kwargs.get(key, None) is not None:
                self.config[key] = kwargs.get(key, None)

        self.config['level'] = self.get_log_level()
         
    def update_config(self, file_path):
        config_file = ConfigObj(file_path)
        if config_file is not None:
            if config_file.get("logging") is not None:
                self.config.update(config_file.get("logging"))

    def get_log_level(self, default_level=logging.INFO):
        try:
            level = getattr(logging, self.config.get('level').upper(), None)
        except Exception:
            level = default_level
        
        return level

if __name__ == "__main__":
    logging_config = LoggingConfigLoader()
    print logging_config.config