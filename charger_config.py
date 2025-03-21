import configparser
import os
import shutil


class ChargerConfig:
    def __init__(self):
        self.config = configparser.ConfigParser()
        config_file = "%s/config.ini" % (os.path.dirname(os.path.realpath(__file__)))
        if not os.path.exists(config_file):
            sample_config_file = "%s/config.ini" % (os.path.dirname(os.path.realpath(__file__)))
            shutil.copy(sample_config_file, config_file)
        self.config.read("%s/config.ini" % (os.path.dirname(os.path.realpath(__file__))))

    def get_device(self):
        return self.config.get('Setup', 'device', fallback="om.victronenergy.charger.ttyUSB0")

    def get_voltage(self):
        return self.config.get('Setup', 'voltage', fallback="230")

    def get_debug(self):
        val = self.config.get("Setup", "debug", fallback=False)
        if val == "true":
            return True
        else:
            return False

    @staticmethod
    def get_version():
        with open("%s/version" % (os.path.dirname(os.path.realpath(__file__))), 'r') as file:
            return file.read()
