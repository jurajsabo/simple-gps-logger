import re
import io
import csv

from lib.utils.units import gpx_time_to_utc_ms


def parse_all_csv_statistics(csv_content):
    '''
        Parse all statistics from CSV header comments including elevation changes and units.
    '''
    statistics = {}

    # Define patterns for each statistic (adapted for CSV comment format)
    patterns = \
    {
        'units': r'# Units = (\w+)',
        'track_points': r'# Track = (\d+) TrackPoints',
        'distance': r'# Distance = ([\d.]+)\s*(\w+)?',
        'duration': r'# Duration = ([\d:]+)',
        'elevation_gain': r'# Elevation Gain = ([\d.]+)\s*(\w+)?',
        'elevation_loss': r'# Elevation Loss = ([\d.]+)\s*(\w+)?',
        'speed_max': r'# Max Speed = ([\d.]+)\s*([\w/]+)?',
        'speed_avg': r'# Avg Speed = ([\d.]+)\s*([\w/]+)?',
    }

    # Extract each statistic
    for key, pattern in patterns.items():
        match = re.search(pattern, csv_content)
        if match:
            value = match.group(1)

            if key in ['distance', 'elevation_gain', 'elevation_loss', 'speed_max', 'speed_avg']:
                # Convert to float and store with unit
                statistics[key] = \
                {
                    'value': float(value),
                    'unit': match.group(2) if len(match.groups()) > 1 and match.group(2) else None
                }

            elif key == 'track_points':
                statistics[key] = \
                {
                    'value': int(value),
                    'unit': 'points'
                }

            else:
                statistics[key] = \
                {
                    'value': value
                }

    # Calculate net elevation change
    if 'elevation_gain' in statistics and 'elevation_loss' in statistics:
        net_change = statistics['elevation_gain']['value'] - statistics['elevation_loss']['value']
        statistics['net_elevation_change'] = \
        {
            'value': net_change,
            'unit': statistics['elevation_gain']['unit']
        }

    return statistics


def parse_csv_dict(csv_content, reconstruct = False):
    '''
        Parse CSV track segments and extract lat/lon (or full GPXPoint if requested).
    '''
    # Split into lines and strip
    lines = [line.strip() for line in csv_content.splitlines() if line.strip()]

    # Case 1: If first non-comment line starts with "#"
    if lines[0].startswith('#'):
        # Drop comments
        lines = [line for line in lines if not line.startswith('#')]
        # Build CSV reader with header
        reader = csv.DictReader(io.StringIO('\n'.join(lines)), skipinitialspace = True)

    # Case 2: No header → add one manually
    else:
        header = 'lat,lon,ele,time,speed,sat,accuracy'
        reader = csv.DictReader(io.StringIO(header + '\n' + '\n'.join(lines)), skipinitialspace = True)

    points = []
    for c in reader:
        if reconstruct:
            points.append \
            (
                {
                    'latitude':                            float(c['lat']) if c['lat']      is not None else None,
                    'longitude':                           float(c['lon']) if c['lon']      is not None else None,
                    'altitude_m':                          float(c['ele']) if c['ele']      is not None else None,
                    'time_ms_utc': int(gpx_time_to_utc_ms(str(c['time']))) if c['time']     is not None else None,
                    'speed_mps':                         float(c['speed']) if c['speed']    is not None else None,
                    'accuracy_m':                     float(c['accuracy']) if c['accuracy'] is not None else None,
                    'satellites_used_in_fix':                int(c['sat']) if c['sat']      is not None else None
                }
            )
        else:
            points.append \
            (
                {
                    'lat': float(c['lat']),
                    'lon': float(c['lon'])
                }
            )
    return points
