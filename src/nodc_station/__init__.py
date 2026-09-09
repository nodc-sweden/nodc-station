import functools
from pathlib import Path

from nodc_config import nodc_conf

from nodc_station.station_file import MatchingStations, StationFile


def _get_default_station_path() -> Path:
    path = nodc_conf.get_path("station.txt")
    if path is None:
        raise FileNotFoundError("nodc-config path 'station.txt' not found")
    return path


def get_station_object(
    path: Path | str | None = None, case_sensitive: bool = True
) -> StationFile:
    path = path or _get_default_station_path()
    return StationFile(path, case_sensitive=case_sensitive)


@functools.cache
def get_matching_stations(
    name: str | None = None,
    lat_dd: float | None = None,
    lon_dd: float | None = None,
) -> MatchingStations:
    return get_station_object().get_matching_stations(
        name=name, lat_dd=lat_dd, lon_dd=lon_dd
    )


def clear_cache() -> None:
    get_matching_stations.cache_clear()
