# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2020-10-12 11:16

@author: a002028

"""
import pandas as pd
from nodc_station.validators.validator import Validator, ValidatorLog


class MandatoryAttributes(Validator):
    """
    """
    def __init__(self, *args, **kwargs):
        super(MandatoryAttributes, self).__init__()
        for key, item in kwargs.items():
            setattr(self, key, item)

    def validate(self, list_obj, **kwargs):
        """
        :param list_obj: stations.handler.List
        :return:
        """
        assert self.attributes

        report = {
            'statn': [],
            'approved': [],
            'comnt': []
        }

        for attr in self.attributes:
            report['statn'].append('')
            if list_obj.has_attribute(attr):
                if list_obj.get(attr).all():
                    report['approved'].append('Passed')
                    report['comnt'].append(f'Attribute exists ({attr})')
                else:
                    report['approved'].append('Failed')
                    report['comnt'].append(f'WARNING! Missing values for attribute: {attr}')
            else:
                report['approved'].append('Failed')
                report['comnt'].append(f'WARNING! Missing attribute: {attr}')

        ValidatorLog.update_info(
            list_name=list_obj.get('name'),
            validator_name=self.name,
            info=report,
        )


class MasterAttributes(Validator):
    """
    Check if master list contains information that a given list does not.
    If so: take info from master and copy to the given list.

    Mandatory attribute used to compare a given list to the master list: "id"
    """
    def __init__(self, *args, **kwargs):
        super(MasterAttributes, self).__init__()
        for key, item in kwargs.items():
            setattr(self, key, item)

    def validate(self, list_obj, **kwargs):
        """
        :param list_obj: stations.handler.List
        :return:
        """
        # assert self.attributes
        assert 'master' in kwargs

        if list_obj.name == 'master':
            # No need to validate our master list (against itself)
            return

        list_master = kwargs.get('master')

        report = {
            'approved': {},
            'comnt': {}
        }

        if list_obj.has_values(self.id_key):
            list_obj.boolean = list_obj.get(self.id_key).ne('')
            id_list = list_obj.get(self.id_key, boolean=True)

            list_master.boolean = list_master.get(self.id_key).isin(id_list.to_list())
            if list_master.boolean.any():

                # Add attributes that the given list does not possess (attributes from master list)
                d = {a: pd.Series([''] * list_obj.length).rename(a)
                     for a in list_master.loaded_attributes
                     if not list_obj.has_attribute(a)}
                list_obj.set_attributes(**d)

                for id in id_list:
                    list_master.boolean = list_master.get(self.id_key).eq(id)
                    list_obj.boolean = list_obj.get(self.id_key).eq(id)

                    for attr in list_obj.loaded_attributes:
                        if list_master.has_attribute(attr):
                            value = list_obj.get(attr, boolean=True, value=True)
                            value_master = list_master.get(attr, boolean=True, value=True)
                            if value_master and value == '':
                                list_obj.set_value(attr, value_master, boolean=True)


        # for attr in self.attributes:
        #     if list_obj.has_attribute(attr):
        #         if list_obj.get(attr).all():
        #             report['approved'].setdefault(attr, 'No missing values')
        #         else:
        #             report['disapproved'].setdefault(attr, 'WARNING! Missing values')
        #     else:
        #         report['disapproved'].setdefault(attr, 'WARNING! Missing attribute')
        #
        # ValidatorLog.update_info(
        #     list_name=list_obj.get('name'),
        #     validator_name=self.name,
        #     info=report,
        # )
