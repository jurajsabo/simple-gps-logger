import os

from lib.gpx.csv_stat_parser import parse_csv_dict
from lib.gpx.gpxRecorder     import GPXRecorder

from lib.utils.units import \
(
    utc_ms_time,
    utc_ms_to_gpx_time,
    meters_to_gpx_distance,
    mps_to_gpx_speed,
    units_to_gpx_distance,
    units_to_gpx_speed
)


class CSVRecorder(GPXRecorder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Ensure output file has .csv extension
        if self.output_file:
            self.output_file = self.output_file.replace('.gpx', '.csv')

    def temp_init(self):
        if self.output_file:
            self._output_file = self.output_file
        else:
            self._output_file = f'Track {utc_ms_to_gpx_time(utc_ms_time()).replace(":", "")}.csv'

        self.track_name     = self._output_file.replace('.csv', '')
        self._temp_filename = f'{self.track_name}.csv_{self.units}'
        self.temp_file_path = os.path.join(self.work_path, self._temp_filename)

    def point_to_string(self, point):
        '''
            Convert point to CSV string for temporary working
        '''

        # Latitude and longitude in decimal degrees
        csv_parts = []
        if point.get('latitude') is not None and point.get('longitude') is not None:
            csv_parts.append(f"{point.get('latitude'):.16f}")
            csv_parts.append(f"{point.get('longitude'):.16f}")
        else:
            csv_parts.append(' ')
            csv_parts.append(' ')

        # Altitude in meters
        if point.get('altitude_m') is not None:
            csv_parts.append(f"{point.get('altitude_m'):.16f}")
        else:
            csv_parts.append(' ')

        # UTC time in YYYY-MM-DDTHH:MM:SSZ
        if point.get('time_ms_utc') is not None:
            time_gpx = utc_ms_to_gpx_time(point.get('time_ms_utc'))
        else:
            time_gpx = utc_ms_to_gpx_time(utc_ms_time())
        csv_parts.append(time_gpx)

        # Speed in m/s
        if point.get('speed_mps') is not None:
            csv_parts.append(f"{point.get('speed_mps'):.16f}")
        else:
            csv_parts.append(' ')

        # Number of sattelites used in fix
        if point.get('satellites_used_in_fix') is not None:
            csv_parts.append(str(point.get('satellites_used_in_fix')))
        else:
            csv_parts.append(' ')

        # Accuracy in meters
        if point.get('accuracy_m') is not None:
            csv_parts.append(f"{point.get('accuracy_m'):.16f}")
        else:
            csv_parts.append(' ')

        return ','.join(csv_parts)

    def generate_final_file(self, reconstruct = False):
        '''
            Generate the final CSV file with all recorded points
        '''
        # Reconstruct lines
        lines = self.reconstruct_file(parse_csv_dict, reconstruct)

        # Clean up temporary file
        os.remove(self.temp_file_path)
        print('[GPX]', f'Temporary file {self._temp_filename} deleted')

        # Create and write to final CSV file
        output_file_path = os.path.join(self.work_path, self._output_file)
        with open(output_file_path, 'x', encoding = 'utf-8', newline = '') as f:
            # Write header comments
            self._create_csv_header(f)

            # Write CSV column headers
            f.write('#\n')  # Empty comment line for separation
            f.write('lat,lon,ele,time,speed,sat,accuracy\n')

            # Read and add all points from temporary file
            for line in lines:
                line = line.strip()
                if line:
                    f.write(f'{line}\n')
        print('[GPX]', f'Final file {self._output_file} created')

    def _create_csv_header(self, file_handle):
        '''
            Create CSV file header with metadata and statistics
        '''
        file_handle.write(f'# Created with {self.creator}\n')
        file_handle.write(f'# Units = {self.units}\n')
        file_handle.write(f'# Track = {self.points_count} TrackPoints\n')
        file_handle.write('# Track Statistics:\n')
        file_handle.write(f'# Distance = {meters_to_gpx_distance(self.units, self.total_distance, 1000):.0f} {units_to_gpx_distance(self.units, self.total_distance, 1000)}\n')
        file_handle.write(f'# Duration = {self.duration_format}\n')
        file_handle.write(f'# Elevation Gain = {meters_to_gpx_distance(self.units, self.elevation_gain):.0f} {units_to_gpx_distance(self.units)}\n')
        file_handle.write(f'# Elevation Loss = {meters_to_gpx_distance(self.units, self.elevation_loss):.0f} {units_to_gpx_distance(self.units)}\n')
        file_handle.write(f'# Max Speed = {mps_to_gpx_speed(self.units, self.speed_max):.0f} {units_to_gpx_speed(self.units)}\n')
        file_handle.write(f'# Avg Speed = {mps_to_gpx_speed(self.units, self.speed_avg):.0f} {units_to_gpx_speed(self.units)}\n')

        if self.activity:
            file_handle.write(f'# Activity = {self.activity}\n')

        # Add bounds if available
        if self.points_count > 0:
            file_handle.write(f'# Bounds: {self.min_lat:.16f}, {self.min_lon:.16f} to {self.max_lat:.16f},{self.max_lon:.16f}\n')

        # Add track name and timing info
        file_handle.write(f'# Track Name = {self.track_name}\n')
        file_handle.write(f'# Start Time = {utc_ms_to_gpx_time(self.start_time)}\n')
