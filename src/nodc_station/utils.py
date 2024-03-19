# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2020-09-25 16:41

@author: a002028

"""
import os
import numpy as np
try:
    from collections import Mapping
except ImportError:
    from typing import Mapping
from datetime import datetime
from pyproj import Proj, CRS, transform
from decimal import Decimal, ROUND_HALF_UP


def eliminate_empty_rows(df):
    return df.loc[df.apply(any, axis=1), :].reset_index(drop=True)


def distance_between_points_meters(x1, x2, y1, y2):
    """Distance between two points.

    Example of coordinate reference system in meters: SWEREF99TM
    """
    return (((x2 - x1) ** 2) + ((y2 - y1) ** 2)) ** 0.5


def decmin_to_decdeg(pos, string_type=True, decimals=4):
    """
    :param pos: str, Position in format DDMM.mm (Degrees + decimal minutes)
    :param string_type: As str?
    :param decimals: Number of decimals
    :return: Position in format DD.dddd (Decimal degrees)
    """
    pos = float(pos.replace(' ', ''))

    output = np.floor(pos/100.) + (pos % 100)/60.
    output = round_value(output, nr_decimals=decimals)
    # output = "%.5f" % output
    if string_type:
        return output
    else:
        return float(output)


def decdeg_to_decmin(pos: (str, float), string_type=True, decimals=2) -> (str, float):
    """
    :param pos: Position in format DD.dddd (Decimal degrees)
    :param string_type: As str?
    :param decimals: Number of decimals
    :return: Position in format DDMM.mm(Degrees + decimal minutes)
    """
    pos = float(pos)
    deg = np.floor(pos)
    minute = pos % deg * 60.0
    if string_type:
        if decimals:
            output = ('%%2.%sf'.zfill(7) % decimals % (float(deg) * 100.0 + minute))
        else:
            output = (str(deg * 100.0 + minute))

        if output.index('.') == 3:
            output = '0' + output
    else:
        output = (deg * 100.0 + minute)
    return output


def generate_filepaths(directory: str, pattern=''):
    """
    :param directory: str, directory path
    :param pattern: str
    :return: generator
    """
    for path, subdir, fids in os.walk(directory):
        for f in fids:
            if pattern in f:
                yield os.path.abspath(os.path.join(path, f))


def get_now_time(fmt=None) -> str:
    """
    :param fmt: str, format to export datetime object
    :return:
    """
    fmt = fmt or '%Y-%m-%d %H:%M:%S'
    return datetime.now().strftime(fmt)


def recursive_dict_update(d: dict, u: dict) -> dict:
    """ Recursive dictionary update using
    Copied from:
        http://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth
        via satpy
    """
    for k, v in u.items():
        if isinstance(v, Mapping):
            r = recursive_dict_update(d.get(k, {}), v)
            d[k] = r
        else:
            d[k] = u[k]
    return d


def round_value(value: (str, int, float), nr_decimals=2) -> str:
    """"""
    return str(Decimal(str(value)).quantize(Decimal('%%1.%sf' % nr_decimals % 1), rounding=ROUND_HALF_UP))


def transform_ref_system(lat=0.0, lon=0.0,
                         in_proj='EPSG:3006',  # SWEREF 99TM 1200
                         out_proj='EPSG:4326'):
    """
    Transform coordinates from one spatial reference system to another.
    in_proj is your current reference system
    out_proj is the reference system you want to transform to, default is EPSG:4326 = WGS84
    (Another good is EPSG:4258 = ETRS89 (Europe), almost the same as WGS84 (in Europe)
    and not always clear if coordinates are in WGS84 or ETRS89, but differs <1m.
    lat = latitude
    lon = longitude
    To find your EPSG check this website: http://spatialreference.org/ref/epsg/
    """
    # o_proj = Proj("+init=" + out_proj)
    # i_proj = Proj("+init=" + in_proj)
    o_proj = CRS(out_proj)
    i_proj = CRS(in_proj)

    x, y = transform(i_proj, o_proj, float(lon), float(lat), always_xy=True)

    # Returns LAT, LONG   !!!!
    return y, x


def latlon_distance(origin, destination):
    '''
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    '''
    from math import radians, cos, sin, asin, sqrt
    lat1, lon1 = origin
    lat2, lon2 = destination
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = list(map(radians, [lon1, lat1, lon2, lat2]))
    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2.)**2 + cos(lat1) * cos(lat2) * sin(dlon/2.)**2
    c = 2 * asin(sqrt(a))
    # km = 6367 * c
    km = 6363 * c # Earth radius at around 57 degrees North
    return km * 1000
