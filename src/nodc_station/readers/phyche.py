# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2021-03-19 18:41
@author: johannes
"""
import pandas as pd
from nodc_station.readers.xlsx import PandasXlsxReader
from nodc_station.utils import eliminate_empty_rows


class PhysicalChemicalExcelReader(PandasXlsxReader):
    """
    Reads xlsx files
    """
    def __init__(self, *args, **kwargs):
        self.columns = None
        super().__init__(*args, **kwargs)

    def read(self, *args, **kwargs):
        if kwargs.get('dtype') == '':
            kwargs['dtype'] = str
        df = pd.read_excel(*args, **kwargs)
        df = self.filter_data(df)
        return df

    def filter_data(self, df):
        df = eliminate_empty_rows(df.loc[:, self.columns].drop_duplicates().reset_index(drop=True))
        return df
