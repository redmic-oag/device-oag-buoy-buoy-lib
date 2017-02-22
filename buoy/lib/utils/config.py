# -*- coding: utf-8 -*-

from os import path

import yaml


class Config(object):
    def __init__(self):
        self.FILENAME_CONFIG = 'buoy.cfg'
        self.LOCAL_CONFIG_PATH = '../config/'
        self.GLOBAL_CONFIG_PATH = '/etc/buoy/'

    def filename(self):
        filename = self.LOCAL_CONFIG_PATH + self.FILENAME_CONFIG
        if not path.isfile(filename):
            filename = self.GLOBAL_CONFIG_PATH + self.FILENAME_CONFIG

        return filename


def load_config_logger(filename, config='/etc/buoy/logging.yaml'):
    filename += '.log'
    config = yaml.load(open(config, 'r'))
    config['handlers']['file']['filename'] = path.join(config['handlers']['file']['filename'], filename)

    return config
