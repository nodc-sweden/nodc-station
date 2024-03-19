# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2020-09-29 18:41

@author: a002028

"""
import pandas as pd
from nodc_station.utils import (
    decmin_to_decdeg,
    decdeg_to_decmin,
    round_value,
    transform_ref_system
)
from nodc_station.validators.validator import Validator, ValidatorLog


class SweRef99tmValidator(Validator):
    """
    Coordinates in SWEREF 99TM are mandatory information for any list
    """
    def __init__(self, *args, **kwargs):
        super(SweRef99tmValidator, self).__init__()
        for key, item in kwargs.items():
            setattr(self, key, item)

    def validate(self, list_obj, **kwargs):
        """
        :param list_obj: stations.handler.List
        :return:
        """
        self.message(self.__class__.__name__, 'Running validation on list: %s' % list_obj.name)

        report = {
            'statn': [],
            'approved': [],
            'comnt': []
        }
        any_disapproved = False
        if list_obj.has_values(self.lat_key) and list_obj.has_values(self.lon_key):
            list_obj.boolean = list_obj.get(self.lat_key).ne('') & list_obj.get(self.lon_key).ne('')
            for name, north, east in zip(list_obj.get('statn', boolean=True),
                                         list_obj.get(self.lat_key, boolean=True),
                                         list_obj.get(self.lon_key, boolean=True)):
                report['statn'].append(name)
                report['approved'].append('Passed')
                report['comnt'].append('')

            list_obj.boolean = list_obj.get(self.lat_key).eq('') | list_obj.get(self.lon_key).eq('')
            for name, north, east in zip(list_obj.get('statn', boolean=True),
                                         list_obj.get(self.lat_key, boolean=True),
                                         list_obj.get(self.lon_key, boolean=True)):
                report['statn'].append(name)
                report['approved'].append('Failed')
                report['comnt'].append('Missing info')
                any_disapproved = True
        else:
            any_disapproved = True
            for name in list_obj.get('statn'):
                report['statn'].append(name)
                report['approved'].append('Failed')
                report['comnt'].append('Missing info')

        if any_disapproved and self.fill_in_new_values:
            self._calculate_coord_values(list_obj)

        ValidatorLog.update_info(
            list_name=list_obj.get('name'),
            validator_name=self.name,
            info=report,
        )

        self.message(self.__class__.__name__, 'Validation complete\n')

    def _calculate_coord_values(self, list_obj):
        """
        :param list_obj:
        :return:
        """
        if not list_obj.has_values(self.lat_key):
            d = {self.lat_key: pd.Series([''] * list_obj.length).rename(self.lat_key),
                 self.lon_key: pd.Series([''] * list_obj.length).rename(self.lon_key)}
            list_obj.set_attributes(**d)

        list_obj.boolean = list_obj.get(self.lat_key).eq('')
        if not all(list_obj.boolean):
            return

        if not list_obj.has_values('lat_dd'):
            if list_obj.has_values('lat_dm'):
                if not list_obj.has_attribute('lat_dd'):
                    d = {'lat_dd': pd.Series([''] * list_obj.length).rename('lat_dd'),
                         'lon_dd': pd.Series([''] * list_obj.length).rename('lon_dd')}
                    list_obj.set_attributes(**d)
                new_lat = []
                new_lon = []
                for lat, lon in zip(list_obj.get('lat_dm'),
                                    list_obj.get('lon_dm')):
                    new_lat.append(decmin_to_decdeg(lat, decimals=6))
                    new_lon.append(decmin_to_decdeg(lon, decimals=6))
                list_obj.update_attribute_values('lat_dd', new_lat)
                list_obj.update_attribute_values('lon_dd', new_lon)
            else:
                raise AttributeError('Missing coordinates, in any format! Fix it!')

        new_lat = []
        new_lon = []
        for lat, lon in zip(list_obj.get('lat_dd', boolean=True),
                            list_obj.get('lon_dd', boolean=True)):
            newla, newlo = transform_ref_system(lat=lat, lon=lon, in_proj='EPSG:4326', out_proj='EPSG:3006')
            new_lat.append(round_value(newla, nr_decimals=0))
            new_lon.append(round_value(newlo, nr_decimals=0))

        list_obj.update_attribute_values(self.lat_key, new_lat)
        list_obj.update_attribute_values(self.lon_key, new_lon)

        self.validate(list_obj)


class DegreeValidator(Validator):
    """
    Coordinates in format Decimal degrees are selectable, not mandatory.
    Format: DD.dddddd
    """
    def __init__(self, *args, **kwargs):
        super(DegreeValidator, self).__init__()
        for key, item in kwargs.items():
            setattr(self, key, item)

    def validate(self, list_obj, **kwargs):
        """
        :param list_obj: stations.handler.List
        :return:
        """
        self.message(self.__class__.__name__, 'Running validation on list: %s' % list_obj.name)

        report = {
            'statn': [],
            'approved': [],
            'comnt': []
        }

        if not list_obj.has_attribute(self.lat_key):
            d = {self.lat_key: pd.Series([''] * list_obj.length).rename(self.lat_key),
                 self.lon_key: pd.Series([''] * list_obj.length).rename(self.lon_key)}
            list_obj.set_attributes(**d)

        if all(list_obj.get(self.lat_key)) and all(list_obj.get(self.lon_key)):
            return True
        else:
            list_obj.boolean = list_obj.get(self.lat_key).eq('')

            if self.fill_in_new_values:
                new_lat = []
                new_lon = []
                for lat, lon in zip(list_obj.get('lat_sweref99tm', boolean=True),
                                    list_obj.get('lon_sweref99tm', boolean=True)):
                    newla, newlo = transform_ref_system(lat=lat, lon=lon)
                    new_lat.append(round_value(newla, nr_decimals=4))
                    new_lon.append(round_value(newlo, nr_decimals=4))

                list_obj.update_attribute_values(self.lat_key, new_lat)
                list_obj.update_attribute_values(self.lon_key, new_lon)

                for name, north, east in zip(list_obj.get('statn', boolean=True),
                                             list_obj.get(self.lat_key, boolean=True),
                                             list_obj.get(self.lon_key, boolean=True)):
                    report['statn'].append(name)
                    report['approved'].append('Passed')
                    report['comnt'].append('')
            else:
                for name, north, east in zip(list_obj.get('statn', boolean=True),
                                             list_obj.get(self.lat_key, boolean=True),
                                             list_obj.get(self.lon_key, boolean=True)):
                    report['statn'].append(name)
                    report['approved'].append('Failed')
                    report['comnt'].append('Current settings do not allow '
                                           'us to "fill_in_new_values"')

        ValidatorLog.update_info(
            list_name=list_obj.get('name'),
            validator_name=self.name,
            info=report,
        )

        self.message(self.__class__.__name__, 'Validation complete\n')


class DegreeMinuteValidator(Validator):
    """
    Coordinates in format Degrees - decimal-Minutes are selectable, not mandatory.
    Format: DDMM.mmm
    """
    def __init__(self, *args, **kwargs):
        super(DegreeMinuteValidator, self).__init__()
        for key, item in kwargs.items():
            setattr(self, key, item)

    def validate(self, list_obj, **kwargs):
        """
        :param list_obj: stations.handler.List
        :return:
        """
        self.message(self.__class__.__name__, 'Running validation on list: %s' % list_obj.name)

        report = {
            'statn': [],
            'approved': [],
            'comnt': []
        }

        if not list_obj.has_attribute(self.lat_key):
            d = {self.lat_key: pd.Series([''] * list_obj.length).rename(self.lat_key),
                 self.lon_key: pd.Series([''] * list_obj.length).rename(self.lon_key)}
            list_obj.set_attributes(**d)

        list_obj.boolean = list_obj.get(self.lat_key).str.contains('°')
        if list_obj.boolean.any():
            new_lat = [p.replace('°', '').replace('N', '')
                       for p in list_obj.get(self.lat_key, boolean=True)]
            new_lon = [p.replace('°', '').replace('E', '')
                       for p in list_obj.get(self.lon_key, boolean=True)]
            list_obj.update_attribute_values(self.lat_key, new_lat)
            list_obj.update_attribute_values(self.lon_key, new_lon)

        if not all(list_obj.get(self.lat_key)):
            list_obj.boolean = list_obj.get(self.lat_key).eq('')

            if self.fill_in_new_values:
                new_lat = [decdeg_to_decmin(p) for p in list_obj.get('lat_dd', boolean=True)]
                new_lon = [decdeg_to_decmin(p) for p in list_obj.get('lon_dd', boolean=True)]

                list_obj.update_attribute_values(self.lat_key, new_lat)
                list_obj.update_attribute_values(self.lon_key, new_lon)

                for name, north, east in zip(list_obj.get('statn', boolean=True),
                                             list_obj.get(self.lat_key, boolean=True),
                                             list_obj.get(self.lon_key, boolean=True)):
                    report['statn'].append(name)
                    report['approved'].append('Passed')
                    report['comnt'].append('')
            else:
                for name, north, east in zip(list_obj.get('statn', boolean=True),
                                             list_obj.get(self.lat_key, boolean=True),
                                             list_obj.get(self.lon_key, boolean=True)):
                    report['statn'].append(name)
                    report['approved'].append('Failed')
                    report['comnt'].append('Current settings do not allow '
                                           'us to "fill_in_new_values"')

        ValidatorLog.update_info(
            list_name=list_obj.get('name'),
            validator_name=self.name,
            info=report,
        )

        self.message(self.__class__.__name__, 'Validation complete\n')
