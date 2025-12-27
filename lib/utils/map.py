from kivy.graphics   import Color, Line
from kivy.properties import ListProperty

from kivymd.material_resources   import dp
from kivymd.theming_dynamic_text import get_contrast_text_color
from kivymd.uix.widget           import MDWidget


class Map(MDWidget):
    '''
        A lightweight map widget that renders a polyline from latitude/longitude points.

        The widget normalizes geographic coordinates into its own width/height
        and draws a line connecting them. It adapts its colors automatically
        to the current theme.

        Attributes:
            points_to_show (ListProperty): A list of dictionaries containing
                geographic coordinates with keys ``'lat'`` and ``'lon'``.
                Example: ``[{"lat": 50.1, "lon": 8.6}, {"lat": 50.2, "lon": 8.7}]``
    '''
    points_to_show = ListProperty([])

    def __init__(self, **kwargs):
        '''
            Initialize the map widget and bind it to theme changes.
        '''
        super().__init__(**kwargs)

        self.padding = dp(10)

        # Bind to theme changes - bind to the actual properties that change
        self.theme_cls.bind(theme_style = self._update_colors)
        self._update_colors()

    def on_size(self, *args):
        '''
            Redraw the polyline when the widget is resized.
        '''
        self.canvas.after.clear()
        self.draw_line()

    def draw_line(self):
        '''
            Normalize coordinates and draw a line connecting all points
            from `points_to_show`.
        '''

        try:
            lons = [float(point['lon']) for point in self.points_to_show]
            lats = [float(point['lat']) for point in self.points_to_show]

            min_lon, max_lon = min(lons), max(lons)
            min_lat, max_lat = min(lats), max(lats)

            points = []
            for point in self.points_to_show:
                lon = float(point['lon'])
                lat = float(point['lat'])

                x = self.lon_norm(lon, min_lon, max_lon, self.width  - 2 * self.padding) + self.pos[0] + self.padding
                y = self.lat_norm(lat, min_lat, max_lat, self.height - 2 * self.padding) + self.pos[1] + self.padding

                points.append(x)
                points.append(y)

            self.add_line(points)

        except Exception as e:
            print('[MAP]', f'Error drawing map: {e}')

    def add_line(self, points):
        '''
            Add a line with theme-appropriate color to the canvas.
            Args:
                points (list[float]): Flattened list of x, y coordinates.
        '''
        color = Color(*get_contrast_text_color(self.theme_cls.bg_dark))
        line = Line(points = points, width = dp(1.2))
        self.canvas.after.add(color)
        self.canvas.after.add(line)

    def lon_norm(self, lon, min_lon, max_lon, width):
        if max_lon == min_lon:
            return width / 2
        else:
            return (lon - min_lon) / (max_lon - min_lon) * width

    def lat_norm(self, lat, min_lat, max_lat, height):
        if max_lat == min_lat:
            return height / 2
        else:
            return (lat - min_lat) / (max_lat - min_lat) * height

    def _update_colors(self, *args):
        '''
            Update widget background color and redraw the line.
        '''
        # Update background color
        self.md_bg_color = self.theme_cls.bg_dark
        self.canvas.after.clear()
        self.draw_line()
