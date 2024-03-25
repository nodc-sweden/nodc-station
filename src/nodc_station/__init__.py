# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2020-09-24 16:44

@author: a002028

"""
import logging
import pathlib

import requests

from nodc_station import *
from nodc_station.main import App
from nodc_station.readers import *
from nodc_station.validators import *
from nodc_station.writers import *

logger = logging.getLogger(__name__)


THIS_DIR = pathlib.Path(__file__).parent
CONFIG_DIR = THIS_DIR / "CONFIG_FILES"

CONFIG_URLS = [
    r'https://raw.githubusercontent.com/nodc-sweden/nodc-worms/main/src/nodc_worms/CONFIG_FILES/station.txt',
]


def update_config_files() -> None:
    """Downloads config files from github"""
    try:
        for url in CONFIG_URLS:
            name = pathlib.Path(url).name
            target_path = CONFIG_DIR / name
            res = requests.get(url)
            with open(target_path, 'w', encoding='utf8') as fid:
                fid.write(res.text)
                logger.info(f'Config file "{name}" updated from {url}')
    except requests.exceptions.ConnectionError:
        logger.warning('Connection error. Could not update config files!')

