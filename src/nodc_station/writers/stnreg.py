# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2020-09-25 13:28

@author: a002028

"""
import pandas as pd
from nodc_station.utils import get_now_time
from nodc_station.writers.writer import WriterBase


class StnRegWriter(WriterBase):
    """
    """
    def __init__(self, *args, **kwargs):
        super(StnRegWriter, self).__init__()
        self.update_attributes(**kwargs)

    def write(self, file_path, list_obj, **kwargs):
        """
        :param file_path: str
        :param list_obj: dictionary of stations.handler.List
        :return:
        """
        mf = self.get_metaframe()
        df = pd.DataFrame(columns=self.header, index=[])
        for list_name, item in list_obj.items():
            list_df = pd.DataFrame(columns=self.header, index=[])
            for col in self.header:
                lst_key = self.attribute_mapping.get(col)
                if lst_key and hasattr(item, lst_key):
                    list_df[col] = item.get(lst_key)
                else:
                    value = self.attribute_constants.get(col) or ''
                    list_df[col] = [value] * item.length
            df = df.append(list_df, ignore_index=True)
        df = df.reset_index(drop=True)

        self._write({'Provplatser': df,
                     'Metadata': mf},
                    file_path)

    def _write(self, dictionary, path_to_new_file):
        """
        :param dictionary: dictionary
        :param path_to_new_file: str
        :return:
        """
        xls = XlsxWriter(file_path=path_to_new_file)
        xls.write_multiple_sheets(dictionary)

    def get_metaframe(self):
        """
        :return:
        """
        mf = pd.DataFrame(columns=self.meta_header, index=[0])
        for col in self.meta_header:
            if col == 'Datum':
                mf[col] = get_now_time()
            else:
                mf[col] = self.attribute_constants.get(col) or ''

        return mf


class XlsxWriter:
    """
    """
    def __init__(self, **kwargs):
        self.xlsx_writer = pd.ExcelWriter(kwargs.get('file_path'),
                                          engine='openpyxl')

    def _load_xlsx_writer(self, save_path, engine='openpyxl'):
        """
        Create a Pandas Excel writer using engine.
        :param save_path: str, path to file
        :param engine: Engine for the writer
        :return: Pandas Excel writer using engine.
        """
        raise NotImplementedError

    def write_multiple_sheets(self, dictionary):
        """
        :param dictionary: dictionary with pd.DataFrames
        :return:
        """
        for sheet_name, frame in dictionary.items():
            frame.to_excel(self.xlsx_writer,
                           sheet_name=sheet_name,
                           na_rep='',
                           index=False,
                           encoding='cp1252')
        self.close_writer()

    def close_writer(self):
        """
        Close the Pandas Excel writer and save the Excel file.
        :return:
        """
        self.xlsx_writer.save()
