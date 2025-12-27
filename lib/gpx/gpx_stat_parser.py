import re
from lib.utils.units  import gpx_time_to_utc_ms


def parse_all_gpx_statistics(gpx_content):
    '''
        Parse all statistics from GPX comments including elevation changes and units.
    '''
    statistics = {}

    # Define patterns for each statistic
    patterns = \
    {
        'version': r'GPX Version = ([\d.]+)\s*(\w+)?',
        'units': r'Units = (\w+)',
        'track_points': r'Track = (\d+) TrackPoints',
        'distance': r'Distance = ([\d.]+)\s*(\w+)?',
        'duration': r'Duration = ([\d:]+)',
        'elevation_gain': r'Elevation Gain = ([\d.]+)\s*(\w+)?',
        'elevation_loss': r'Elevation Loss = ([\d.]+)\s*(\w+)?',
        'speed_max': r'Max Speed = ([\d.]+)\s*([\w/]+)?',
        'speed_avg': r'Avg Speed = ([\d.]+)\s*([\w/]+)?'
    }

    # Extract each statistic
    for key, pattern in patterns.items():
        match = re.search(pattern, gpx_content)
        if match:
            value = match.group(1)
            if key in ['distance', 'elevation_gain', 'elevation_loss', 'speed_max', 'speed_avg']:
                # Convert to float and store with unit
                statistics[key] = \
                {
                    'value': int(value),
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


def parse_gpx_trkseg(gpx_content, reconstruct = False):
    '''
        Parse GPX track segments and extract lat/lon only - works for both GPX 1.0 and 1.1
        using simple pattern.
    '''
    track_points = []

    # Simple pattern
    pattern = \
    (
        r'<trkpt[^>]+lat="([^"]+)"[^>]+lon="([^"]+)"[^>]*>'                                                  # lat, lon
        r'(?:.*?<ele>([^<]+)</ele>)?'                                                                        # alt
        r'(?:.*?<time>([^<]+)</time>)?'                                                                      # time
        r'(?:.*?<sat>([^<]+)</sat>)?'                                                                        # sat
        r'(?:.*?(?:<speed>([^<]+)</speed>|<gpxtpx:speed>([^<]+)</gpxtpx:speed>))?'                           # speed
        r'(?:.*?(?:<custom:accuracy>([^<]+)</custom:accuracy>|<gpxtpx:accuracy>([^<]+)</gpxtpx:accuracy>))?' # accuracy
        r'.*?</trkpt>'                                                                                       # allow anything until closing trkpt
    )

    matches         = re.findall(pattern, gpx_content)
    cleaned_matches = [tuple(x for x in t if x != '') for t in matches]

    for lat, lon, alt, time, sat, speed, accuracy in cleaned_matches:
        if reconstruct:
            track_points.append \
            (
                {
                    'latitude':                         float(lat)      if lat      is not None else None,
                    'longitude':                        float(lon)      if lon      is not None else None,
                    'altitude_m':                       float(alt)      if alt      is not None else None,
                    'time_ms_utc': int(gpx_time_to_utc_ms(str(time)))   if time     is not None else None,
                    'speed_mps':                        float(speed)    if speed    is not None else None,
                    'accuracy_m':                       float(accuracy) if accuracy is not None else None,
                    'satellites_used_in_fix':           int(sat)        if sat      is not None else None
                }
            )

        else:
            track_points.append \
            (
                {
                    'lat': float(lat) if lat is not None else None,
                    'lon': float(lon) if lon is not None else None
                }
            )
    return track_points
