# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2020-09-28 16:09

@author: a002028

"""
from abc import ABC


class WriterBase(ABC):
    """
    """
    def __init__(self, *args, **kwargs):
        super(WriterBase, self).__init__()
        self.attribute_constants = None
        self.attribute_mapping = None
        self.default_file_name = None
        self.header = None
        self.meta_header = None
        self.map_settings = None
        self.marker_tag_attributes = None
        self.station_radius = False
        self.new_stations_as_cluster = True

    def update_attributes(self, **kwargs):
        if 'second_update' in kwargs:
            for key in kwargs.copy():
                if not hasattr(self, key):
                    kwargs.pop(key)
            print('second_update', kwargs)

        for key, item in kwargs.items():
            setattr(self, key, item)

    def write(self, *args, **kwargs):
        """
        :param args:
        :param kwargs:
        :return:
        """
        raise NotImplementedError

    def _write(self, *args, **kwargs):
        """
        :param args:
        :param kwargs:
        :return:
        """
        raise NotImplementedError
