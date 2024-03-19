# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2020-09-24 16:27

@author: a002028

"""
import pandas as pd
import numpy as np


class NumpyReaderBase:
    """
    """
    def __init__(self):
        super(NumpyReaderBase, self).__init__()

    @staticmethod
    def read(*args, **kwargs):
        """
        :param args:
        :param kwargs:
        :return:
        """
        return np.loadtxt(*args, **kwargs)


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
                sep
                encoding
                dtype
                keep_default_na
        :return:
        """
        return pd.read_csv(*args, **kwargs)


class NoneReaderBase:
    """
    Dummy base
    """
    def __init__(self):
        super(NoneReaderBase, self).__init__()

    @staticmethod
    def read(*args, **kwargs):
        print('Warning! No data was read due to unrecognizable reader type')


class PandasTxtReader(PandasReaderBase):
    """
    Reads txt / csv files
    """
    def __init__(self, *args, **kwargs):
        super(PandasTxtReader, self).__init__()
        for key, item in kwargs.items():
            setattr(self, key, item)


def text_reader(reader_type, *args, **kwargs):
    """
    Dynamic text reader.
    :param reader_type: str, decides what type of reader base to be used.
    :param args: tuple
    :param kwargs: dict
    :return:
    """
    if reader_type == 'pandas':
        base = PandasReaderBase
    elif reader_type == 'numpy':
        base = NumpyReaderBase
    else:
        base = NoneReaderBase

    class TextReader(base):
        """
        """
        def __init__(self):
            super(TextReader, self).__init__()

    tr = TextReader()
    return tr.read(*args, **kwargs)
