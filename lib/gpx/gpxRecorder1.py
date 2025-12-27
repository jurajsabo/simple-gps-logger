import os

from lib.gpx.gpxRecorder import GPXRecorder

from lib.utils.units import \
(
    utc_ms_to_gpx_time,
    utc_ms_time,
    meters_to_gpx_distance,
    mps_to_gpx_speed,
    units_to_gpx_distance,
    units_to_gpx_speed
)


class GPXRecorder1(GPXRecorder):
    '''
        Streaming GPX recorder that writes points in real-time using GPX 1.1 format
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # GPX 1.1 specific initialization if needed

    def temp_init(self):
        if self.output_file:
            self._output_file = self.output_file
        else:
            self._output_file = f'Track {utc_ms_to_gpx_time(utc_ms_time()).replace(":", "")}.gpx'

        self.track_name     = self._output_file.replace('.gpx', '')
        self._temp_filename = f'{self.track_name}.gpx1_{self.units}'
        self.temp_file_path = os.path.join(self.work_path, self._temp_filename)

    def point_to_string(self, point):
        '''
            Convert point to XML string for temporary working (GPX 1.1 format)
        '''

        # Latitude and longitude in decimal degrees
        xml_parts = []
        if point.get('latitude') is not None and point.get('longitude') is not None:
            xml_parts.append(f'''<trkpt lat="{point.get('latitude'):.16f}" lon="{point.get('longitude'):.16f}">''')
        else:
            xml_parts.append(f'<trkpt lat=" " lon=" ">')

        # Altitude in meters
        if point.get('altitude_m') is not None:
            xml_parts.append(f"<ele>{point.get('altitude_m'):.16f}</ele>")
        else:
            xml_parts.append(f'<ele> </ele>')

        # UTC time in YYYY-MM-DDTHH:MM:SSZ
        if point.get('time_ms_utc') is not None:
            time_gpx = utc_ms_to_gpx_time(point.get('time_ms_utc'))
        else:
            time_gpx = utc_ms_to_gpx_time(utc_ms_time())
        xml_parts.append(f'<time>{time_gpx}</time>')

        # Number of sattelites used in fix
        if point.get('satellites_used_in_fix') is not None:
            xml_parts.append(f"<sat>{point.get('satellites_used_in_fix')}</sat>")
        else:
            xml_parts.append(f'<sat> </sat>')

        # GPX 1.1 uses extensions for custom fields like speed and accuracy
        extensions = []
        # Speed in m/s
        if point.get('speed_mps') is not None:
            extensions.append(f"<gpxtpx:speed>{point.get('speed_mps'):.16f}</gpxtpx:speed>")
        else:
            extensions.append(f'<gpxtpx:speed> </gpxtpx:speed>')

        # Accuracy in meters
        if point.get('accuracy_m') is not None:
            extensions.append(f"<gpxtpx:accuracy>{point.get('accuracy_m'):.16f}</gpxtpx:accuracy>")
        else:
            extensions.append(f'<gpxtpx:accuracy> </gpxtpx:accuracy>')

        if extensions:
            xml_parts.append('<extensions>')
            xml_parts.extend(extensions)
            xml_parts.append('</extensions>')

        xml_parts.append('</trkpt>')
        return ''.join(xml_parts)

    def create_gpx_header(self) -> str:
        '''
            Create GPX 1.1 file header with metadata and statistics
        '''
        # Create header with comments
        header =   '<?xml version="1.0" encoding="UTF-8"?>\n'
        header += f'<!-- Created with {self.creator} -->\n'
        header +=  '<!-- GPX Version = 1.1 -->\n'
        header += f'<!-- Units = {self.units} -->\n'
        header += f'<!-- Track = {self.points_count} TrackPoints -->\n'
        header +=  '<!-- Track Statistics: -->\n'
        header += f'<!-- Distance = {meters_to_gpx_distance(self.units, self.total_distance, 1000):.0f} {units_to_gpx_distance(self.units, self.total_distance, 1000)} -->\n'
        header += f'<!-- Duration = {self.duration_format} -->\n'
        header += f'<!-- Elevation Gain = {meters_to_gpx_distance(self.units, self.elevation_gain):.0f} {units_to_gpx_distance(self.units)} -->\n'
        header += f'<!-- Elevation Loss = {meters_to_gpx_distance(self.units, self.elevation_loss):.0f} {units_to_gpx_distance(self.units)} -->\n'
        header += f'<!-- Max Speed = {mps_to_gpx_speed(self.units, self.speed_max):.0f} {units_to_gpx_speed(self.units)} -->\n'
        header += f'<!-- Avg Speed = {mps_to_gpx_speed(self.units, self.speed_avg):.0f} {units_to_gpx_speed(self.units)} -->\n'

        if self.activity:
            header += f'<!--  Activity = {self.activity} -->\n'

        # GPX 1.1 root element with proper namespaces
        header +=  '<gpx version="1.1"\n'
        header += f'     creator="{self.creator}"\n'
        header +=  '     xmlns="http://www.topografix.com/GPX/1/1"\n'
        header +=  '     xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1"\n'
        header +=  '     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
        header +=  '     xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd\n'
        header +=  '                         http://www.garmin.com/xmlschemas/TrackPointExtension/v1 http://www.garmin.com/xmlschemas/TrackPointExtensionv1.xsd">\n'

        # Metadata section (GPX 1.1 structure)
        header += '<metadata>\n'

        if self.track_name:
            header += f'  <name>{self.track_name}</name>\n'

        header += f'<time>{utc_ms_to_gpx_time(self.start_time)}</time>\n'

        if self.activity:
            header += f'  <keywords>{self.activity}</keywords>\n'

        # Bounds (if we have points)
        if self.points_count > 0:
            header += f'  <bounds minlat="{self.min_lat:.16f}" minlon="{self.min_lon:.16f}" '
            header += f'maxlat="{self.max_lat:.16f}" maxlon="{self.max_lon:.16f}" />\n'

        header += '</metadata>\n'
        return header
