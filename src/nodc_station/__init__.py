import functools
import logging
import os
import pathlib

from nodc_station.station_file import StationFile

logger = logging.getLogger(__name__)

CONFIG_ENV = 'NODC_CONFIG'

home = pathlib.Path.home()
OTHER_CONFIG_SOURCES = [
    home / 'NODC_CONFIG',
    home / '.NODC_CONFIG',
    home / 'nodc_config',
    home / '.nodc_config',
]

CONFIG_FILE_NAMES = [
    'station.txt'
]


CONFIG_DIRECTORY = None
if os.getenv(CONFIG_ENV) and pathlib.Path(os.getenv(CONFIG_ENV)).exists():
    CONFIG_DIRECTORY = pathlib.Path(os.getenv(CONFIG_ENV))
else:
    for directory in OTHER_CONFIG_SOURCES:
        if directory.exists():
            CONFIG_DIRECTORY = directory
            break


def get_config_path(name: str = None) -> pathlib.Path:
    if not CONFIG_DIRECTORY:
        raise NotADirectoryError(f'Config directory not found. Environment path {CONFIG_ENV} does not seem to be set.')
    if not name:
        return CONFIG_DIRECTORY
    if name not in CONFIG_FILE_NAMES:
        raise FileNotFoundError(f'No config file with name "{name}" exists')
    path = CONFIG_DIRECTORY / name
    if not path.exists():
        raise FileNotFoundError(f'Could not find config file {name}')
    return path


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
    station = get_station_object()

