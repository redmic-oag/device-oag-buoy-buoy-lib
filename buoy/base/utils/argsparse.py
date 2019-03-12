# -*- coding: utf-8 -*-

import argparse
from os import path


def is_valid_file(filename):
    if not path.isfile(filename):
        raise argparse.ArgumentTypeError("{0} does not exist".format(filename))

    return filename


def parse_args(path_config='/etc/buoy/'):
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-file", help="Ruta al fichero de configuración del servicio",
                        default=path.join(path_config, 'device.yaml'), type=is_valid_file)
    parser.add_argument("--config-log-file", help="Ruta al fichero de configuración de los logs",
                        default=path.join(path_config, 'logging.yaml'), type=is_valid_file)
    return parser.parse_args()
