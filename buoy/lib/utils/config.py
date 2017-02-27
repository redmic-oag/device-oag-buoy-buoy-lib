# -*- coding: utf-8 -*-

import yaml
import logging
from os import path

logger = logging.getLogger(__name__)


def load_config(path_config):
    if not path.isfile(path_config):
        logger.error("No exists config file %s" % (path_config,))

    config = yaml.load(open(path_config, 'r'))

    return config


def load_config_device(device_name, path_config='/etc/buoy/buoy.yaml'):

    config = load_config(path_config=path_config)

    return config['device'][device_name]


def load_config_device_serial(device_name, path_config='/etc/buoy/device.yaml'):

    config = load_config_device(device_name, path_config=path_config)

    return config['device'][device_name]['serial']


def load_config_logger(filename, path_config='/etc/buoy/logging.yaml'):
    config = load_config(path_config=path_config)

    filename += '.log'
    config['handlers']['file']['filename'] = path.join(config['handlers']['file']['filename'], filename)

    return config
