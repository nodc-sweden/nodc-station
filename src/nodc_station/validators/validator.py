# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2020-10-09 12:54

@author: a002028

"""
from abc import ABC
# import logging
# logging.root.setLevel(logging.NOTSET)
# logging(filename='myapp.log', format='%(message)s', level=logging.NOTSET)
# logging.root.setLevel(logging.NOTSET)


class Validator(ABC):
    """
    Base class for validators.
    """
    def __init__(self, *args, **kwargs):
        super(Validator, self).__init__()
        self.name = None
        self.id_key = None
        self.lat_key = None
        self.lon_key = None
        self.fill_in_new_values = None
        self.attributes = None

    def validate(self, *args, **kwargs):
        raise NotImplementedError

    @staticmethod
    def message(*args):
        """
        :param args: tuple of strings
        :return: print to console
        """
        # FIXME We intend to introduce logging..
        print(' - '.join(args))
        # print('SHOULD print: %s' % ' - '.join(args))
        # logging.info(' - '.join(args))


class ValidatorLog:
    """
    Logger for validators.

    Each validator categorizes validation in "approved" and "disapproved" validation.

    log: {
        'list_name': {
            'validator_name': {
                approved: [],
                disapproved: []
                }
        ... }
    ... }
    """
    log = {}

    def __init__(self, *args, reset_log=False, list_name=False,
                 validator_name=None, info=None):
        if any(args):
            if 'etc' not in self.log:
                self.log['etc'] = []
            for a in args:
                self.log['etc'].append(a)

        if reset_log:
            self.log = {}

        if list_name:
            if list_name not in self.log:
                self.log[list_name] = {}

            if validator_name:
                self.log[list_name].setdefault(
                    validator_name,
                    info
                )

    @classmethod
    def update_info(cls, *args, **kwargs):
        return cls(*args, **kwargs)
