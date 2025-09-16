import functools
import pathlib
import re

import geopandas as gpd
import numpy as np
import pandas as pd
import polars as pl
from shapely import Point

HEADER_MAPPER = {
    "LATITUDE_WGS84_SWEREF99_DD": "lat_dd",
    "LONGITUDE_WGS84_SWEREF99_DD": "lon_dd",
    "LAT_DM": "lat_dm",
    "LONG_DM": "lon_dm",
    "LONGITUDE_SWEREF99TM": "sweref99tm_x",
    "LATITUDE_SWEREF99TM": "sweref99tm_y",
    "STATION_NAME": "station_name",
    "OUT_OF_BOUNDS_RADIUS": "radius",
    "REG_ID": "reg_id",
    "REG_ID_GROUP": "reg_id_group",
    "ICES_STATION_NAME": "ices_station_name",
    "EU_CD": "eu_cd",
}


class MatchingStation:
    def __init__(self, station: dict):
        self._station = station

    def __repr__(self):
        synonyms = "; ".join(self.synonyms)
        return f"{self.station} ({self.distance:_} m). Synonyms: {synonyms}".replace(
            "_", " "
        )

    @property
    def is_accepted(self) -> str:
        return self._station["accepted"]

    @property
    def accepted_name(self) -> str:
        return self._station["accepted_name"]

    @property
    def accepted_position(self) -> str:
        return self._station["accepted_position"]

    @property
    def station(self) -> str:
        return self._station["station_name"]

    @property
    def synonyms(self) -> list[str]:
        return self._station["synonyms"]

    @property
    def all_info(self) -> dict:
        return self._station

    @property
    def lat_dd(self) -> float:
        return self._station["lat_dd"]

    @property
    def lon_dd(self) -> float:
        return self._station["lon_dd"]

    @property
    def lat_sweref99tm(self) -> float:
        return self._station["sweref99tm_y"]

    @property
    def lon_sweref99tm(self) -> float:
        return self._station["sweref99tm_x"]

    @property
    def distance(self) -> int:
        return round(float(self._station["distance"]))

    @property
    def reg_id(self) -> int:
        return self._station["reg_id"]


class MatchingStations:
    def __init__(self, stations: list[dict]) -> None:
        self._stations = [MatchingStation(station) for station in stations]
        self._stations.sort(key=lambda x: x.distance)

    def get_accepted_station(self) -> MatchingStation | None:
        for station in self._stations:
            if station.is_accepted:
                return station

    def __repr__(self):
        lines = ["Matching stations:"] + [repr(station) for station in self._stations]
        return "\n".join(lines)

    def __getitem__(self, item: int):
        return self._stations[item]

    def __iter__(self):
        return iter(self._stations)

    def __len__(self):
        return len(self._stations)

    def __bool__(self):
        return bool(self._stations)


class StationFile:
    """Class to handle the official station list att SMHI"""

    def __init__(self, path: pathlib.Path, case_sensitive: bool = True, **kwargs):
        self._path = pathlib.Path(path)
        self._encoding = kwargs.get("encoding", "cp1252")
        self._delimiter = "\t"
        self._case_sensitive = case_sensitive

        self._header = []
        self._data = dict()
        self._synonym_index = dict()
        self._pol_df: pl.DataFrame = pl.DataFrame()
        self._geopan_df: gpd.GeoDataFrame = gpd.GeoDataFrame()

        self._load_file()

    @property
    def gdf(self) -> gpd.GeoDataFrame:
        return self._geopan_df

    @property
    def pol_df(self) -> pl.DataFrame:
        return self._pol_df

    @property
    def path(self) -> pathlib.Path:
        return self._path

    @property
    def header(self) -> list[str]:
        return self._header

    @property
    def keys_as_synonyms(self) -> list[str]:
        """Returns a list of column names that should be used as synonyms"""
        return [
            # "reg_id",
            # "reg_id_group",
            # "ices_station_name",
            # "eu_cd",
        ]

    @staticmethod
    def _convert_synonym(synonym: str) -> str:
        """Converts a synonym to a more comparable string"""
        return synonym.lower().replace(" ", "")

    @staticmethod
    def _convert_station_name(station_name: str) -> str:
        """Converts a public value to a more comparable string"""
        return station_name.upper()

    @staticmethod
    def _convert_header_col(header_col: str) -> str:
        """Converts a header column to a more comparable string"""
        return header_col.strip().lower()

    def _load_file(self) -> None:
        # self._load_pol_df()
        self._load_geopan_df()
        self._add_synonyms_to_geopan_df()

    def _load_pol_df(self):
        self._pol_df = pl.read_csv(
            self._path,
            encoding=self._encoding,
            separator=self._delimiter,
        ).with_row_index()

        self._pol_df = self._pol_df.with_columns(
            pl.col("station_name").str.split(by="DUMMY").alias("synonyms")
        )

        self._pol_df = self._pol_df.with_columns(
            pl.when(pl.col("SYNONYM_NAMES").is_not_null())
            .then(
                pl.col("synonyms").list.concat(
                    pl.col("SYNONYM_NAMES").str.split(by="<or>")
                )
            )
            .otherwise(pl.col("synonyms"))
            .alias("synonyms")
        )
        for col in self._pol_df.columns:
            if col not in self.keys_as_synonyms:
                continue
            self._pol_df = self._pol_df.with_columns(
                pl.when(pl.col(col).is_not_null())
                .then(
                    pl.col("synonyms").list.concat(
                        pl.col(col).cast(str).str.split(by="DUMMY")
                    )
                )
                .otherwise(pl.col("synonyms"))
                .alias("synonyms")
            )

    def _load_geopan_df(self):
        pdf = pd.read_csv(self._path, encoding="cp1252", sep="\t")
        new_header = [HEADER_MAPPER.get(col, col) for col in pdf.columns]
        pdf.columns = new_header

        self._geopan_df = gpd.GeoDataFrame(
            pdf,
            geometry=gpd.points_from_xy(pdf["lon_dd"], pdf["lat_dd"]),
            crs="EPSG:4326",
        )
        self._geopan_df["index"] = self._geopan_df.index
        self._geopan_df = self._geopan_df.to_crs("3006")
        self._geopan_df["buffer"] = self._geopan_df["geometry"].buffer(
            self._geopan_df["radius"]
        )

    def _add_synonyms_to_geopan_df(self):
        if self._case_sensitive:
            self._geopan_df["synonyms"] = self._geopan_df["station_name"].str.split(
                "DUMMY"
            )
            synonym_function = _combine_synonyms_columns
        else:
            self._geopan_df["synonyms"] = (
                self._geopan_df["station_name"].str.upper().str.split("DUMMY")
            )
            synonym_function = _combine_synonym_columns_uppercase

        # Om SYNONYM_NAMES inte är null, splitta på <or> och lägg till i 'synonyms'
        mask = self._geopan_df["SYNONYM_NAMES"].notna()
        self._geopan_df.loc[mask, "synonyms"] = self._geopan_df.loc[mask].apply(
            synonym_function, axis=1
        )

        # Lägg till värden från övriga kolumner (om de finns i keys_as_synonyms)
        for col in self._geopan_df.columns:
            if col in self.keys_as_synonyms:
                mask = self._geopan_df[col].notna()
                self._geopan_df.loc[mask, "synonyms"] = self._geopan_df.loc[mask].apply(
                    lambda row: sorted(
                        set(row["synonyms"] + str(row[col]).split("DUMMY"))
                    ),
                    axis=1,
                )

    def get_station_name_list(self) -> list[str]:
        return sorted(self.pol_df["station_name"])

    @functools.cache
    def get_matching_stations(
        self,
        name: str | None = None,
        lat_dd: float | None = None,
        lon_dd: float | None = None,
    ) -> MatchingStations:
        position_matches = {
            station["index"]: station
            for station in self.get_stations_within_radius(lat_dd, lon_dd)
        }

        name_matches = {
            station["index"]: station
            for station in self.get_stations_with_matching_synonym(name)
        }

        all_matching_indices = set(position_matches.keys() | name_matches.keys())
        all_matches = []
        for index in all_matching_indices:
            station = {"accepted_position": False, "accepted_name": False}

            if radius_match := position_matches.get(index):
                station |= radius_match
                station["accepted_position"] = True

            if name_match := name_matches.get(index):
                station |= name_match
                station["accepted_name"] = True

            station["accepted"] = (
                station["accepted_position"] and station["accepted_name"]
            )
            all_matches.append(station)

        self._geopan_df.drop("distance", axis=1, inplace=True)
        return MatchingStations(all_matches)

    def get_stations_within_radius(
        self, lat_dd: float | None = None, lon_dd: float | None = None
    ) -> list[dict]:
        point = self._get_point(lat_dd=lat_dd, lon_dd=lon_dd)
        self._geopan_df["distance"] = self._geopan_df.distance(point).astype(int)
        within_radius = self._geopan_df["buffer"].contains(point)
        df = self._geopan_df[within_radius].copy()
        df["distance"] = df.distance(point)
        return df.to_dict(orient="records")

    def _get_point(self, lat_dd: float, lon_dd: float):
        point = Point(lon_dd, lat_dd)
        d = {"name": ["name"], "geometry": [point]}
        pos_df = gpd.GeoDataFrame(d, crs=4326)
        return next(pos_df.to_crs("3006")["geometry"])

    def get_stations_with_matching_synonym(self, name: str) -> list[dict]:
        if self._case_sensitive:
            df = self._geopan_df[
                self._geopan_df["synonyms"].apply(lambda synonyms: name in synonyms)
            ]
        else:
            df = self._geopan_df[
                self._geopan_df["synonyms"].apply(
                    lambda synonyms: name.upper() in synonyms
                )
            ]

        return df.to_dict(orient="records")

    def get_stations_with_matching_synonym_polars(self, name: str) -> list[dict]:
        if self._case_sensitive:
            return self._pol_df.filter(pl.col("synonyms").list.contains(name)).to_dicts()
        else:
            return self._pol_df.filter(
                pl.col("synonyms").list.contains(name.upper())
            ).to_dicts()

    def _get_spatial_info_for_index_polars(self, index: int) -> dict:
        return self._geopan_df.loc[index, :].to_dict()

    def get_stations_by_name(self, names: list[str]) -> gpd.GeoDataFrame:
        def is_match(x, n) -> bool:
            if re.match(n, x):
                return True
            return False

        boolean = np.zeros(len(self._geopan_df), dtype=bool)
        for name in names:
            boolean = boolean | self._geopan_df["station_name"].apply(
                lambda x, n=name: is_match(x, n)
            )

        return_df = self._geopan_df.loc[boolean, :].copy()
        return return_df

    def get_stations_within_buffer(
        self, df: pl.DataFrame | pd.DataFrame, buffer: int
    ) -> gpd.GeoDataFrame:
        if isinstance(df, pl.DataFrame):
            df = df.to_pandas()
        df.drop_duplicates(["sample_longitude_dd", "sample_latitude_dd"], inplace=True)
        gdf = gpd.GeoDataFrame(
            df,
            geometry=gpd.points_from_xy(
                df["sample_longitude_dd"], df["sample_latitude_dd"]
            ),
            crs="EPSG:4326",
        )
        gdf = gdf.to_crs("3006")

        self._geopan_df["buffer"] = self._geopan_df.buffer(buffer)
        within_buffer = np.array(np.zeros(len(self._geopan_df)), dtype=bool)
        for point in gdf["geometry"]:
            within_buffer = within_buffer | self._geopan_df["buffer"].contains(point)

        return_df = self._geopan_df.loc[within_buffer, :].copy()
        return_df.reset_index(inplace=True)
        return return_df


def _combine_synonyms_columns(row):
    return row["synonyms"] + row["SYNONYM_NAMES"].split("<or>")


def _combine_synonym_columns_uppercase(row):
    return row["synonyms"] + row["SYNONYM_NAMES"].upper().split("<OR>")
