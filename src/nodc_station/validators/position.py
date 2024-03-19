# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2020-09-29 18:41

@author: a002028
"""
import pandas as pd
import geopandas as gp
from shapely.geometry import Point
from nodc_station.utils import distance_between_points_meters
from nodc_station.validators.validator import Validator, ValidatorLog


class MatchMasterListValidator(Validator):
    """Validate if a given position lies within radius
    of stations in the SHARK master list."""

    def __init__(self, *args, **kwargs):
        self.masterframe = gp.GeoDataFrame()
        super(MatchMasterListValidator, self).__init__()
        for key, item in kwargs.items():
            setattr(self, key, item)

    def _setup_masterframe(self, master_list):
        """Doc."""
        if master_list and self.masterframe.empty:
            columns = ('statn', 'radius', 'lat_sweref99tm', 'lon_sweref99tm')
            self.masterframe = gp.GeoDataFrame({
                key: master_list.get(key).astype(
                    float if key != 'statn' else str) for key in columns
            })
            self.masterframe.geometry = self.masterframe[
                ['lon_sweref99tm', 'lat_sweref99tm']].apply(
                lambda xy: Point(xy), axis=1)
            self.masterframe.geometry = self.masterframe.buffer(
                self.masterframe['radius'])

    def point_within_radius(self, point):
        """With "point_within_radius" we mean that the point lies within
        radius of an other station in the master list.

        Boolean operation. If any True: return message
        :param point: shapely.geometry.Point
        :return: str / False
        """
        boolean = self.masterframe.contains(point)
        if boolean.any():
            statns = []
            for row in self.masterframe[boolean].itertuples():
                d = distance_between_points_meters(row.lon_sweref99tm, point.x,
                                                   row.lat_sweref99tm, point.y)
                statns.append(f'{row.statn} [{round(d, 1)} m]')

            return 'Lies within radius of the following masterlist stations: ' \
                   '{}'.format(' <AND> '.join(statns)
            )
        else:
            return False

    def validate(self, list_obj, **kwargs):
        """
        :param list_obj: stations.handler.List
        :return:
        """
        self._setup_masterframe(kwargs.get('master'))

        self.message(self.__class__.__name__,
                     f'Running validation on list: {list_obj.name}')
        report = {
            'statn': [],
            'approved': [],
            'comnt': []
        }
        for name, north, east in zip(list_obj.get('statn'),
                                     list_obj.get(self.lat_key),
                                     list_obj.get(self.lon_key)):
            point = Point(float(east), float(north))
            validation_fail = self.point_within_radius(point)
            report['statn'].append(name)
            if validation_fail:
                report['approved'].append('Failed')
                report['comnt'].append(validation_fail)
            else:
                report['approved'].append('Passed')
                report['comnt'].append('')
        ValidatorLog.update_info(
            list_name=list_obj.get('name'),
            validator_name=self.name,
            info=report,
        )

        self.message(self.__class__.__name__, 'Validation complete\n')


class PositionInOceanValidator(Validator):
    """
    Using SVAR areas to validate if a given position lies in sea water or outside.
    Example of shapefile that can be used: Havsomr_SVAR_2016_3c_CP1252.shp

    NOTE: Version 2016_3c does contain scale errors, new version (may 2021) should be more accurate..
    """
    def __init__(self, *args, **kwargs):
        super(PositionInOceanValidator, self).__init__()
        assert ('geodataframe' in kwargs) or ('file_path' in kwargs)
        for key, item in kwargs.items():
            setattr(self, key, item)

        if not hasattr(self, 'geodataframe'):
            self.geodataframe = gp.read_file(kwargs.get('file_path'))

    def point_in_polygons(self, point):
        """
        With "point_in_polygons" we mean that the point lies in the ocean.

        Boolean operation. If any True: return True
        :param point: shapely.geometry.Point
        :return: True / False
        """
        return self.geodataframe.contains(point).any()

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
        for name, north, east in zip(list_obj.get('statn'),
                                     list_obj.get(self.lat_key),
                                     list_obj.get(self.lon_key)):
            point = Point(float(east), float(north))
            validation = self.point_in_polygons(point)
            report['statn'].append(name)
            if validation:
                report['approved'].append('Passed')
                report['comnt'].append('')
            else:
                report['approved'].append('Failed')
                report['comnt'].append('On land')
        ValidatorLog.update_info(
            list_name=list_obj.get('name'),
            validator_name=self.name,
            info=report,
        )

        self.message(self.__class__.__name__, 'Validation complete\n')


if __name__ == '__main__':
    from nodc_station.main import App
    app = App()
    app.read_list(
        'C:/Arbetsmapp/config/station.txt',
        reader='shark_master',
        list_name='master'
    )

    fid = r'C:\station_exports\lisas_nya\station_list_stnreg.xlsx'
    app.read_list(
        fid,
        reader='stnreg',
        list_name='stnreg_import',
    )
    validator = MatchMasterListValidator(**{'lat_key': 'lat_sweref99tm', 'lon_key': 'lon_sweref99tm'})
    validator.validate(app.lists['stnreg_import'], master=app.lists['master'])