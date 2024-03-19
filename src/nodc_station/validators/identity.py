#!/usr/bin/env python
# Copyright (c) 2022 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2022-04-28 11:19

@author: johannes
"""
from nodc_station.validators.validator import Validator, ValidatorLog


class Name(Validator):
    """Check if a given name exists in the master name list."""

    def __init__(self, *args, **kwargs):
        self.name_set = None
        super(Name, self).__init__()
        for key, item in kwargs.items():
            setattr(self, key, item)

    def validate(self, list_obj, master=None, **kwargs):
        """Validate list.

        Args:
            list_obj: List of stations to validate.
            master: The master list to validate list_obj with.
            **kwargs: kwargs.

        Returns: Validation report (dictionary).
        """
        self.message(self.__class__.__name__,
                     f'Running validation on list: {list_obj.name}')
        self._setup_name_set(master)
        report = {
            'statn': [],
            'approved': [],
            'comnt': []
        }

        for name in list_obj.get('statn'):
            validation = self._validate(name)
            report['statn'].append(name)
            if validation:
                report['approved'].append('Failed')
                report['comnt'].append(validation)
            else:
                report['approved'].append('Passed')
                report['comnt'].append('')
                # report['comnt'].append('Name does not exists as a synonym in '
                #                        'the master list.')

        ValidatorLog.update_info(
            list_name=list_obj.get('name'),
            validator_name=self.name,
            info=report,
        )
        self.message(self.__class__.__name__, 'Validation complete\n')

    def _validate(self, name):
        """Validate and return validation string."""
        validation = name in self.name_set
        if validation:
            return 'Name already exists in SHARK station list'

    def _setup_name_set(self, master_list):
        """

        Args:
            master_list:
        """
        self.name_set = set(master_list.statn)


class Synonyms(Validator):
    """Check if a given name exists in the synonym list."""

    def __init__(self, *args, **kwargs):
        self.master_synonyms = {}
        super(Synonyms, self).__init__()
        for key, item in kwargs.items():
            setattr(self, key, item)

    def validate(self, list_obj, master=None, **kwargs):
        """Validate list.

        Args:
            list_obj: List of stations to validate.
            master: The master list to validate list_obj with.
            **kwargs: kwargs.

        Returns: Validation report (dictionary).
        """
        self.message(self.__class__.__name__,
                     f'Running validation on list: {list_obj.name}')
        self._setup_synonym_mapping(master)

        report = {
            'statn': [],
            'approved': [],
            'comnt': []
        }

        for name in list_obj.get('statn'):
            validation = self._validate(name)
            report['statn'].append(name)
            if validation:
                report['approved'].append('Failed')
                report['comnt'].append(validation)
            else:
                report['approved'].append('Passed')
                report['comnt'].append('')
                # report['comnt'].append('Name does not exists as a synonym in '
                #                        'the master list.')

        ValidatorLog.update_info(
            list_name=list_obj.get('name'),
            validator_name=self.name,
            info=report,
        )
        self.message(self.__class__.__name__, 'Validation complete\n')

    def _setup_synonym_mapping(self, master_list):
        """Append nominal name to each unique synonym.

         Based on the master list.
         """
        for statn, synos in zip(master_list.statn, master_list.synonyms):
            for syno in synos.split(';'):
                self.master_synonyms.setdefault(syno, []).append(statn)

    def _validate(self, name):
        """Validate and return validation string."""
        validation = self.master_synonyms.get(name)
        if validation:
            return 'Name exists as a synonym for the following ' \
                   'masterlist stations: {}'.format(' <AND> '.join(validation))
