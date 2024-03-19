# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2020-10-05 08:48

@author: a002028

"""
import pandas as pd
import numpy as np


class PandasReaderBase:
    """
    """
    def __init__(self, *args, **kwargs):
        super(PandasReaderBase, self).__init__()

    def get(self, item):
        """
        :param item: str
        :return:
        """
        if item in self.__dict__.keys():
            return self.__getattribute__(item)
        else:
            print('Warning! Can´t find attribute: %s' % item)
            return 'None'

    @staticmethod
    def read(*args, **kwargs):
        """
        :param args: tuple
            Expects:
                file_path
        :param kwargs: dict
            Addition:
                header
                encoding
                dtype
                keep_default_na
        :return:
        """
        return pd.read_excel(*args, **kwargs)


class PandasXlsxReader(PandasReaderBase):
    """
    Reads txt / csv files
    """
    def __init__(self, *args, **kwargs):
        super(PandasXlsxReader, self).__init__()
        for key, item in kwargs.items():
            setattr(self, key, item)
