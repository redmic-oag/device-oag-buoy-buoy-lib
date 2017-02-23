# -*- coding: utf-8 -*-

import configparser
import yaml
import logging
from os import path

logger = logging.getLogger(__name__)


def load_config_devices(path_config='/etc/buoy/buoy.cfg'):
    if not path.isfile(path_config):
        logger.error("No exists config file %s" % (path_config,))

    config = configparser.ConfigParser()
    config.read(path_config)

    return config


def load_config_logger(filename, config='/etc/buoy/logging.yaml'):
    filename += '.log'
    config = yaml.load(open(config, 'r'))
    config['handlers']['file']['filename'] = path.join(config['handlers']['file']['filename'], filename)

    return config
