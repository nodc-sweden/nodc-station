import functools
import os
from pathlib import Path

from nodc_station.station_file import StationFile

CONFIG_ENV = "NODC_CONFIG"

_home = Path.home()
OTHER_CONFIG_SOURCES = [
    _home / "NODC_CONFIG",
    _home / ".NODC_CONFIG",
    _home / "nodc_config",
    _home / ".nodc_config",
]


def _get_config_dir():
    if config_dir := os.getenv(CONFIG_ENV):
        return Path(config_dir)
    for config_dir in OTHER_CONFIG_SOURCES:
        if config_dir.exists():
            return config_dir


def _get_default_station_path() -> Path:
    if config_dir := _get_config_dir():
        station_path = config_dir / "station.txt"
        if station_path.exists():
            return station_path
        raise FileNotFoundError(f"Config dir '{config_dir}' has no 'station.txt' file.")
    raise NotADirectoryError("Could not find a config directory.")


@functools.cache
def get_station_object(
    path: Path | str | None = None, case_sensitive: bool = True
) -> StationFile:
    path = path or _get_default_station_path()
    return StationFile(path, case_sensitive=case_sensitive)
