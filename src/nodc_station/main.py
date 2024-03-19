# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2020-09-24 16:45

@author: a002028

"""
import pandas as pd
from nodc_station.config import Settings
from nodc_station.handler import MultiList


class App:
    """
    Keep it clean, keep it tidy!
    - read
    - validate
    - write
    """

    def __init__(self, *args, **kwargs):
        self.settings = Settings(**kwargs)
        self.lists = MultiList()
        self.validated = set([])

    def validate_list(self, *args, validator_list=None, **kwargs):
        """
        :param validator_list:
        :param args:
            Expects:
                list_name(s)
        :param kwargs:
            Addition:
                validator_list
        :return:
        """
        validator_list = validator_list or self.settings.validators_sorted
        for list_name in args:
            for validator_name in validator_list:
                validator = self.settings.load_validator(validator_name)
                validator.validate(self.lists.select(list_name),
                                   master=self.lists.select('master'))

            self.validated.add(validator_name)

    def read_list(self, *args, reader=None, list_name=None, **kwargs):
        """
        :param args: tuple
            Expects:
                file_path
        :param kwargs: dict
            Expects:
                reader
        :return:
        """
        if not reader:
            raise ValueError(
                'Missing reader! Please give one as input '
                '(App.read_list(reader=NAME_OF_READER)')
        if not list_name:
            raise ValueError(
                'Missing list_name! Please give one as input '
                '(App.read_list(list_name=NAME_OF_LIST)')
        if not args:
            raise ValueError(
                'Missing file path! Please give one as input '
                '(App.read_list(PATH_TO_DATA_SOURCE)')

        reader_kwargs = self.settings.readers[reader].get('reader_kwargs') or {}

        reader = self.settings.load_reader(reader)

        if 'reader_kwargs' in kwargs:
            for key, value in kwargs['reader_kwargs'].items():
                reader_kwargs[key] = value

        reader_kwargs = reader_kwargs or kwargs

        if reader_kwargs.get('dtype') == '':
            reader_kwargs['dtype'] = str

        lst = reader.read(*args, **reader_kwargs)

        self.lists.append_new_list(
            name=list_name,
            meta=reader.get('meta'),
            data=lst,
            attributes=self.settings.attributes,
        )

    def add_list_data(self,
                      data: pd.DataFrame,
                      list_name: str):
        """Adds a pandas dataframe to the list"""
        # reader = self.settings.load_reader('stnreg')  # Could be any
        self.lists.append_new_list(
            name=list_name,
            data=data,
            attributes=self.settings.attributes
        )

    def write_list(self, *args, writer=None, list_name=None, list_names=None,
                   **kwargs):
        """
        :param args: tuple
        :param kwargs: dict.
            Expects:
                writer
                list_name or list_names or data
            Addition:
                file_path
                file_name
        :return:
        """
        if not writer:
            raise ValueError(
                'Missing writer! Please give one as input '
                '(App.write_list(writer=NAME_OF_WRITER)')

        file_path = kwargs.pop('file_path', None)

        writer = self.settings.load_writer(writer)
        writer.update_attributes(second_update=True, **kwargs)
        kwargs.setdefault('default_file_name', writer.default_file_name)
        if not file_path:
            file_path = self.settings.get_export_file_path(**kwargs)
        kwargs.pop('file_path', None)
        if 'data' in kwargs:
            lst = kwargs.pop('data')
        else:
            lst = self.lists.select(list_name or list_names, for_writer=True)

        print('Writing stations to: %s' % file_path)
        writer.write(file_path, lst, **kwargs)
        print('Writer done!')


if __name__ == '__main__':
    app = App()
    app.read_list(
        'C:/Arbetsmapp/config/station.txt',
        reader='shark_master',
        list_name='master',
    )

    # new_stations = {
    #     'statn': ['N Fredriksskansbron'.upper(), 'Vallviksfjärden centroid'],
    #     'lat_sweref99tm': ['6729995', '6782432'],
    #     'lon_sweref99tm': ['618965', '620581'],
    # }
    #
    # app.lists.append_new_list(
    #     name='new_stations',
    #     data=new_stations,
    #     attributes={k: k for k in list(new_stations)}
    # )

    # app.validate_list('new_stations')
    #
    # app.write_list(writer='map', list_names=['master', 'new_stations'])

    # app.write_list(writer='stnreg', list_name='new_stations')
