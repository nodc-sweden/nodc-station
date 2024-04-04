import logging
import pathlib
import sys
import pandas as pd
import functools
from nodc_station import utils


logger = logging.getLogger(__name__)

THIS_DIR = pathlib.Path(__file__).parent
DEFAULT_STATION_FILE_PATH = THIS_DIR / 'CONFIG_FILES' / 'station.txt'


class StationFile:
    """Class to handle the official station list att SMHI"""

    def __init__(self, path: pathlib.Path, **kwargs):
        self._path = pathlib.Path(path)
        self._encoding = kwargs.get('encoding', 'cp1252')

        self._header = []
        self._data = dict()
        self._synonym_index = dict()
        self._df: pd.DataFrame = pd.DataFrame()

        self._load_file()

    @property
    def df(self):
        return self._df

    @property
    def path(self) -> pathlib.Path:
        return self._path

    @property
    def header(self) -> list[str]:
        return self._header

    @property
    def keys_not_as_synonyms(self) -> list[str]:
        """Returns a list of column names that can not be used as synonyms"""
        return ['synonym_names', 'lat_dm', 'long_dm', 'latitude_wgs84_sweref99_dd', 'longitude_wgs84_sweref99_dd',
                'latitude_sweref99tm', 'longitude_sweref99tm', 'out_of_bounds_radius', 'wadep', 'media', 'comnt']

    @staticmethod
    def _convert_synonym(synonym: str) -> str:
        """Converts a synonym (in list or given by user) to a more comparable string"""
        return synonym.lower().replace(' ', '')

    @staticmethod
    def _convert_station_name(station_name: str) -> str:
        """Converts a public value (in list or given by user) to a more comparable string"""
        return station_name.upper()

    @staticmethod
    def _convert_header_col(header_col: str) -> str:
        """Converts a header column (in station file or given by user) to a more comparable string"""
        return header_col.strip().lower()

    def _get_synonyms_for_row(self, row: pd.Series):
        synonyms = []
        for col in row.keys():
            if col in self.keys_not_as_synonyms:
                continue
            if type(row[col]) is not str:
                continue
            for item in row[col].split('<o>'):
                syn = self._convert_synonym(item)
                synonyms.append(syn)
        return synonyms

    def _load_file(self) -> None:
        self._df = pd.read_csv(self._path, encoding=self._encoding, sep='\t')
        for i, row in self._df.iterrows():
            for syn in self._get_synonyms_for_row(row):
                self._synonym_index.setdefault(syn, [])
                self._synonym_index[syn].append(i)


            # for col in self._df.columns:
            #     if col in self.keys_not_as_synonyms:
            #         continue
            #     if type(row[col]) is not str:
            #         continue
            #     for item in row[col].split('<o>'):
            #         syn = self._convert_synonym(item)
            #         self._synonym_index.setdefault(syn, [])
            #         self._synonym_index[syn].append(i)

    def get_station_name_list(self) -> list[str]:
        return sorted(self.df['STATION_NAME'])

    def get_station_names(self, synonym: str = None) -> list[str]:
        """Takes a synonym of a station and returns the corresponding station name. Returns None if no match for the
        synonym is found"""
        index = self._synonym_index.get(self._convert_synonym(synonym))
        if not index:
            return []
        return sorted(self.df.loc[index]['STATION_NAME'])

    def _get_info_from_row(self, row: pd.Series, index: int) -> dict:
        info = row.to_dict()
        info['index'] = index
        print(info)
        # info['synonyms'] = [self._convert_synonym(syn) for syn in info['SYNONYM_NAMES'].split('<o>')]
        info['synonyms'] = self._get_synonyms_for_row(row)
        if not info['OUT_OF_BOUNDS_RADIUS']:
            info['accepted'] = None
        elif 'calc_dist' in info and (info['calc_dist'] <= info['OUT_OF_BOUNDS_RADIUS']):
            info['accepted'] = True
        else:
            info['accepted'] = False
        return info

    def _get_info_list_from_df(self, df: pd.DataFrame) -> list[dict]:
        info_list = []
        for index, row in df.iterrows():
            info = self._get_info_from_row(row, index)
            info_list.append(info)
        return info_list

    def get_station_info(self, synonym: str) -> list:
        """Returns all station information corresponding to the given synonym.
        Returns None if synonym dont match any station"""
        index = self._synonym_index.get(self._convert_synonym(synonym))
        if not index:
            return []
        df = self.df.loc[index]
        return self._get_info_list_from_df(df)
    # def get_pos_dm(self, synonym: str) -> tuple[str, str] | None:
    #     station_data = self._data.get(self.get_station_name(synonym))
    #     if not station_data:
    #         return None
    #     return station_data[self._convert_header_col('LAT_DM')], station_data[self._convert_header_col('LON_DM')]
    #
    # def get_pos_wgs84_sweref99_dd(self, synonym: str) -> tuple[str, str] | None:
    #     station_data = self._data.get(self.get_station_name(synonym))
    #     if not station_data:
    #         return None
    #     return station_data[self._convert_header_col('LATITUDE_WGS84_SWEREF99_DD')], \
    #         station_data[self._convert_header_col('LONGITUDE_WGS84_SWEREF99_DD')]
    #
    # def get_pos_sweref99tm(self, synonym: str) -> tuple[str, str] | None:
    #     station_data = self._data.get(self.get_station_name(synonym))
    #     if not station_data:
    #         return None
    #     return station_data[self._convert_header_col('LATITUDE_SWEREF99TM')], \
    #         station_data[self._convert_header_col('LONGITUDE_SWEREF99TM')]
    #
    # def list_synonyms(self, station_name: str) -> list[str]:
    #     station_name = self._convert_station_name(station_name)
    #     return self._data[station_name]['synonym_names']

    @functools.cache
    def get_closest_station_info(self, lat: str, lon: str):
        self.df['calc_dist'] = self.df.apply(lambda row,
                                                    lat=float(lat),
                                                    lon=float(lon): self._calc_distance(lat, lon, row), axis=1)
        cdf = self.df[self.df['calc_dist'] == min(self.df['calc_dist'])]
        info_list = self._get_info_list_from_df(cdf)
        return info_list

    @functools.cache
    def get_station_info_from_synonym_and_position(self, synonym: str, lat: str, lon: str) -> dict:
        index = self._synonym_index.get(self._convert_synonym(synonym), [])
        if not index:
            return {}
        df = self.df.loc[index]
        df['calc_dist'] = df.apply(lambda row,
                                   lat=float(lat),
                                   lon=float(lon): self._calc_distance(lat, lon, row), axis=1)
        info_list = self._get_info_list_from_df(df)
        return sorted(info_list, key=lambda info: info['calc_dist'])[0]

    def _calc_distance(self, lat: float, lon: float, row: pd.Series):
        pos1 = lat, lon
        pos2 = row['LATITUDE_WGS84_SWEREF99_DD'], row['LONGITUDE_WGS84_SWEREF99_DD']
        return utils.latlon_distance(pos1, pos2)


    # def get_eu_cd_for_station_name(self, station_name: str) -> str:
    #     info = self.get_station_info(station_name)
    #     if not info:
    #         return None
    #     return info[self._convert_header_col('EU_CD')]


@functools.cache
def get_station_object(path: pathlib.Path | str | None = None) -> "StationFile":
    path = path or DEFAULT_STATION_FILE_PATH
    return StationFile(path)


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


