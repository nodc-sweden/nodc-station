# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2020-10-09 17:22

@author: a002028

"""
from abc import ABC
import copy
import yaml
import pandas as pd
from nodc_station.validators.validator import ValidatorLog
from nodc_station.writers.writer import WriterBase


def cell_border_width(style_object, side='bottom', width='medium'):
    """Doc."""
    return ['border-' + side + '-width:' + width for v in style_object]


def get_station_break_index(df):
    return df.drop_duplicates(subset='statn', keep='last').index


class ValidationWriter(WriterBase, ABC):
    """
    """
    def __init__(self, *args, **kwargs):
        super(ValidationWriter, self).__init__()
        self.update_attributes(**kwargs)

    @staticmethod
    def write(file_path, log, **kwargs):
        """
        :param file_path: str
        :param list_obj: stations.validators.ValidatorLog.log
        :return:
        """
        with open(file_path, 'w') as file:
            yaml.safe_dump(log, file, indent=4, default_flow_style=False)


class ExcelWriter(WriterBase, ABC):
    """
    """
    def __init__(self, *args, **kwargs):
        super(ExcelWriter, self).__init__()
        self.update_attributes(**kwargs)

    def write(self, file_path, data, styled=False, **kwargs):
        """Write ValidatorLog.log to excel file.

        Args:
            file_path (str): Path to file
            exclude_approved_formats (bool): False | True. If True only disapproved tests will
                                                           be included in the file.
        """
        log_copy = copy.deepcopy(data)

        out_dict = self.get_writer_format(log_copy)
        df = pd.DataFrame(out_dict)
        df = df.sort_values(by=['statn', 'validator'])
        if styled:
            indices = get_station_break_index(df)
            df = df.style
            df = df.apply(
                cell_border_width,
                side='bottom',
                width='thin',
                subset=pd.IndexSlice[indices, :]
            )

        df.to_excel(
            file_path,
            sheet_name='log',
            na_rep='',
            index=None,
            engine='openpyxl' if styled else None,
        )

    def get_writer_format(self, data):
        """Return ValidatorLog.log in format likeable to this writer.
        stnreg_import:
            coordinates_dm:
                approved:
                    All good!
                disapproved: {}
        """
        out_dict = {
            'delivery': [],
            'statn': [],
            'validator': [],
            'approved': [],
            'comnt': [],
        }
        for delivery, item in data.items():
            for validator_name, item_element in item.items():
                length = len(item_element['approved'])
                if length:
                    out_dict['delivery'].extend([delivery] * length)
                    out_dict['statn'].extend(item_element['statn'])
                    out_dict['validator'].extend([validator_name] * length)
                    out_dict['approved'].extend(item_element['approved'])
                    out_dict['comnt'].extend(item_element['comnt'])
        return out_dict
