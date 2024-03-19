# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2020-09-28 10:44

@author: a002028

"""
import folium
from folium.plugins import MarkerCluster
from nodc_station.writers.writer import WriterBase


def get_html_string_format(*args):
    s = '<b>'
    for a in args:
        new_line = a + ': %s<br>'
        s += new_line
    s += '</b>'
    return s


class MapWriter(WriterBase):
    """
    """
    def __init__(self, **kwargs):
        super(MapWriter, self).__init__()
        self.update_attributes(**kwargs)
        self.map = folium.Map(**self.map_settings)
        self.html_fmt = get_html_string_format(*(self.marker_tag_attributes.get(key)
                                                 for key in self.marker_tag_attributes))

    def add_to_map(self, list_obj):
        """
        :param list_obj:
        :return:
        """
        self.add_markers(list_obj)
        if self.station_radius:
            self.add_radius_circles(list_obj)

        folium.LayerControl().add_to(self.map)

    def write(self, file_path, list_obj, **kwargs):
        """
        :param file_path:
        :param list_obj:
        :return:
        """
        # print(list_obj)
        # if not isinstance(list_obj, dict):
        #     list_obj = {list_obj.name: list_obj}
        self.add_to_map(list_obj)

        self._write(file_path)

    def _write(self, file_path):
        """
        :param file_path:
        :return:
        """
        self.map.save(file_path)

    def add_markers(self, list_objs):
        """"""
        for list_name, item in list_objs.items():
            fg = self.get_group(name=list_name,
                                add_to_map=True,
                                return_group=True)

            mc = MarkerCluster() if (self.new_stations_as_cluster or list_name == 'master') else None

            for idx in range(item.length):
                html_obj = self.get_html_object(item, idx)
                popup = self.get_popup(html_obj)
                marker = self.get_marker([item.get('lat_dd')[idx],
                                          item.get('lon_dd')[idx]],
                                         popup=popup,
                                         icon=folium.Icon(color='blue' if list_name == 'master' else 'red', icon='map-marker'),
                                         tooltip=item.get('statn')[idx] or 'Click me!')

                if self.new_stations_as_cluster or list_name == 'master':
                    marker.add_to(mc)
                else:
                    marker.add_to(fg)

            if self.new_stations_as_cluster or list_name == 'master':
                mc.add_to(fg)

    def add_radius_circles(self, list_objs):
        """"""
        for list_name, item in list_objs.items():
            fg = self.get_group(name='-'.join([list_name, 'radius']),
                                add_to_map=True,
                                return_group=True)

            mc = MarkerCluster() if (self.new_stations_as_cluster or list_name == 'master') else None

            check = False
            for idx in range(item.length):
                if item.has_attribute('radius'):
                    if item.get('radius')[idx]:
                        check = True
                        circle = folium.Circle(tuple([item.get('lat_dd')[idx], item.get('lon_dd')[idx]]),
                                               radius=int(item.get('radius')[idx]),
                                               fill_color='#3186cc',
                                               weight=.5,
                                               )
                        if self.new_stations_as_cluster or list_name == 'master':
                            circle.add_to(mc)
                        else:
                            circle.add_to(fg)
            if check and (self.new_stations_as_cluster or list_name == 'master'):
                mc.add_to(fg)

    def get_group(self, **kwargs):
        """
        :param kwargs:
        :return:
        """
        fg = folium.FeatureGroup(**kwargs)

        if kwargs.get('add_to_map'):
            fg.add_to(self.map)

        if kwargs.get('return_group'):
            return fg

    def get_html_object(self, item, list_idx):
        """
        :param item:
        :param list_idx:
        :return:
        """
        args = []
        for tag in self.marker_tag_attributes:
            value = item.get(tag)
            if type(value) != str:
                value = value[list_idx]#.encode(encoding='cp1252').decode()
            else:
                value = '-'
            args.append(value)
        html_string = self.html_fmt % tuple(args)
        # print('self.html_fmt', type(self.html_fmt), self.html_fmt)
        return folium.Html(html_string, script=True)

    @property
    def html_string(self):
        return self.map._repr_html_()

    @staticmethod
    def get_marker(*args, **kwargs):
        """
        :param args:
        :param kwargs:
        :return:
        """
        return folium.Marker(*args, **kwargs)

    @staticmethod
    def get_popup(html_obj):
        """
        :param html_obj:
        :return:
        """
        return folium.Popup(html_obj, max_width=500)

    def add_polyline(self, points, name):
        folium.PolyLine(points,
                        weight=4.,
                        opacity=.5,
                        popup=folium.Popup(name, max_width=100)
                        ).add_to(self.map)


if __name__ == '__main__':

    m = MapWriter(map_settings={'location': [61.75, 19.45],
                                'zoom_start': 5},
                  marker_tag_attributes={'statn': 'statn',
                                         'id': 'id',
                                         'lat_dd': 'lat_dd',
                                         'lon_dd': 'lon_dd'})
    # m._write('map.html')
