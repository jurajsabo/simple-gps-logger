import os

from math  import sin, cos, radians, atan2, sqrt

from lib.gpx.gpx_stat_parser import parse_gpx_trkseg

from config import app_name, urls
from lib.utils.paths    import working_path
from lib.utils.units    import \
(
    utc_ms_to_gpx_time,
    utc_ms_time,
    mps_to_gpx_speed,
    meters_to_gpx_distance,
    units_to_gpx_distance,
    units_to_gpx_speed
)


class GPXRecorder:
    '''
        Streaming GPX recorder that writes points in real-time
    '''
    def __init__ \
        (
            self,
            output_file: str = None,
            creator:     str = app_name,
            activity:    str = None,
            work_path:   str = working_path,
            units:       str = 'metric',
            link:        str = urls['web']
        ):
        self.__output_file = output_file

        self.creator   = creator
        self.activity  = activity
        self.work_path = work_path
        self.units     = units
        self.link      = link

        # Statistics tracking
        self.stats_reset()

        # File handles
        self.temp_points_file = None
        self.temp_file_path   = None
        self.temp_filename    = None

        # Recorder handles
        self.track_name   = None
        self.start_time   = None
        self.points_count = 0

        # Recording indicator
        self._is_recording = 0  # -1... pause, 0... stop, 1... record

    @property
    def output_file(self):
        return self.__output_file

    @output_file.setter
    def output_file(self, value):
        if value is not None:
            allowed_extensions = ['.csv', '.gpx']
            file_ext = os.path.splitext(value)[1].lower()

            if file_ext not in allowed_extensions:
                raise ValueError \
                (
                    f"[GPX] Invalid file extension '{file_ext}'."
                    f"Allowed extensions: {', '.join(sorted(allowed_extensions))}"
                )

        self.__output_file = value

    @property
    def is_recording(self):
        return self._is_recording

    @is_recording.setter
    def is_recording(self, value):
        if value not in [-1, 0, 1]:
            raise ValueError('[GPX] Recording indicator out of bounds.')
        self._is_recording = value

    def temp_init(self):
        # Use output file name or use default
        if self.output_file:
            self._output_file = self.output_file
        else:
            self._output_file = f'Track {utc_ms_to_gpx_time(self.start_time).replace(":", "")}.gpx'

        self.track_name     = self._output_file.replace('.gpx', '')
        self.temp_filename  = f'{self.track_name}.gpx_{self.units}'
        self.temp_file_path = os.path.join(self.work_path, self.temp_filename)

    def start_recording(self):
        '''
            Start recording GPS points
        '''
        if self.is_recording == 0:
            self.is_recording = 1
            self.start_time   = utc_ms_time()
            self.points_count = 0

            # Create temporary file for storing points in working directory
            self.temp_init()
            self.temp_points_file = open(self.temp_file_path, 'w')

            print('[GPX]', f'Started recording to {self._output_file}')
            print('[GPX]', f'Track:               {self.track_name}')

    def resume_recording(self):
        '''
            Resume recording GPS points
        '''
        if self.is_recording == -1:
            if not self.temp_file_path:
                raise RuntimeError('[GPX] No active temporary file')

            self.is_recording = 1
            self.temp_points_file = open(self.temp_file_path, 'a')

            print('[GPX]', f'Resumed recording to {self._output_file}')
            print('[GPX]', f'Track:               {self.track_name}')

    def pause_recording(self):
        '''
            Pause recording
        '''
        if self.is_recording == 1:
            self.is_recording = -1

            # Close temporary file
            self.temp_points_file.close()

            print('[GPX]', f'Recording paused. Duration: {self.total_duration:.0f} s')
            print('[GPX]', f'Total points: {self.points_count}')
            print('[GPX]', f'Distance: {self.total_distance:.0f} m')

    def stop_recording(self):
        '''
            Stop recording and generate final GPX file
        '''
        if self.is_recording != 0:
            self.is_recording = 0

            # Close temporary file
            self.temp_points_file.close()

            # Generate final file
            self.generate_final_file()

            print('[GPX]', f'Recording stopped. Duration: {self.total_duration:.0f} s')
            print('[GPX]', f'Total points: {self.points_count}')
            print('[GPX]', f'Distance: {self.total_distance:.0f} m')
            print('[GPX]', f'Final GPX saved to: {self._output_file}')

            # Stats reset
            self.stats_reset()

        return True

    def add_point(self, point):
        '''
            Add a GPS point to the recording
        '''
        # Update statistics
        self.update_statistics(point)

        # Write point to temporary file
        point_xml = self.point_to_string(point)
        self.temp_points_file.write(f'{point_xml} \n')
        self.temp_points_file.flush()

    def update_statistics(self, point):
        '''
            Update recording statistics with new point
        '''
        # Update bounds
        self.min_lat = min(self.min_lat, point.get('latitude'))
        self.max_lat = max(self.max_lat, point.get('latitude'))
        self.min_lon = min(self.min_lon, point.get('longitude'))
        self.max_lon = max(self.max_lon, point.get('longitude'))

        # Update total distance in meters
        if self.last_point:
            distance = self.haversine_distance(self.last_point.get('latitude'), self.last_point.get('longitude'),
                                               point.get('latitude'), point.get('longitude'))
            self.total_distance += distance

        # Update speed (track for average calculation) in mps
        if point.get('speed_mps') is not None:
            if point.get('speed_mps') > self.speed_max:
                self.speed_max = point.get('speed_mps')
            self.speed_sum += point.get('speed_mps')
            self.speed_count += 1

            # Update average speed in mps
            self.speed_avg = self.speed_sum / self.speed_count if self.speed_count > 0 else 0

        # Update elevation in m
        if point.get('altitude_m') is not None:
            if self.last_elevation is not None:
                ele_diff = point.get('altitude_m') - self.last_elevation
                if ele_diff > 0:
                    self.elevation_gain += ele_diff
                else:
                    self.elevation_loss += abs(ele_diff)
            self.last_elevation = point.get('altitude_m')

        # Calculate total duration in seconds
        if point.get('time_ms_utc') is not None:
            if self.last_point:
                t1 = point.get('time_ms_utc')
                t0 = self.last_point.get('time_ms_utc')
                duration = (t1 - t0) / 1000 # Convert milliseconds to seconds
                self.total_duration += duration

        hours   = int(self.total_duration // 3600)
        minutes = int((self.total_duration % 3600) // 60)
        seconds = int(self.total_duration % 60)

        # Format duration
        self.duration_format = f'{hours:02d}:{minutes:02d}:{seconds:02d}'

        # Points
        self.points_count += 1
        self.last_point = point.copy()

        if self.points_count % 100 == 0:
            print('[GPX]', f'Recorded {self.points_count} points...')

    def haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        '''
            Calculate distance between two points in meters using Haversine formula
        '''
        lat1_rad  = radians(lat1)
        lat2_rad  = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)

        R = 6371000  # Earth's radius in meters
        a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c

    def point_to_string(self, point):
        '''
            Convert point to XML string for temporary working
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

        # Speed in m/s
        if point.get('speed_mps') is not None:
            xml_parts.append(f"<speed>{point.get('speed_mps'):.16f}</speed>")
        else:
            xml_parts.append(f'<speed> </speed>')

        # GPX 1.0 uses extensions for custom fields like accuracy
        extensions = []
        # Accuracy in meters
        if point.get('accuracy_m') is not None:
            extensions.append(f"<custom:accuracy>{point.get('accuracy_m'):.16f}</custom:accuracy>")
        else:
            extensions.append(f'<custom:accuracy> </custom:accuracy>')

        if extensions:
            xml_parts.append('<extensions>')
            xml_parts.extend(extensions)
            xml_parts.append('</extensions>')

        xml_parts.append('</trkpt>')
        return ''.join(xml_parts)

    def reconstruct_file(self, func, reconstruct = False):
        if reconstruct:
            self.temp_init()

            # Open temporary file
            with open(self.temp_file_path, 'r', encoding = 'utf-8') as f:
                points = f.read()
                f.seek(0)
                lines = f.readlines()

            start_time = []
            for point in func(points, reconstruct):
                self.update_statistics(point)
                start_time.append(point.get('time_ms_utc'))

            self.start_time = min(start_time)

        else:
            # Open temporary file
            with open(self.temp_file_path, 'r', encoding = 'utf-8') as f:
                lines = f.readlines()

        return lines

    def generate_final_file(self, reconstruct = False):
        '''
            Generate the final GPX file with all recorded points
        '''
        # Reconstruct lines
        lines = self.reconstruct_file(parse_gpx_trkseg, reconstruct)

        # Clean up temporary file
        os.remove(self.temp_file_path)
        print('[GPX]', f'Temporary file {self.temp_filename} deleted')

        # Create GPX content
        gpx_content = self.create_gpx_header()

        # Add track start
        gpx_content += f'<trk>\n <name>{self.track_name}</name>\n <trkseg>\n'

        # Read and add all points from temporary file
        for line in lines:
            line = line.strip()
            if line:
                gpx_content += f'  {line}\n'

        # Close track
        gpx_content += ' </trkseg>\n</trk>\n'
        gpx_content += '</gpx>'

        # Write final file
        output_file_path = f'{os.path.join(self.work_path, self._output_file)}'
        with open(output_file_path, 'x', encoding = 'utf-8') as f:
            f.write(gpx_content)

        print('[GPX]', f'Final file {self._output_file} created')

    def create_gpx_header(self) -> str:
        '''
            Create GPX file header with metadata and statistics
        '''
        # Create header with comments
        header =   '<?xml version="1.0" encoding="UTF-8"?>\n'
        header += f'<!-- Created with {self.creator} -->\n'
        header +=  '<!-- GPX Version = 1.0 -->\n'
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

        # GPX root element
        header +=  '<gpx version="1.0"\n'
        header += f'     creator="{self.creator}"\n'
        header +=  '     xmlns="http://www.topografix.com/GPX/1/0"\n'
        header += f'     xmlns:custom="{self.link}"\n'
        header +=  '     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
        header +=  '     xsi:schemaLocation="http://www.topografix.com/GPX/1/0 http://www.topografix.com/GPX/1/0/gpx.xsd">\n'

        # Metadata
        if self.track_name:
            header += f'<name>{self.track_name}</name>\n'

        header += f'<time>{utc_ms_to_gpx_time(self.start_time)}</time>\n'

        if self.activity:
            header += f'<keywords>{self.activity}</keywords>\n'

        # Bounds
        if self.points_count > 0:
            header += f'<bounds minlat="{self.min_lat:.16f}" minlon="{self.min_lon:.16f}" '
            header += f'maxlat="{self.max_lat:.16f}" maxlon="{self.max_lon:.16f}" />\n'
        return header

    def stats_reset(self):
        self.total_distance  = 0
        self.speed_max       = 0
        self.speed_avg       = 0
        self.speed_sum       = 0
        self.speed_count     = 0
        self.elevation_gain  = 0
        self.elevation_loss  = 0
        self.total_duration  = 0
        self.duration_format = 0

        self.min_lat = float('inf')
        self.max_lat = float('-inf')
        self.min_lon = float('inf')
        self.max_lon = float('-inf')

        self.last_point     = None
        self.last_elevation = None
