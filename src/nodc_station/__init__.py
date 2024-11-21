# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2020-09-24 16:44

@author: a002028

"""
import functools
import logging
import os
import pathlib
import ssl

import requests

from nodc_station.main import App
from nodc_station.readers import *
from nodc_station.validators import *
from nodc_station.writers import *
from nodc_station.station_file import StationFile

logger = logging.getLogger(__name__)

CONFIG_SUBDIRECTORY = 'nodc_station'
CONFIG_FILE_NAMES = [
    'station.txt'
]


CONFIG_DIRECTORY = None
if os.getenv('NODC_CONFIG'):
    CONFIG_DIRECTORY = pathlib.Path(os.getenv('NODC_CONFIG')) / CONFIG_SUBDIRECTORY
TEMP_CONFIG_DIRECTORY = pathlib.Path.home() / 'temp_nodc_config' / CONFIG_SUBDIRECTORY


CONFIG_URL = r'https://raw.githubusercontent.com/nodc-sweden/nodc_config/refs/heads/main/' + f'{CONFIG_SUBDIRECTORY}/'


def get_config_path(name: str) -> pathlib.Path:
    if name not in CONFIG_FILE_NAMES:
        raise FileNotFoundError(f'No config file with name "{name}" exists')
    if CONFIG_DIRECTORY:
        path = CONFIG_DIRECTORY / name
        if path.exists():
            return path
    temp_path = TEMP_CONFIG_DIRECTORY / name
    if temp_path.exists():
        return temp_path
    update_config_file(temp_path)
    if temp_path.exists():
        return temp_path
    raise FileNotFoundError(f'Could not find config file {name}')


def update_config_file(path: pathlib.Path) -> None:
    path.parent.mkdir(exist_ok=True, parents=True)
    url = CONFIG_URL + path.name
    try:
        res = requests.get(url, verify=ssl.CERT_NONE)
        with open(path, 'w', encoding='utf8') as fid:
            fid.write(res.text)
            logger.info(f'Config file "{path.name}" updated from {url}')
    except requests.exceptions.ConnectionError:
        logger.warning(f'Connection error. Could not update config file {path.name}')
        raise


def update_config_files() -> None:
    """Downloads config files from github"""
    for name in CONFIG_FILE_NAMES:
        target_path = TEMP_CONFIG_DIRECTORY / name
        update_config_file(target_path)


@functools.cache
def get_station_object(path: pathlib.Path | str | None = None) -> "StationFile":
    return StationFile(get_config_path('station_file.txt'))


def print_closest_station_info(lat: float | str, lon: float | str, path: str | pathlib.Path | None = None) -> None:
    obj = get_station_object(path)
    info = obj.get_closest_station_info(lat, lon)
    print()
    print('-'*100)
    print(f'Closest station for position [{lat}, {lon}]')
    print('-'*100)
    for key in sorted(info):
        value = info[key]
        print(f'{key.ljust(30)}:  {value}')


DEFAULT_STATION_FILE_PATH = get_config_path('station.txt')


@functools.cache
def get_station_object(path: pathlib.Path | str | None = None) -> "StationFile":
    path = path or DEFAULT_STATION_FILE_PATH
    return StationFile(path)



if __name__ == '__main__':
    update_config_files()

